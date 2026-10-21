import json, sys, urllib.request
W="279146358279"
def cnp(b):
    s=sum(int(a)*int(w) for a,w in zip(b,W))%11; return b+str(1 if s==10 else s)
A=cnp("185030729001"); B=cnp("290112129002"); P=cnp("160061529003")
base=sys.argv[1] if len(sys.argv)>1 else "http://localhost:5055"
d={"denumire":"Brădet Consult","alternative":["Brădet Soluții Digitale","Ștejar Țărăncuța"],
 "sediu":{"judet":"Prahova","localitate":"Ploiești","strada":"Mihai Bravu","numar":"12","bloc":"A3","scara":"B","etaj":"2","ap":"14","carte_funciara":"123456","durata_comodat":"5","activitate_la_sediu":False,
  "proprietar":{"nume":"Ionescu Gheorghiță","cnp":P,"ci_serie":"PH","ci_numar":"654321","domiciliu":"Ploiești, str. Văleni nr. 5, jud. Prahova"}},
 "asociati":[{"nume":"Popescu Ștefan-Răzvan","cnp":A,"cetatenie":"română","data_nasterii":"07.03.1985","loc_nastere":"Câmpina","ci_serie":"PH","ci_numar":"123456","ci_emitent":"SPCLEP Ploiești","ci_data":"10.01.2022","domiciliu":"Ploiești, str. Mărășești nr. 3, jud. Prahova","cota":"60"},
  {"nume":"Dumitrescu Ioana-Mădălina","cnp":B,"cetatenie":"română","data_nasterii":"21.11.1990","loc_nastere":"Brașov","ci_serie":"BV","ci_numar":"987654","ci_emitent":"SPCLEP Brașov","ci_data":"05.05.2021","domiciliu":"Brașov, str. Lungă nr. 77, jud. Brașov","cota":"40"}],
 "administratori":[],"capital":"1000","valoare_parte":"10","caen_principal":"6210","caen_principal_desc":"Activități de realizare a software-ului la comandă","caen_secundare":["6220","7022"],"durata":"nelimitata","durata_ani":""}
d["administratori"]=[dict(d["asociati"][0],mandat="nelimitată")]
def post(x):
    r=urllib.request.Request(base+"/api/genereaza",json.dumps(x).encode(),{"Content-Type":"application/json"})
    try: return json.load(urllib.request.urlopen(r))
    except urllib.error.HTTPError as e: return json.load(e)
bad=json.loads(json.dumps(d)); bad["asociati"][1]["cota"]="30"; bad["capital"]="1"; bad["asociati"][0]["cnp"]=A[:-1]+str((int(A[-1])+1)%10)
print("INVALID:", post(bad)["erori"])
j=post(d); print("VALID:", j)
for n in j["fisiere"]:
    urllib.request.urlretrieve(f"{base}/dosar/{j['id']}/{n}", f"/tmp/out_{n}")
urllib.request.urlretrieve(f"{base}/dosar/{j['id']}.zip","/tmp/out.zip"); print("zip ok")
