import re,json,pdfplumber,urllib.request
num=lambda s: float(s.replace(".","").replace(",","."))/1e9
TOPO=[("total",r"^Total Geral"),("servicos_publicos",r"^Servi.{1,3}os P.{1,2}blicos Gerais \d"),("defesa",r"^Defesa \d"),("seguranca",r"^Seguran.{1,3} E Ordem P.{1,2}blica \d"),
("educacao",r"^Educa.{1,4}o \d"),("saude",r"^Sa.{1,2}de \d"),("protecao_social",r"^Protec.{1,4}o Social \d"),("habitacao",r"^Habita.{1,4}o E Servi.{1,3}os Comunit.{1,2}rios \d"),
("economico",r"^Assuntos Econ.{1,2}micos \d"),("divida",r"^(Encargos Financeiros|Opera.{1,4}es D. D.{1,2}vida P.{1,2}blica) \d")]
out={}
for a in ["2023","2024","2025"]:
    with pdfplumber.open(f"cge/cge_{a}_funcao.pdf") as d:
        print(a,"pags",len(d.pages)); txt="\n".join((p.extract_text() or "") for p in d.pages)
    hd=[l for l in txt.split("\n") if "Per" in l and "odo" in l][:1]; print(hd)
    o={}
    for l in txt.split("\n"):
        n=re.findall(r"\d[\d.]*,\d{2}",l)
        if len(n)!=8: continue
        for k,rx in TOPO:
            if k not in o and re.match(rx,l): o[k]={"orc":round(num(n[0]),2),"liq":round(num(n[4]),2),"pago":round(num(n[6]),2)}
    out[a]=o
    print({k:(v["orc"],v["liq"],v["pago"]) for k,v in o.items()})
json.dump(out,open("exec_v4.json","w"),indent=0)
