"""Para cada ano 2010-2026, procura Receita por Natureza no catálogo e baixa."""
import json, urllib.request, re
from pathlib import Path

DIR = Path(r".")
OUT = DIR / "pdfs_rec"
OUT.mkdir(exist_ok=True)

cat_pdfs = json.loads(Path("../../public/static/minfin-pdfs.json").read_text(encoding="utf-8"))["pdfs"]

# Ano 2026 manual
EXTRA_2026 = {"ano": 2026, "uuid": "0e96b879-b74e-468a-b4ed-d4878167c432", "nome": "Resumo da Receita por Natureza Económica.pdf"}
cat_pdfs = [EXTRA_2026] + cat_pdfs

por_ano = {}
for p in cat_pdfs:
    if "receita" in p["nome"].lower() and "natureza" in p["nome"].lower() and "u.o" not in p["nome"].lower() and "unidade" not in p["nome"].lower():
        por_ano.setdefault(p["ano"], p)  # primeiro match por ano

for ano, p in sorted(por_ano.items(), reverse=True):
    fp = OUT / f"{ano}_receita.pdf"
    if fp.exists(): continue
    try:
        print(f"{ano}: {p['nome'][:60]}")
        urllib.request.urlretrieve(f"https://cms.minfin.gov.ao/api/assets/portal-minfin/{p['uuid']}/", fp)
    except Exception as e: print(f"  err: {e}")

print(f"\n{len(por_ano)} anos cobertos")
