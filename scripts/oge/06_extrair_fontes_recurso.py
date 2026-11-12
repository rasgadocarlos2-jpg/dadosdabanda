import json,re,urllib.request
from pathlib import Path
import pdfplumber
P=Path("pdfs_font"); P.mkdir(exist_ok=True)
cat=json.load(open("../../public/static/minfin-pdfs.json",encoding="utf-8"))["pdfs"]
cat=[{"ano":2026,"uuid":"9ca6be66-e5d5-43a6-b0bd-0c53da0ce687","nome":"Resumo da Receita por Fonte de Recurso.pdf"}]+cat
por={}
for p in cat:
    n=p["nome"].lower()
    if "receita" in n and "fonte" in n: por.setdefault(p["ano"],[]).append(p)
for a,l in sorted(por.items()):
    print(a,len(l),[x["nome"][:34] for x in l])
    for i,x in enumerate(l):
        f=P/f"{a}_{i}.pdf"
        if not f.exists(): urllib.request.urlretrieve(f"https://cms.minfin.gov.ao/api/assets/portal-minfin/{x['uuid']}/",f)
num=lambda s: float(s.replace(".","").replace(",","."))
res={}
for f in sorted(P.glob("*.pdf")):
    with pdfplumber.open(f) as d:
        txt="\n".join((p.extract_text() or "") for p in d.pages[:4])
    linhas=[]
    for l in txt.split("\n"):
        m=re.match(r"^(?:[\d.]+ - )?(.+?)\s+(\d[\d.]*,\d{2})\s+(\d+,\d+)%?\s*$",l)
        if m: linhas.append((m.group(1),round(num(m.group(2))/1e9,2),m.group(3)))
    t=re.search(r"Total Geral:?\s+(\d[\d.]*,\d{2})",txt)
    res[f.stem]={"total":round(num(t.group(1))/1e9,2) if t else None,"linhas":linhas}
json.dump(res,open("fontes_rec.json","w",encoding="utf-8"),ensure_ascii=False,indent=0)
for k in ["2011_0","2016_0","2020_0","2026_0"]:
    if k in res: print("==",k,res[k]["total"]); [print("  ",*x) for x in res[k]["linhas"][:16]]
print({k:(v["total"],len(v["linhas"])) for k,v in res.items()})
