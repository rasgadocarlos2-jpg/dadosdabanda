"""Ficha pública de cada série, gerada no servidor para funcionar sem JavaScript."""
import json
from datetime import date
from html import escape

BASE = "https://dadosdabanda.vercel.app"
MESES = ("Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro")
NAV = (("/painel.html", "Painel"), ("/orcamento.html", "Orçamento"), ("/regional.html", "Províncias"), ("/comparar.html", "Comparar"),
       ("/pdfs.html", "Documentos"), ("/api.html", "API"), ("/metodologia.html", "Metodologia"))
RODAPE = (("/sobre.html", "Sobre"), ("/metodologia.html", "Metodologia"), ("/estatuto.html", "Estatuto"), ("/correcoes.html", "Correcções"),
          ("/faq.html", "FAQ"), ("/privacidade.html", "Privacidade"), ("/contacto.html", "Contacto"), ("/economico.html", "Modo económico"))
CSS = """
body{margin:0;font-family:'IBM Plex Sans',system-ui,sans-serif;color:#14274E;background:#F3F5F7;line-height:1.5}
a{color:#14274E;text-decoration:none}a:hover{color:#B80F2D}
main{max-width:980px;margin:0 auto;padding:40px 24px;display:flex;flex-direction:column;gap:20px;box-sizing:border-box;width:100%}
h1{font-size:34px;line-height:1.15;margin:0}h2{font-size:21px;margin:0 0 10px}
.cx{background:#fff;border:1px solid #E3E6EA;border-radius:12px;padding:22px 24px;min-width:0}
.val{font:500 38px 'IBM Plex Mono',monospace;line-height:1.1}.mut{color:#4B5563;font-size:14px}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #E3E6EA}td.n{font-family:'IBM Plex Mono',monospace;text-align:right}th.n{text-align:right}
.btn{display:inline-flex;align-items:center;font:600 15px 'IBM Plex Sans',sans-serif;border:1px solid #14274E;background:#fff;color:#14274E;padding:10px 16px;border-radius:8px;min-height:44px;box-sizing:border-box;cursor:pointer}
.acoes{display:flex;gap:8px;flex-wrap:wrap}.tag{font:600 12px 'IBM Plex Sans',sans-serif;background:#FDF0D2;color:#7A4B00;padding:2px 8px;border-radius:999px}
summary{cursor:pointer;font-weight:600;min-height:32px}
"""


def explicar(s: dict) -> str:
    i = s["id"]
    if i == "ine_ipcn_variacao_mensal":
        return "Quanto os preços subiram ou desceram face ao mês anterior, a nível nacional. Um valor de 1% significa que o cabaz de referência ficou 1% mais caro num mês."
    if i == "ine_ipcn_indice":
        return "Índice de preços no consumidor. Compara o nível de preços com a base de Dezembro de 2020, que vale 100."
    if i.startswith("ine_ipcn_"):
        return "Variação mensal dos preços nesta província, publicada pelo INE."
    if i.startswith("bna_cambio_"):
        return "Quantos kwanzas custa uma unidade da moeda estrangeira, na média mensal da taxa de referência do BNA. Um número maior significa um kwanza mais fraco."
    if i == "bna_taxa_diretora":
        return "Taxa de juro de referência definida pelo BNA. Influencia o custo do crédito e serve para controlar a inflação."
    if "inflacao" in i:
        return "Variação média anual dos preços no consumidor."
    if "pib_crescimento" in i:
        return "Quanto a economia cresceu num ano, descontando a subida de preços."
    if "pib" in i:
        return "Valor total da produção do país num ano, a preços correntes, ou seja, sem descontar a inflação."
    if "divida" in i and i.startswith("imf_"):
        return "Dívida pública bruta em percentagem do PIB. Mede o total em dívida, não o que se paga num ano."
    if i.startswith("cge_liq_"):
        return "Despesa liquidada: a obrigação de pagamento já foi reconhecida pelo Estado, mesmo que ainda não tenha sido paga."
    if i.startswith("cge_pago_") or i == "oge_executado_total":
        return "Despesa efectivamente paga até 31 de Dezembro, segundo a Conta Geral do Estado."
    if i.startswith("cge_orc_"):
        return "Dotação inicial aprovada no OGE. Pode ser alterada durante o ano."
    if i.startswith("oge_fonte_"):
        return "Fonte de recurso prevista no OGE. Financiamento significa dinheiro emprestado, dentro ou fora do país."
    if i in ("oge_encargos_financeiros", "oge_divida_interna", "oge_divida_externa", "oge_divida_servico"):
        return "Pagamentos de juros e amortizações previstos no OGE. Mede o que há a pagar no ano, não o total da dívida."
    if i.startswith("oge_"):
        return "Valor previsto no Orçamento Geral do Estado, não o valor efectivamente gasto. Em 2015, 2016, 2019 e 2020 usa-se o OGE revisto."
    if i.startswith("ilo_"):
        return "Percentagem da população activa sem emprego, segundo estimativas da Organização Internacional do Trabalho."
    return "Indicador publicado pela fonte identificada nesta página."


