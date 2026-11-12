"""Extrai Operações da Dívida Pública (interna + externa) de 2011-2026."""
import pdfplumber, re, json
from pathlib import Path

DIR = Path(r".")

def norm(s):
    s = s.lower()
    for a,b in [("á","a"),("ã","a"),("â","a"),("é","e"),("ê","e"),("í","i"),("ó","o"),("ô","o"),("ú","u"),("ç","c")]:
        s = s.replace(a,b)
    return s

def parse_num(s):
    s = s.strip()
    if "," in s: s = s.replace(".", "").replace(",", ".")
    else: s = s.replace(".", "")
    try: return float(s)
    except: return None

resultados = {}
for pdf_path in sorted((DIR / "pdfs_oge").glob("*_funcao.pdf")):
    ano = pdf_path.stem.split("_")[0]
    try:
        with pdfplumber.open(pdf_path) as pdf:
            txt = ""
            for p in pdf.pages[:20]: txt += (p.extract_text() or "") + "\n"
    except: resultados[ano] = None; continue

    enc = interna = externa = None
    for linha in txt.split("\n"):
        ln = norm(linha.strip())
        nums = re.findall(r"[\d]{1,3}(?:\.[\d]{3})+(?:,\d{1,2})?", linha)
        if not nums: continue
        # Encargos Financeiros (função topo)
        if re.search(r"^encargos financeiros", ln):
            enc = parse_num(nums[0])
        # Operações Dívida Pública (função topo, antigo) — tolera encoding partido
        elif re.search(r"opera.{1,3}es? d. d.vida p.blica", ln) or re.search(r"opera.{1,3}es? d. d\W+vida p\W+blica", ln):
            if "interna" not in ln and "externa" not in ln:
                if not enc: enc = parse_num(nums[0])
            elif "interna" in ln and not interna:
                interna = parse_num(nums[0])
            elif "externa" in ln and not externa:
                externa = parse_num(nums[0])
    resultados[ano] = {"encargos_ou_divida": enc, "divida_interna": interna, "divida_externa": externa}

for ano in sorted(resultados, reverse=True):
    v = resultados[ano] or {}
    e = v.get("encargos_ou_divida"); i = v.get("divida_interna"); x = v.get("divida_externa")
    print(f"{ano}: total={e/1e12 if e else '-'} interna={i/1e12 if i else '-'} externa={x/1e12 if x else '-'}")

Path(DIR / "divida_v2.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
