"""Parser v3 — case-insensitive, aceita códigos e acentos partidos."""
import json, re
from pathlib import Path
import pdfplumber

DIR = Path(r".")
PDFS = DIR / "pdfs_oge"

def norm(s):
    """Normaliza: substitui . e � e caracteres partidos por .+."""
    s = s.lower()
    s = re.sub(r"[àáâãä]", "a", s)
    s = re.sub(r"[éèê]", "e", s)
    s = re.sub(r"[íìî]", "i", s)
    s = re.sub(r"[óòôõ]", "o", s)
    s = re.sub(r"[úùû]", "u", s)
    s = re.sub(r"ç", "c", s)
    return s

# Padrões procurados na linha normalizada e deencodificada:
# A chave é um padrão de substring que pode casar com "Educação" ou "Educa��o"
def pattern(s):
    # "educação" + possíveis bytes partidos no meio
    return re.compile("(?:^|[^a-z])" + s.replace(".", ".{1,2}") + "\\b", re.IGNORECASE)

PATRÕES = [
    ("servicos_publicos",  [r"servi.os\s+publicos\s+gerais"]),
    ("defesa",             [r"(?<!e\s)(?<!ao\s)defesa(?!\s+militar)(?!\s+e\s+)"]),  # "Defesa" como função-topo
    ("seguranca",          [r"seguran.a\s+e\s+ordem", r"seguranca\s+e\s+ordem"]),
    ("economico",          [r"assuntos\s+econ.micos", r"afetos\s+econ.micos", r"assuntos\s+economicos"]),
    ("habitacao",          [r"habita.ao\s+e\s+servi", r"habitacao\s+e\s+servi"]),
    ("saude",              [r"(?:^|[-\s])sa.de(?:\s|$)", r"(?:^|[-\s])saude(?:\s|$)"]),
    ("educacao",           [r"(?:^|[-\s])educa.ao(?:\s|$)", r"(?:^|[-\s])educacao(?:\s|$)"]),
    ("protecao_social",    [r"protec.ao\s+social", r"protecao\s+social"]),
    ("ambiente",           [r"protec.ao\s+ambient", r"protecao\s+ambient"]),
    ("recreacao",          [r"recrea.ao,?\s*cultura", r"recreacao,?\s*cultura"]),
]

def parse_num(s):
    s = s.strip()
    if "," in s: s = s.replace(".", "").replace(",", ".")
    else: s = s.replace(".", "")
    try: return float(s)
    except: return None

def extrai(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            txt = ""
            for p in pdf.pages[:20]:
                txt += (p.extract_text() or "") + "\n"
    except Exception as e:
        return {"err": str(e)}

    # Total
    m = re.search(r"total\s+geral:?\s+([\d.,]+)", txt, re.IGNORECASE)
    total = parse_num(m.group(1)) if m else None
    valores = {"total_geral": total}

    for linha in txt.split("\n"):
        linha_norm = norm(linha)
        # Ignorar sub-itens "XX.XX.XX" — só funções-topo "XX - ..."
        is_sub = re.match(r"^\s*\d{2}\.\d{2}", linha)
        for chave, pats in PATRÕES:
            if chave in valores: continue
            if is_sub: continue
            for pat in pats:
                if re.search(pat, linha_norm):
                    nums = re.findall(r"[\d]{1,3}(?:\.[\d]{3})+(?:,\d{1,2})?", linha)
                    if nums:
                        v = parse_num(nums[0])
                        if v and v > 100_000_000:  # >100M Kz
                            valores[chave] = v
                            break
    return valores

resultados = {}
for pdf_path in sorted(PDFS.glob("*_funcao.pdf")):
    ano = pdf_path.stem.split("_")[0]
    resultados[ano] = extrai(pdf_path)

for ano in sorted(resultados, reverse=True):
    v = resultados[ano]
    if "err" in v: print(f"{ano}: ERR"); continue
    tot = v.get("total_geral", 0) / 1e12 if v.get("total_geral") else 0
    ed = v.get("educacao", 0) / 1e12 if v.get("educacao") else 0
    sd = v.get("saude", 0) / 1e12 if v.get("saude") else 0
    df = v.get("defesa", 0) / 1e12 if v.get("defesa") else 0
    print(f"{ano}: {len(v)-1} fns | total={tot:.2f} educ={ed:.3f} saude={sd:.3f} def={df:.3f}")

(DIR / "funcoes_v3.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
