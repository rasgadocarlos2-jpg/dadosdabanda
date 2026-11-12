import csv
import io
import re
import time
from pathlib import Path

from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from ..supa import Supa, get_supa
from . import ficha
from .auth import Limitador, chave_opcional, criar_chave

app = FastAPI(
    title="Dados da Banda API",
    version="0.1.0",
    description="Dados abertos sobre Angola. Cada valor traz a fonte, a data de recolha e o endereço de consulta.",
)
app.state.limitador = Limitador()

# CORS — API pública para leitura
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
    max_age=86400,
)

# Limites duráveis de criação de chaves: contados na BD, não em memória.
LIMITE_CHAVES_EMAIL_HORA = 3
LIMITE_CHAVES_GLOBAL_HORA = 100


def _verifica_limite_chaves(supa: Supa, email: str) -> None:
    desde = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 3600))
    recentes = supa.select("chaves_api", columns="email", limit=LIMITE_CHAVES_GLOBAL_HORA + 1,
                           filters={"criada_em": f"gte.{desde}"})
    if len(recentes) >= LIMITE_CHAVES_GLOBAL_HORA:
        raise HTTPException(429, "Muitas chaves criadas na última hora. Tenta mais tarde.",
                            headers={"Retry-After": "3600"})
    if sum(1 for r in recentes if r.get("email") == email) >= LIMITE_CHAVES_EMAIL_HORA:
        raise HTTPException(429, "Este e-mail já criou várias chaves na última hora. Tenta mais tarde.",
                            headers={"Retry-After": "3600"})


# Handler global — IDs malformados → 400 (não 500)
@app.exception_handler(Exception)
async def _global_handler(request: Request, exc: Exception):
    # HTTPException passa pela rota padrão
    if isinstance(exc, HTTPException):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=getattr(exc, "headers", None))
    # Tudo o resto: devolvemos 500 genérico sem leak de stack trace
    msg = str(exc)[:200]
    return JSONResponse({"detail": f"Erro interno. Tenta de novo ou reporta em /contacto.html. (ref: {msg})"}, status_code=500)

WEB_DIR = Path(__file__).resolve().parents[2] / "web"
PUBLIC_DIR = Path(__file__).resolve().parents[2] / "public"

AVISO_COMPARACAO = ("As diferenças entre fontes podem refletir metodologias, revisões ou datas de "
                    "publicação diferentes. Não indicam qual das fontes está certa.")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SERIE_ID_RE = re.compile(r"^[a-z0-9_]{2,80}$")


def _valida_id(serie_id: str) -> str:
    if not SERIE_ID_RE.match(serie_id):
        raise HTTPException(400, "ID de série inválido. Usa apenas letras minúsculas, dígitos e _.")
    return serie_id

import os
CRON_SECRET = os.environ.get("CRON_SECRET", "")


@app.get("/cron/atualizar", include_in_schema=False)
def cron_atualizar(request: Request, supa: Supa = Depends(get_supa)):
    """Chamado pelo Vercel Cron semanalmente. Atualiza fontes rápidas (Frankfurter)."""
    import httpx
    from datetime import datetime, timezone

    # Auth: Vercel Cron inclui o header Authorization: Bearer <CRON_SECRET>
    # Falha fechada: sem CRON_SECRET configurado, o endpoint não corre.
    import hmac
    if not CRON_SECRET:
        raise HTTPException(503, "CRON_SECRET não configurado")
    auth = request.headers.get("authorization", "")
    if not hmac.compare_digest(auth.encode(), f"Bearer {CRON_SECRET}".encode()):
        raise HTTPException(401, "Unauthorized")

    agora = datetime.now(timezone.utc).isoformat()
    log = {"started": agora, "jobs": []}

    def push(sid: str, rows: list):
        if not rows: return
        supa.client.post(
            f"{supa.url}/rest/v1/observacoes?on_conflict=serie_id,periodo,recolhido_em",
            headers={**supa.headers, "Prefer": "return=minimal,resolution=ignore-duplicates"},
            json=rows)
        log["jobs"].append({"serie": sid, "linhas": len(rows), "estado": "ok"})

    # --- Frankfurter BNA (4 séries de câmbio) ---
    try:
        r = httpx.get("https://api.frankfurter.dev/v2/rates",
            params={"base": "aoa", "providers": "bna", "from": "2004-01-01", "group": "month"},
            timeout=15, headers={"User-Agent": "DadosDaBanda/0.5"})
        r.raise_for_status()
        resp = r.json()
        for codigo, sid in [("USD", "bna_cambio_usd"), ("EUR", "bna_cambio_eur"),
                            ("CNY", "bna_cambio_cny"), ("ZAR", "bna_cambio_zar")]:
            rows = []
            for rec in resp:
                if rec.get("quote") != codigo or not rec.get("rate"):
                    continue
                periodo = str(rec["date"])[:7]
                rows.append({"serie_id": sid, "periodo": periodo,
                             "valor": round(1.0 / float(rec["rate"]), 6),
                             "recolhido_em": agora, "hash_bruto": None})
            push(sid, rows)
    except Exception as e:
        log["jobs"].append({"fonte": "frankfurter", "estado": "erro", "mensagem": str(e)[:200]})

    # --- World Bank (indicadores anuais, 4 séries) ---
    WB = {
        "wb_inflacao":        "FP.CPI.TOTL.ZG",
        "wb_pib_crescimento": "NY.GDP.MKTP.KD.ZG",
        "wb_pib_usd":         "NY.GDP.MKTP.CD",
        "wb_populacao":       "SP.POP.TOTL",
        "wb_pib_kz":          "NY.GDP.MKTP.CN",
    }
    for sid, codigo in WB.items():
        escala = 1e9 if sid == "wb_pib_kz" else 1
        try:
            r = httpx.get(
                f"https://api.worldbank.org/v2/country/AGO/indicator/{codigo}",
                params={"format": "json", "per_page": 200, "date": "2000:2030"},
                timeout=15, headers={"User-Agent": "DadosDaBanda/0.5"})
            r.raise_for_status()
            body = r.json()
            if not isinstance(body, list) or len(body) < 2: continue
            rows = []
            for rec in body[1]:
                if rec.get("value") is None: continue
                rows.append({"serie_id": sid, "periodo": str(rec["date"]),
                             "valor": round(float(rec["value"]) / escala, 6), "recolhido_em": agora, "hash_bruto": None})
            push(sid, rows)
        except Exception as e:
            log["jobs"].append({"fonte": sid, "estado": "erro", "mensagem": str(e)[:200]})

    log["terminou"] = datetime.now(timezone.utc).isoformat()
    return log