def n(v: float) -> str:
    casas = 4 if abs(v) < 1 else 2
    t = f"{v:,.{casas}f}"
    return t.replace(",", " ").replace(".", ",")


def data_pt(iso: str) -> str:
    a, m, d = iso[:10].split("-")
    return f"{int(d)} de {MESES[int(m) - 1]} de {a}"


def previsao_desde(s: dict) -> int | None:
    return date.today().year if s["id"].startswith("imf_") else None


def _ano(p: str) -> int:
    return int(p[:4])


def grafico(obs: list[dict], desde: int | None, nome: str) -> str:
    if len(obs) < 2:
        return ""
    w, h, m = 900, 240, 8
    v = [o["valor"] for o in obs]
    lo, hi = min(v), max(v)
    amp = (hi - lo) or 1
    pts = [(m + i * (w - 2 * m) / (len(v) - 1), m + (hi - x) / amp * (h - 2 * m)) for i, x in enumerate(v)]
    corte = next((i for i, o in enumerate(obs) if desde and _ano(o["periodo"]) >= desde), len(obs))
    txt = lambda a: " ".join(f"{x:.1f},{y:.1f}" for x, y in a)
    linhas = f'<polyline points="{txt(pts[:max(corte, 1)])}" fill="none" stroke="#B80F2D" stroke-width="2.5"/>'
    if corte < len(pts):
        linhas += f'<polyline points="{txt(pts[max(corte - 1, 0):])}" fill="none" stroke="#B80F2D" stroke-width="2.5" stroke-dasharray="7 6"/>'
    alt = f"Gráfico de {nome}, de {obs[0]['periodo']} a {obs[-1]['periodo']}, entre {n(lo)} e {n(hi)}. Os valores estão na tabela abaixo."
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{escape(alt)}" style="width:100%;height:auto;display:block">{linhas}</svg>'


