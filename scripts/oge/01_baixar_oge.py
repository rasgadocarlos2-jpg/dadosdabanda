"""Baixa os PDFs-chave do OGE de cada ano (2010-2026):
Lei + Relatório de Fundamentação + Despesa por Função A (com dívida)."""
import json, urllib.request, os, re
from pathlib import Path

OUT = Path(r"pdfs_oge")
OUT.mkdir(exist_ok=True)

CAT_PATH = r"minfin_cat.json"
cat = json.loads(open(CAT_PATH, "r", encoding="utf-8").read())

# Adicionar 2026
OGE2026 = [
    ("2026", "9278f553-680d-4715-8f2d-9e24f42d3d5f", "0. Lei Que Aprova o OGE 2026.pdf"),
    ("2026", "20bdf524-70b1-4b10-b509-ef79f76e61b3", "1. Relatorio de Fundamentacao OGE 2026.pdf"),
    ("2026", "fdfd3c37-c13c-40da-99c0-581c38694db7", "2. Estrategia Fiscal 2026-2031.pdf"),
    ("2026", "3089745f-7eca-48e9-906c-4041b9aee779", "6. Resumo da Despesa por Funcao A.pdf"),
    ("2026", "0e96b879-b74e-468a-b4ed-d4878167c432", "3. Resumo da Receita por Natureza Economica.pdf"),
]
cat = OGE2026 + cat

# Escolher: fundamentação por ano + função por ano
def rel(nome):
    nl = nome.lower()
    return any(p in nl for p in ["fundament", "relatorio", "relatório"])
def fun(nome):
    nl = nome.lower()
    return ("função a" in nl or "funcao a" in nl or ("função" in nl and "sem" not in nl) or ("funcao" in nl and "sem" not in nl)) and "despesa" in nl

por_ano = {}
for ano, uuid, nome in cat:
    por_ano.setdefault(ano, []).append((uuid, nome))

for ano in sorted(por_ano.keys(), reverse=True):
    cands = por_ano[ano]
    rels = [c for c in cands if rel(c[1])]
    funs = [c for c in cands if fun(c[1])]
    if rels:
        u, n = rels[0]
        fp = OUT / f"{ano}_fundamentacao.pdf"
        if not fp.exists():
            try:
                print(f"{ano} fund: {n[:60]}")
                urllib.request.urlretrieve(f"https://cms.minfin.gov.ao/api/assets/portal-minfin/{u}/", fp)
            except Exception as e: print(f"  err: {e}")
    if funs:
        u, n = funs[0]
        fp = OUT / f"{ano}_funcao.pdf"
        if not fp.exists():
            try:
                print(f"{ano} func: {n[:60]}")
                urllib.request.urlretrieve(f"https://cms.minfin.gov.ao/api/assets/portal-minfin/{u}/", fp)
            except Exception as e: print(f"  err: {e}")
print("concluído")