def _ler_serie(supa: Supa, serie_id: str) -> dict:
    s = supa.first("series", columns="*,fonte:fontes(nome)",
                   filters={"id": f"eq.{serie_id}"})
    if s is None:
        raise HTTPException(404, f"Série '{serie_id}' não encontrada.")
    return s


def _meta(s: dict) -> dict:
    return {"id": s["id"], "nome": s["nome"], "unidade": s["unidade"],
            "periodicidade": s["periodicidade"],
            "fonte": (s.get("fonte") or {}).get("nome", s.get("fonte_id", "")),
            "fonte_id": s["fonte_id"], "url_consulta": s.get("url_consulta")}


def _valores_atuais(supa: Supa, serie_id: str, de: str | None = None, ate: str | None = None) -> list[dict]:
    """Última versão recolhida de cada período, por ordem cronológica."""
    linhas = supa.select(
        "observacoes",
        columns="periodo,valor,recolhido_em,id",
        order="recolhido_em.desc,id.desc",
        filters={"serie_id": f"eq.{serie_id}"},
    )
    atuais: dict[str, dict] = {}
    for o in linhas:
        atuais.setdefault(o["periodo"], o)
    return [atuais[p] for p in sorted(atuais)
            if (de is None or p >= de) and (ate is None or p <= ate)]


@app.get("/saude")
def saude():
    return {"estado": "ok"}


@app.post("/v1/chaves", status_code=201)
def gerar_chave(payload: dict = Body(...), supa: Supa = Depends(get_supa)):
    email = (payload.get("email") or "").strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 200:
        raise HTTPException(400, "E-mail inválido.")
    _verifica_limite_chaves(supa, email)
    chave = criar_chave(supa, email)
    return {"chave": chave, "email": email, "limite_por_minuto": 60,
            "aviso": "Guarda esta chave agora. Não a voltamos a mostrar."}


@app.get("/v1/fontes")
def listar_fontes(supa: Supa = Depends(get_supa)):
    return supa.select("fontes", columns="id,nome,url,estado_autorizacao,licenca", order="id.asc")


@app.get("/v1/series", dependencies=[Depends(chave_opcional)])
def listar_series(fonte: str | None = None, q: str | None = None, supa: Supa = Depends(get_supa)):
    filters = {}
    if fonte:
        filters["fonte_id"] = f"eq.{fonte}"
    series = supa.select("series", columns="*,fonte:fontes(nome)", order="id.asc", filters=filters)
    if q:
        series = [s for s in series if q.lower() in s["nome"].lower()]
    return [_meta(s) for s in series]


@app.get("/v1/series/{serie_id}", dependencies=[Depends(chave_opcional)])
def ver_serie(serie_id: str, supa: Supa = Depends(get_supa)):
    return _meta(_ler_serie(supa, _valida_id(serie_id)))


