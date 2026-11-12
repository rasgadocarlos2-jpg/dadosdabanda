import os
import json,urllib.request,urllib.error
from datetime import datetime,timezone
U = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/"
K = os.environ["SUPABASE_KEY"]
H={"apikey":K,"Authorization":"Bearer "+K,"Content-Type":"application/json"}
def rq(m,p,d=None,pref="return=representation"):
    r=urllib.request.Request(U+p,data=json.dumps(d).encode() if d is not None else None,method=m,headers={**H,"Prefer":pref})
    try:
        b=urllib.request.urlopen(r).read(); return json.loads(b) if b else []
    except urllib.error.HTTPError as e: print("ERRO",m,p[:60],e.code,e.read().decode()[:200]); return None
agora=datetime.now(timezone.utc).isoformat()
def serie(i,f,n,u,url):
    rq("POST","series?on_conflict=id",{"id":i,"fonte_id":f,"codigo":i.upper(),"nome":n,"unidade":u,"periodicidade":"anual","url_consulta":url},"return=minimal,resolution=merge-duplicates")
def obs(i,vals):
    rows=[{"serie_id":i,"periodo":str(a),"valor":v,"recolhido_em":agora,"hash_bruto":None} for a,v in sorted(vals.items()) if v is not None]
    if rows: rq("POST","observacoes",rows,"return=minimal")
    return len(rows)
def apagar_serie(i):
    a=rq("DELETE",f"observacoes?serie_id=eq.{i}"); b=rq("DELETE",f"series?id=eq.{i}")
    print("apagada",i,len(a or []),"obs",len(b or []),"serie")
OGE="https://www.minfin.gov.ao/oge/oge-passados"; CGE="https://www.minfin.gov.ao/oge/conta-geral-do-estado"
# 1 PIB
wb=json.load(urllib.request.urlopen("https://api.worldbank.org/v2/country/AGO/indicator/NY.GDP.MKTP.CN?format=json&per_page=60&date=2004:2026"))[1]
serie("wb_pib_kz","banco_mundial","PIB a preços correntes, em kwanzas","mil milhões Kz","https://data.worldbank.org/indicator/NY.GDP.MKTP.CN?locations=AO")
print("pib",obs("wb_pib_kz",{r["date"]:round(r["value"]/1e9,1) for r in wb if r["value"]}))
apagar_serie("ao_pib_nominal_kz")
# 2 fontes
for i,lic in [("minfin","Documentos públicos do Ministério das Finanças, reutilizados com atribuição. Sem autorização específica."),
              ("minfin_fundamentacao","Documentos públicos do Ministério das Finanças, reutilizados com atribuição. Sem autorização específica."),
              ("minfin_cge","Documentos públicos do Ministério das Finanças, reutilizados com atribuição. Sem autorização específica.")]:
    r=rq("PATCH",f"fontes?id=eq.{i}",{"estado_autorizacao":"publica","licenca":lic}); print(i,r and r[0]["estado_autorizacao"])
# 3 receita
apagar_serie("oge_receita_petrolifera"); apagar_serie("oge_receita_nao_petrolifera")
print("rec tot apagadas",len(rq("DELETE","observacoes?serie_id=eq.oge_receita_total") or []))
print("rec cor apagadas",len(rq("DELETE","observacoes?serie_id=eq.oge_receita_correntes") or []))
pet=json.load(open("petro.json")); fr=json.load(open("fontes_rec.json")); fv=json.load(open("funcoes_v3.json"))
serie("oge_receita_petroleo","minfin_fundamentacao","OGE — Receita petrolífera prevista (impostos e partilha de produção)","mil milhões Kz",OGE)
print("petroleo",obs("oge_receita_petroleo",{a:v["petroleo"] for a,v in pet.items()}))
print("correntes",obs("oge_receita_correntes",{a:v["correntes"] for a,v in pet.items()}))
GR={"tesouro":("oge_fonte_tesouro","Recursos Ordinários do Tesouro"),"fin_int":("oge_fonte_fin_interno","Financiamentos Internos"),"fin_ext":("oge_fonte_fin_externo","Financiamentos Externos"),
    "proprios":("oge_fonte_proprios","Recursos Próprios"),"consig":("oge_fonte_consignados","Recursos Consignados"),"outros":("oge_fonte_outros","Outras fontes")}
por={k:{} for k in GR}; totais={}
for a in sorted(fv):
    alvo=fv[a]["total_geral"]/1e9
    cands=[v for k,v in fr.items() if k.startswith(a) and v["total"] and abs(v["total"]-alvo)<1]
    if not cands: print("sem fonte a coincidir",a,round(alvo),[ (k,v['total']) for k,v in fr.items() if k.startswith(a)]); continue
    L=cands[0]["linhas"]; totais[a]=cands[0]["total"]
    soma=lambda *p: round(sum(x[1] for x in L if any(q in x[0] for q in p)),2)
    v={"tesouro":soma("Ordin"),"fin_int":soma("Financiamentos Internos"),"fin_ext":soma("Financiamentos Externos"),"proprios":soma("Recursos Pr"),"consig":soma("Consignados")}
    v["outros"]=round(totais[a]-sum(v.values()),2)
    for k in v: por[k][a]=v[k]
print("totais",obs("oge_receita_total",totais))
for k,(i,n) in GR.items():
    serie(i,"minfin_fundamentacao","OGE — Fonte de recurso: "+n,"mil milhões Kz",OGE); print(i,obs(i,por[k]))
print("2026",{k:por[k].get("2026") for k in por}); print("2019 ficheiros",[(k,v["total"]) for k,v in fr.items() if k[:4] in("2019","2020","2015")])
# 4 execucao
ex=json.load(open("exec_v4.json"))
NOM={"total":"Total","servicos_publicos":"Serviços Públicos Gerais","defesa":"Defesa","seguranca":"Segurança e Ordem Pública","educacao":"Educação","saude":"Saúde","protecao_social":"Protecção Social","habitacao":"Habitação e Serviços Comunitários","economico":"Assuntos Económicos","divida":"Serviço da dívida"}
for i in ["oge_executado_educacao","oge_executado_saude","oge_executado_defesa","oge_executado_servicos_publicos","oge_executado_habitacao","oge_executado_economico"]: apagar_serie(i)
apagar_serie("oge_executado_total")
serie("oge_executado_total","minfin_cge","OGE — Despesa paga (Conta Geral do Estado)","biliões Kz",CGE)
print(obs("oge_executado_total",{a:round(ex[a]["total"]["pago"]/1000,3) for a in ex}))
for k,n in NOM.items():
    for m,tt in (("orc","dotação inicial"),("liq","liquidado"),("pago","pago")):
        i=f"cge_{m}_{k}"; serie(i,"minfin_cge",f"CGE — {n}: {tt}","mil milhões Kz",CGE); obs(i,{a:ex[a][k][m] for a in ex})
out={"fonte":"MINFIN, Conta Geral do Estado, Anexo 11","anos":ex,"nomes":NOM}
json.dump(out,open("../../public/static/oge-execucao.json","w",encoding="utf-8"),ensure_ascii=False)
print("ok")
