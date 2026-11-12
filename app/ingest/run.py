"""Corre a recolha do Banco Mundial e do FMI.

  python -m app.ingest.run --contact o-teu-email@exemplo.com

Para cada série: confirma que a fonte está "autorizada", descarrega, guarda o original
em bruto/ (com data e hash), grava as observações e regista a execução.
"""
import argparse
import hashlib
import time
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from ..db import SessionLocal, engine, Base
from ..models import ExecucaoRecolha, Serie, agora
from . import clients
from .sources import FRANKFURTER_URL, IMF_URL, OWID_URL, SERIES, WB_URL
from .store import garantir_fontes_e_series, gravar_observacoes


def guardar_bruto(pasta: Path, serie_id: str, texto: str) -> str:
    h = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / f"{serie_id}_{ts}_{h[:8]}.json").write_text(texto, encoding="utf-8")
    return h


def executar(session: Session, client, bruto_dir: Path, delay: float = 1.5, de: int = 2004,
             fetch_fn=clients.fetch) -> list[ExecucaoRecolha]:
    garantir_fontes_e_series(session)
    resultados = []
    for s in SERIES:
        serie = session.get(Serie, s["id"])
        ex = ExecucaoRecolha(conector=s["id"], iniciada_em=agora())
        session.add(ex)
        if serie.fonte.estado_autorizacao != "autorizada":
            ex.estado = "ignorada"
            ex.mensagem = f"fonte '{serie.fonte_id}' está '{serie.fonte.estado_autorizacao}': não recolhida"
            ex.terminada_em = agora()
            session.commit()
            print(f"IGNORADA {s['id']}: {ex.mensagem}")
            resultados.append(ex)
            continue
        try:
            if s["tipo"] == "wb":
                url = WB_URL.format(codigo=s["codigo"])
                params = {"format": "json", "per_page": 200, "date": f"{de}:{date.today().year}"}
                texto, final = fetch_fn(client, url, params, delay)
                obs = clients.parse_wb(texto)
            elif s["tipo"] == "frankfurter":
                params = {"base": "aoa", "providers": "bna", "from": f"{de}-01-01", "group": "month"}
                texto, final = fetch_fn(client, FRANKFURTER_URL, params, delay)
                obs = clients.parse_frankfurter(texto, s["codigo"])
            elif s["tipo"] == "owid":
                url = OWID_URL.format(codigo=s["codigo"])
                texto, final = fetch_fn(client, url, None, delay)
                obs = clients.parse_owid(texto, s["codigo"])
            else:
                url = IMF_URL.format(codigo=s["codigo"])
                texto, final = fetch_fn(client, url, None, delay)
                obs = clients.parse_imf(texto, s["codigo"])
            h = guardar_bruto(bruto_dir, s["id"], texto)
            serie.url_consulta = final
            ex.novas, ex.revistas = gravar_observacoes(session, s["id"], obs, h)
            ex.estado = "ok"
            print(f"OK       {s['id']}: {len(obs)} períodos, {ex.novas} novos, {ex.revistas} revistos")
        except Exception as e:  # uma série a falhar não pára as outras
            ex.estado = "erro"
            ex.mensagem = f"{type(e).__name__}: {str(e)[:300]}"
            print(f"ERRO     {s['id']}: {ex.mensagem}")
        ex.terminada_em = agora()
        session.commit()
        resultados.append(ex)
    return resultados


def main():
    import os
    ap = argparse.ArgumentParser(description="Recolha do Banco Mundial e do FMI")
    ap.add_argument("--contact", required=True, help="O teu e-mail, incluído no User-Agent")
    ap.add_argument("--bruto", default=os.environ.get("BRUTO_DIR", "bruto"),
                    help="Pasta dos originais descarregados (ou env BRUTO_DIR)")
    ap.add_argument("--delay", type=float, default=1.5)
    args = ap.parse_args()
    Base.metadata.create_all(engine)
    ua = f"DadosDaBandaConector/0.2 (dados abertos, contacto: {args.contact})"
    with httpx.Client(headers={"User-Agent": ua}, follow_redirects=True, timeout=httpx.Timeout(30.0)) as client:
        with SessionLocal() as session:
            executar(session, client, Path(args.bruto), args.delay)


if __name__ == "__main__":
    main()