@app.get("/v1/series/{serie_id}/observacoes", dependencies=[Depends(chave_opcional)])
def observacoes(serie_id: str, de: str | None = None, ate: str | None = None,
                formato: str = Query("json", pattern="^(json|csv)$"),
                supa: Supa = Depends(get_supa)):
    serie_id = _valida_id(serie_id)
    s = _ler_serie(supa, serie_id)
    obs = _valores_atuais(supa, serie_id, de, ate)
    meta = _meta(s)
    if formato == "csv":
        saida = io.StringIO()
        w = csv.writer(saida)
        w.writerow(["periodo", "valor", "unidade", "fonte", "recolhido_em", "url_consulta"])
        for o in obs:
            w.writerow([o["periodo"], o["valor"], meta["unidade"], meta["fonte"], o["recolhido_em"], meta["url_consulta"] or ""])
        return Response(saida.getvalue(), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{serie_id}.csv"'})
    return {**meta, "observacoes": [{"periodo": o["periodo"], "valor": o["valor"],
                                     "recolhido_em": o["recolhido_em"]} for o in obs]}


def _todas_linhas(supa: Supa, filtro: str) -> list[dict]:
    linhas, deslocamento = [], 0
    while True:
        pagina = supa.select("observacoes", columns="serie_id,periodo,valor,recolhido_em",
                             order="recolhido_em.desc,id.desc", limit=1000,
                             filters={"serie_id": filtro, "offset": str(deslocamento)})
        linhas += pagina
        if len(pagina) < 1000:
            return linhas
        deslocamento += 1000


@app.get("/serie/{serie_id}", include_in_schema=False)
def ficha_serie(serie_id: str, supa: Supa = Depends(get_supa)):
    if not SERIE_ID_RE.match(serie_id):
        return RedirectResponse("/series.html", status_code=302)
    s = supa.first("series", columns="*,fonte:fontes(nome)", filters={"id": f"eq.{serie_id}"})
    if s is None:
        return RedirectResponse("/series.html", status_code=302)
    linhas = _todas_linhas(supa, f"eq.{serie_id}")
    atuais: dict[str, dict] = {}
    revisoes = []
    for o in linhas:
        recente = atuais.setdefault(o["periodo"], o)
        if abs(recente["valor"] - o["valor"]) > 0.005 and not recente.get("_revisto"):
            recente["_revisto"] = True
            revisoes.append({"periodo": o["periodo"], "antes": o["valor"], "depois": recente["valor"], "data": recente["recolhido_em"]})
    obs = [atuais[p] for p in sorted(atuais)]
    html = ficha.pagina({**s, "fonte": _meta(s)["fonte"]}, obs, sorted(revisoes, key=lambda r: r["periodo"], reverse=True))
    return HTMLResponse(html, headers={"Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400"})


@app.get("/v1/lote", dependencies=[Depends(chave_opcional)])
def lote(series: list[str] = Query(..., min_length=1, max_length=60), de: str | None = None,
         supa: Supa = Depends(get_supa)):
    """Várias séries num só pedido, para páginas que mostram muitos indicadores."""
    ids = [_valida_id(s) for s in dict.fromkeys(series)]
    atuais: dict[str, dict[str, dict]] = {i: {} for i in ids}
    for o in _todas_linhas(supa, f"in.({','.join(ids)})"):
        atuais[o["serie_id"]].setdefault(o["periodo"], o)
    corpo = {i: {"observacoes": [{"periodo": p, "valor": v[p]["valor"], "recolhido_em": v[p]["recolhido_em"]}
                                 for p in sorted(v) if de is None or p >= de]}
             for i, v in atuais.items()}
    return JSONResponse(corpo, headers={"Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400"})


@app.get("/v1/comparar", dependencies=[Depends(chave_opcional)])
def comparar(series: list[str] = Query(..., min_length=2, max_length=4), de: str | None = None,
             ate: str | None = None, supa: Supa = Depends(get_supa)):
    series = [_valida_id(s) for s in series]
    metas, por_serie = [], {}
    for sid in series:
        s = _ler_serie(supa, sid)
        metas.append(_meta(s))
        por_serie[sid] = {o["periodo"]: o["valor"] for o in _valores_atuais(supa, sid, de, ate)}
    periodos = sorted(set().union(*[set(v) for v in por_serie.values()]))
    linhas = []
    for p in periodos:
        valores = {sid: por_serie[sid].get(p) for sid in series}
        linha = {"periodo": p, "valores": valores}
        if len(series) == 2 and all(v is not None for v in valores.values()):
            linha["diferenca"] = round(valores[series[1]] - valores[series[0]], 6)
        linhas.append(linha)
    return {"series": metas, "linhas": linhas, "aviso": AVISO_COMPARACAO}


# Páginas estáticas (só em desenvolvimento local — na Vercel o CDN serve diretamente de /public).
_STATIC = PUBLIC_DIR if PUBLIC_DIR.exists() else WEB_DIR
if _STATIC.exists() and (_STATIC / "static").exists():
    app.mount("/static", StaticFiles(directory=_STATIC / "static"), name="static")

    PAGES = {"", "index", "painel", "api", "metodologia", "contacto", "privacidade",
             "legislacao", "orcamento", "economico", "diploma", "sobre", "faq",
             "comparar", "series", "regional", "pdfs", "estatuto", "correcoes", "404"}

    @app.get("/", include_in_schema=False)
    def _home():
        return FileResponse(_STATIC / "index.html")

    @app.get("/{page}.html", include_in_schema=False)
    def _page(page: str):
        f = _STATIC / f"{page}.html"
        if page in PAGES and f.exists():
            return FileResponse(f)
        return FileResponse(_STATIC / "404.html", status_code=404)