def pagina(s: dict, atuais: list[dict], revisoes: list[dict]) -> str:
    nome, unidade, fonte = escape(s["nome"]), escape(s["unidade"]), escape(s["fonte"])
    hoje = date.today().isoformat()
    url = f"{BASE}/serie/{s['id']}"
    desde = previsao_desde(s)
    prev = lambda o: bool(desde and _ano(o["periodo"]) >= desde)
    reais = [o for o in atuais if not prev(o)] or atuais
    ultimo = reais[-1] if reais else None
    descricao = f"{s['nome']}, Angola. Fonte: {s['fonte']}. Unidade: {s['unidade']}."
    ld = {"@context": "https://schema.org", "@type": "Dataset", "name": s["nome"], "description": explicar(s) + " " + descricao, "url": url,
          "spatialCoverage": {"@type": "Country", "name": "Angola"}, "creator": {"@type": "Organization", "name": "Dados da Banda", "url": BASE},
          "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": f"{BASE}/v1/series/{s['id']}/observacoes?formato=csv"},
                           {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": f"{BASE}/v1/series/{s['id']}/observacoes"}]}
    if atuais:
        ld["temporalCoverage"] = f"{atuais[0]['periodo']}/{atuais[-1]['periodo']}"
    linha = lambda o: (f'<tr><td>{escape(o["periodo"])}{" <span class=tag>previsão</span>" if prev(o) else ""}</td><td class="n">{n(o["valor"])}</td>'
                       f'<td>{data_pt(o["recolhido_em"])}</td></tr>')
    inv = atuais[::-1]
    cab = '<thead><tr><th scope="col">Período</th><th scope="col" class="n">Valor</th><th scope="col">Recolhido em</th></tr></thead>'
    tabela = f"<table><caption class=\"mut\" style=\"text-align:left;padding-bottom:6px\">Valores em {unidade}</caption>{cab}<tbody>{''.join(map(linha, inv[:12]))}</tbody></table>"
    if len(inv) > 12:
        tabela += f'<details style="margin-top:12px"><summary>Ver os restantes {len(inv) - 12} valores</summary><table>{cab}<tbody>{"".join(map(linha, inv[12:]))}</tbody></table></details>'
    aviso = f'<p class="mut"><span class="tag">previsão</span> Os valores a partir de {desde} são projecções do FMI, não dados observados.</p>' if desde and len(reais) < len(atuais) else ""
    rev = "".join(f'<tr><td>{escape(r["periodo"])}</td><td class="n">{n(r["antes"])}</td><td class="n">{n(r["depois"])}</td><td>{data_pt(r["data"])}</td></tr>' for r in revisoes[:30])
    bloco_rev = (f'<table><thead><tr><th scope="col">Período</th><th scope="col" class="n">Antes</th><th scope="col" class="n">Depois</th><th scope="col">Data</th></tr></thead><tbody>{rev}</tbody></table>'
                 if rev else '<p class="mut" style="margin:0">Sem valores alterados no histórico disponível.</p>')
    citacao = f"Dados da Banda. {s['nome']}. Fonte original: {s['fonte']}. Consultado em {data_pt(hoje)}. {url}"
    fonte_lig = f'<a class="btn" href="{escape(s["url_consulta"], quote=True)}" rel="noopener">Ver na fonte</a>' if s.get("url_consulta") else ""
    nav = "".join(f'<a href="{h}" style="">{t}</a>' for h, t in NAV)
    rod = "".join(f'<a href="{h}" style="color:#fff">{t}</a>' for h, t in RODAPE)
    return f"""<!doctype html><html lang="pt-AO"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{nome} · Dados da Banda</title><meta name="description" content="{escape(descricao, quote=True)}">
<link rel="canonical" href="{url}"><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<script src="/static/head-boost.js?v=6"></script><style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")}</script></head><body>
<header style="background:#fff;border-bottom:1px solid #E3E6EA"><div style="max-width:1200px;margin:0 auto;padding:16px 24px;display:flex;align-items:center;gap:32px;flex-wrap:wrap">
<a href="/" class="ddb-logo" aria-label="Dados da Banda, página inicial">Dados da Banda</a><nav style="display:flex;gap:24px;flex:1;flex-wrap:wrap;font-size:15px">{nav}</nav></div></header>
<main>
<div><div class="mut"><a href="/series.html">Todas as séries</a> · {fonte}</div><h1>{nome}</h1></div>
<section class="g">
<div class="cx"><div class="mut">Último valor{f" ({escape(ultimo['periodo'])})" if ultimo else ""}</div><div class="val">{n(ultimo['valor']) if ultimo else "—"}</div><div class="mut">{unidade}</div></div>
<div class="cx"><h2>O que significa</h2><p style="margin:0">{escape(explicar(s))}</p></div>
</section>
<section class="cx"><h2>Evolução</h2>{grafico(atuais, desde, s['nome'])}{aviso}
<div class="acoes" style="margin-top:14px"><a class="btn" href="/painel.html?s={s['id']}">Abrir no painel</a><a class="btn" href="/v1/series/{s['id']}/observacoes?formato=csv">Descarregar CSV</a><a class="btn" href="/v1/series/{s['id']}/observacoes">JSON</a>{fonte_lig}</div></section>
<section class="cx"><h2>Dados</h2>{tabela}</section>
<section class="g">
<div class="cx"><h2>Ficha técnica</h2><dl style="margin:0"><dt class="mut">Fonte</dt><dd style="margin:0 0 8px">{fonte}</dd><dt class="mut">Unidade</dt><dd style="margin:0 0 8px">{unidade}</dd><dt class="mut">Periodicidade</dt><dd style="margin:0 0 8px">{escape(s['periodicidade'])}</dd><dt class="mut">Código</dt><dd style="margin:0"><code>{s['id']}</code></dd></dl></div>
<div class="cx"><h2>Como citar</h2><p style="margin:0" id="citacao">{escape(citacao)}</p></div>
</section>
<section class="cx"><h2>Histórico de alterações</h2>{bloco_rev}<p class="mut" style="margin:10px 0 0">Correcções de método estão no <a href="/correcoes.html" style="color:#B80F2D;font-weight:600">registo público</a>.</p></section>
</main>
<footer style="margin-top:48px;background:#14274E;color:#fff;padding:24px"><div style="max-width:1200px;margin:0 auto;display:flex;gap:12px 20px;flex-wrap:wrap;font-size:14px"><span style="flex:1 1 280px">Projeto independente de dados abertos. Cada série identifica a sua fonte.</span>{rod}</div></footer>
</body></html>"""
