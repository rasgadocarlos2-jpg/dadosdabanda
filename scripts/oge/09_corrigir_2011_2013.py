import os
import json
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber

src = Path("f2011.py").read_text(encoding="utf-8")
TOPO = eval(re.search(r"TOPO = (\[.*?\n\])", src, re.S).group(1))
num = lambda s: float(s.replace(".", "").replace(",", ".")) / 1e9
with pdfplumber.open("pdfs_oge/2011_funcao.pdf") as d:
    txt = "\n".join((p.extract_text() or "") for p in d.pages)
soma = Counter()
for l in txt.split("\n"):
    m = re.match(r"^(.+?)\s+(\d[\d.]*,\d{2})\s+\d+,\d+%$", l)
    if m:
        for sid, rx in TOPO:
            if re.fullmatch(rx, m.group(1)):
                soma[sid] += num(m.group(2))
                break
linha = lambda p: sum(num(re.search(r"(\d[\d.]*,\d{2})", l).group(1)) for l in txt.split("\n") if re.match(p, l))
soma["oge_servicos_publicos"] -= soma["oge_encargos_financeiros"]
por_ano = {"2011": dict(soma)}
por_ano["2011"]["oge_divida_interna"] = linha(r"^Opera.{1,4}es D. D.{1,2}vida P.{1,2}blica Interna ")
por_ano["2011"]["oge_divida_externa"] = linha(r"^Opera.{1,4}es D. D.{1,2}vida P.{1,2}blica Externa ")
fv = json.load(open("funcoes_v3.json", encoding="utf-8"))
dv = json.load(open("divida_v2.json", encoding="utf-8"))
MAPA = {"servicos_publicos": "oge_servicos_publicos", "defesa": "oge_defesa", "seguranca": "oge_seguranca", "economico": "oge_setor_economico",
        "habitacao": "oge_habitacao", "saude": "oge_saude", "educacao": "oge_educacao", "protecao_social": "oge_protecao_social",
        "ambiente": "oge_ambiente", "recreacao": "oge_recreacao"}
for a in ("2012", "2013"):
    v = {sid: fv[a][k] / 1e9 for k, sid in MAPA.items()}
    enc = dv[a]["encargos_ou_divida"] / 1e9
    v["oge_servicos_publicos"] -= enc
    v["oge_encargos_financeiros"] = enc
    por_ano[a] = v
tot = {"2011": 4172.42, "2012": 4501.11, "2013": 6635.57}
linhas = []
agora = datetime.now(timezone.utc).isoformat()
for a, v in por_ano.items():
    s = sum(x for k, x in v.items() if k not in ("oge_divida_interna", "oge_divida_externa"))
    print(a, "soma", round(s, 2), "total", tot[a], {k: round(x, 1) for k, x in v.items()})
    assert abs(s - tot[a]) < 2, a
    linhas += [{"serie_id": k, "periodo": a, "valor": round(x, 2), "recolhido_em": agora, "hash_bruto": None} for k, x in v.items()]
U = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/"
K = os.environ["SUPABASE_KEY"]
H = {"apikey": K, "Authorization": "Bearer " + K, "Content-Type": "application/json", "Prefer": "return=minimal"}
urllib.request.urlopen(urllib.request.Request(U + "observacoes", data=json.dumps(linhas).encode(), method="POST", headers=H))
r = urllib.request.Request(U + "chaves_api?email=eq.teste-limite@x.ao", method="DELETE", headers={**H, "Prefer": "return=representation"})
print("gravado", len(linhas), "chaves de teste apagadas", len(json.load(urllib.request.urlopen(r))))
q = Path(r"C:\Users\Carlos Rasgado\Desktop\dadosdabanda\public\orcamento.html")
t = q.read_text(encoding="utf-8")
a = "addT(`OGE ${anoSel} — total aprovado`, total ? `${fmt(total,2)} tri Kz` : \"—\", subExec);"
assert a in t
t = t.replace(a, "const revisto = [\"2015\", \"2016\", \"2019\", \"2020\"].includes(anoSel);\n  addT(`OGE ${anoSel} — total ${revisto ? \"revisto\" : \"aprovado\"}`, total ? `${fmt(total,2)} tri Kz` : \"—\", subExec);")
q.write_text(t, encoding="utf-8")
