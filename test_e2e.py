import json, sys, os, requests
W="279146358279"
def cnp(b):
    s=sum(int(a)*int(w) for a,w in zip(b,W))%11; return b+str(1 if s==10 else s)
base=sys.argv[1] if len(sys.argv)>1 else "http://localhost:5055"
pw=open(os.path.join(os.path.dirname(__file__),"..",".app_password")).read().strip()
A=cnp("185030729001"); B=cnp("290112129002"); P=cnp("160061529003")
d={"denumire":"Brădet Consult","alternative":["Brădet Soluții Digitale","Ștejar Țărăncuța"],
 "sediu":{"judet":"Prahova","localitate":"Ploiești","strada":"Mihai Bravu","numar":"12","bloc":"A3","scara":"B","etaj":"2","ap":"14","carte_funciara":"123456","durata_comodat":"5","activitate_la_sediu":False,
  "proprietar":{"nume":"Ionescu Gheorghiță","cnp":P,"ci_serie":"PH","ci_numar":"654321","domiciliu":"Ploiești, str. Văleni nr. 5, jud. Prahova"}},
 "asociati":[{"nume":"Popescu Ștefan-Răzvan","cnp":A,"cetatenie":"română","data_nasterii":"07.03.1985","loc_nastere":"Câmpina","ci_serie":"PH","ci_numar":"123456","ci_emitent":"SPCLEP Ploiești","ci_data":"10.01.2022","domiciliu":"Ploiești, str. Mărășești nr. 3, jud. Prahova","cota":"60"},
  {"nume":"Dumitrescu Ioana-Mădălina","cnp":B,"cetatenie":"română","data_nasterii":"21.11.1990","loc_nastere":"Brașov","ci_serie":"BV","ci_numar":"987654","ci_emitent":"SPCLEP Brașov","ci_data":"05.05.2021","domiciliu":"Brașov, str. Lungă nr. 77, jud. Brașov","cota":"40"}],
 "administratori":[],"capital":"1000","valoare_parte":"10","caen_principal":"6210","caen_principal_desc":"Activități de realizare a software-ului la comandă","caen_secundare":["6220","7022"],"durata":"nelimitata","durata_ani":""}
d["administratori"]=[dict(d["asociati"][0],mandat="nelimitată")]
H={"X-Requested-With":"fetch"}
anon=requests.Session()
r=anon.get(base+"/",allow_redirects=False); print("neautentificat /:",r.status_code,r.headers.get("Location"))
r=anon.post(base+"/api/genereaza",json={"data":d},headers=H); print("neautentificat API:",r.status_code)
r=anon.post(base+"/login",data={"user":"admin","parola":"gresita"}); print("parolă greșită ->", "eroare afișată" if "greșită" in r.text else "??")
s=requests.Session()
r=s.post(base+"/login",data={"user":"admin","parola":pw},allow_redirects=False); print("login:",r.status_code,r.headers.get("Location"))
r=s.post(base+"/api/genereaza",json={"data":d}); print("fără X-Requested-With (CSRF):",r.status_code)
j=s.post(base+"/api/genereaza",json={"data":d},headers=H).json(); print("generare:",j["ok"],"dosar",j["dosar_id"],len(j["fisiere"]),"PDF")
for n in j["fisiere"]:
    c=s.get(f"{base}/dosar/{j['id']}/{n}").content; assert c[:4]==b"%PDF"; open(f"/tmp/out_{n}","wb").write(c)
print("PDF-uri descărcate OK; ZIP:", s.get(f"{base}/dosar/{j['id']}.zip").headers.get("Content-Type"))
d2=json.loads(json.dumps(d)); d2["capital"]="2000"
j2=s.post(base+"/api/genereaza",json={"data":d2,"dosar_id":j["dosar_id"]},headers=H).json(); print("re-salvare același dosar:",j2["dosar_id"]==j["dosar_id"])
print("dosar citit, capital =", s.get(f"{base}/api/dosare/{j['dosar_id']}").json()["data"]["capital"])
rg=s.post(f"{base}/api/dosare/{j['dosar_id']}/regenereaza",headers=H).json(); print("regenerare:",rg["ok"],len(rg["fisiere"]))
print("persoane salvate:",[p["nume"] for p in s.get(base+"/api/persoane").json()])
print("căutare 'Dumitr':",[p["nume"] for p in s.get(base+"/api/persoane?q=Dumitr").json()])
print("firme:",[c["denumire"] for c in s.get(base+"/api/firme").json()])
print("pagina dosare conține firma:", "BRĂDET" in s.get(base+"/dosare?q=Brădet").text.upper())
case=json.load(open("/workspace/platforma_firme/ci_test/cases.json"))[0]
files=[("imagini",(os.path.basename(f),open(f,"rb"),"image/jpeg")) for f in case["files"]]
r=s.post(base+"/api/ci",files=files,headers=H).json()["rezultat"]; print("OCR CI:",{k:r.get(k) for k in ["nume","cnp","ci_serie","ci_numar","data_nasterii","sex","domiciliu","ci_emitent","ci_valabilitate"]}, r.get("mrz",{}).get("verificari"), r["avertismente"])
b=s.get(base+"/api/backup"); print("backup:",b.status_code,len(b.content),"bytes",list(b.json().keys()))
