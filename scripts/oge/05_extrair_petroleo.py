import re,json,urllib.request,pdfplumber
from pathlib import Path
R=Path("pdfs_rec"); f15=R/"2015b_receita.pdf"
if not f15.exists(): urllib.request.urlretrieve("https://cms.minfin.gov.ao/api/assets/portal-minfin/510f1d84-84d9-445c-9f0b-1001c4043e9f/",f15)
num=lambda s: float(s.replace(".","").replace(",","."))/1e9
PAD={"rend":r"Imp.*Rendimentos? .*(Petr.l|Petr.{1,2}l)","trans":r"Transa.*Petr","prod":r"Imp.*Prod.*Petr","part":r"Partilha D. Produ|Rendimentos Das Concess"}
out={}
for f in sorted(R.glob("*_receita.pdf")):
    a=f.stem[:4]
    if f.stem=="2015_receita": continue
    with pdfplumber.open(f) as d: txt="\n".join((p.extract_text() or "") for p in d.pages)
    v={}; tot=None; cor=None
    for l in txt.split("\n"):
        n=re.findall(r"\d[\d.]*,\d{2}",l)
        if not n: continue
        if tot is None and "Total Geral" in l: tot=num(n[0])
        if cor is None and re.search(r"Receitas Correntes",l): cor=num(n[0])
        if re.search(r"Derivados|Diamant",l): continue
        for k,rx in PAD.items():
            if k not in v and re.search(rx,l): v[k]=num(n[0])
    s=sum(v.values()); out[a]={"total":round(tot,2),"correntes":round(cor,2) if cor else None,"petroleo":round(s,2),"comp":{k:round(x,1) for k,x in v.items()}}
    print(a,round(tot),cor and round(cor),round(s),f"{s/cor*100:.0f}%" if cor else "-",out[a]["comp"])
json.dump(out,open("petro.json","w"),indent=0)
