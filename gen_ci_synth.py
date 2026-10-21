"""Generează imagini SINTETICE de CI românească (date fictive) pentru testare OCR."""
import random, json, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import mrz
F="/usr/share/fonts/truetype/dejavu/"
f=lambda n,s: ImageFont.truetype(F+n,s)
SANS,BOLD,MONO="DejaVuSans.ttf","DejaVuSans-Bold.ttf","DejaVuSansMono.ttf"
W="279146358279"
def cnpgen(sex,yy,mm,dd,jud):
    b=f"{sex}{yy:02d}{mm:02d}{dd:02d}{jud:02d}{random.randint(1,999):03d}"
    s=sum(int(a)*int(w) for a,w in zip(b,W))%11; return b+str(1 if s==10 else s)
PEOPLE=[("POPESCU","ȘTEFAN-RĂZVAN","M",85,3,7,"Jud.PH Mun.Câmpina","Jud.PH Mun.Ploiești","Str.Mărășești nr.3 bl.A2 ap.14","SPCLEP Ploiești","PH"),
 ("DUMITRESCU","IOANA-MĂDĂLINA","F",90,11,21,"Jud.BV Mun.Brașov","Jud.BV Mun.Brașov","Str.Lungă nr.77","SPCLEP Brașov","BV"),
 ("ȚĂRANU","GHEORGHE","M",62,6,15,"Jud.PH Orș.Sinaia","Jud.PH Orș.Bușteni","Str.Republicii nr.12","SPCLEP Bușteni","PX"),
 ("STĂNESCU","ANA-MARIA","F",99,1,30,"Mun.București Sec.3","Mun.București Sec.6","Bd.Iuliu Maniu nr.15 bl.8 sc.B et.4 ap.61","SPCEP S6 biroul nr.2","RT"),
 ("IONESCU","MIHAI","M",78,12,2,"Jud.CJ Mun.Cluj-Napoca","Jud.CJ Com.Florești","Str.Eroilor nr.201","SPCLEP Florești","CJ")]
def card(p,kind,seed):
    random.seed(seed)
    nume,pren,sex,yy,mm,dd,loc,dom1,dom2,emis,serie=p
    sx={"M":1,"F":2}[sex] if yy>=0 and yy<100 and yy>5 else 5
    if yy<6: sx={"M":5,"F":6}[sex]
    cnp=cnpgen(sx,yy,mm,dd,random.randint(1,46)); nr=f"{random.randint(100000,999999)}"
    ey=random.randint(27,34); emy=ey-10
    dob=f"{yy:02d}{mm:02d}{dd:02d}"; exp=f"{ey:02d}{mm:02d}{dd:02d}"
    asc=lambda s: s.translate(str.maketrans("ȘȚĂÂÎșțăâî","STAAIstaai"))
    img=Image.new("RGB",(1000,630),(214,228,236)); d=ImageDraw.Draw(img)
    for i in range(0,1000,7): d.line([(i,0),(i-200,630)],fill=(206,222,232))
    d.rectangle([40,150,300,480],fill=(170,170,175)); d.ellipse([110,200,230,320],fill=(120,120,125)); d.rectangle([90,330,250,480],fill=(120,120,125))
    lab=lambda x,y,t: d.text((x,y),t,font=f(SANS,15),fill=(70,90,120))
    val=lambda x,y,t,s=24: d.text((x,y),t,font=f(BOLD,s),fill=(15,15,25))
    truth={"nume":f"{nume} {pren}" ,"cnp":cnp,"ci_serie":serie,"ci_numar":nr,"data_nasterii":f"{dd:02d}.{mm:02d}.{1900+yy if yy>5 else 2000+yy}","sex":sex,"cetatenie":"română","ci_valabilitate":f"{dd:02d}.{mm:02d}.20{ey}","ci_emitent":emis}
    if kind=="veche":
        d.text((330,20),"ROMÂNIA  ROUMANIE  ROMANIA",font=f(BOLD,22),fill=(20,40,90))
        d.text((330,52),"CARTE DE IDENTITATE  CARTE D'IDENTITE  IDENTITY CARD",font=f(SANS,15),fill=(20,40,90))
        val(330,82,f"SERIA {serie} NR {nr}",24); val(40,95,f"CNP {cnp}",22)
        rows=[("Nume/Nom/Last name",nume),("Prenume/Prenom/First name",pren),("Cetățenie/Nationalité/Nationality","Română / ROU"),
              ("Loc naștere/Lieu de naissance/Place of birth",loc),("Domiciliu/Adresse/Address",dom1)]
        y=125
        for l,v in rows: lab(330,y,l); val(330,y+18,v,22); y+=52
        val(330,y-8,dom2,22); y+=26
        lab(330,y,"Emisă de/Délivrée par/Issued by"); lab(700,y,"Valabilitate/Validité/Validity")
        val(330,y+18,emis,20); val(700,y+18,f"{dd:02d}.{mm:02d}.{emy:02d}-{dd:02d}.{mm:02d}.20{ey}",20)
        lab(860,125,"Sex/Sexe/Sex"); val(860,143,sex)
        L=mrz.make_td2(asc(nume),asc(pren),serie,nr,dob,sex,exp,cnp)
        d.rectangle([0,500,1000,630],fill=(236,240,240))
        for i,l in enumerate(L): d.text((30,515+i*52),l,font=f(MONO,37),fill=(0,0,0))
        truth["domiciliu"]=f"{dom1} {dom2}"
        return [img],truth
    # CEI: față + verso
    d.text((330,20),"ROMÂNIA",font=f(BOLD,26),fill=(20,40,90)); d.text((330,55),"CARTE DE IDENTITATE / IDENTITY CARD",font=f(SANS,16),fill=(20,40,90))
    val(720,20,f"{serie}{nr}",26)
    rows=[("Nume / Last name",nume),("Prenume / First name",pren),("Sex / Sex",sex),("Cetățenie / Nationality","ROU"),
          ("Data nașterii / Date of birth",f"{dd:02d}.{mm:02d}.{1900+yy if yy>5 else 2000+yy}"),("Locul nașterii / Place of birth",loc)]
    y=95
    for l,v in rows: lab(330,y,l); val(330,y+18,v,22); y+=50
    lab(330,y,"Emisă de / Issued by"); val(330,y+18,emis,20)
    lab(700,y,"Data expirării / Date of expiry"); val(700,y+18,f"{dd:02d}.{mm:02d}.20{ey}",20)
    lab(700,95,"CNP / Personal No."); val(700,113,cnp,22)
    back=Image.new("RGB",(1000,630),(214,228,236)); bd=ImageDraw.Draw(back)
    for i in range(0,1000,7): bd.line([(i,0),(i-200,630)],fill=(206,222,232))
    bd.rectangle([0,400,1000,630],fill=(236,240,240))
    L=mrz.make_td1(asc(nume),asc(pren),serie,nr,dob,sex,exp,cnp)
    for i,l in enumerate(L): bd.text((60,415+i*68),l,font=f(MONO,44),fill=(0,0,0))
    truth["domiciliu"]=""  # CEI nu are domiciliul tipărit
    return [img,back],truth
def photo(img,seed):
    random.seed(seed)
    bg=Image.new("RGB",(1300,950),(random.randint(60,140),)*3)
    im=img.rotate(random.uniform(-4,4),expand=True,fillcolor=(0,0,0,0) if False else None,resample=Image.BICUBIC)
    bg.paste(im,(random.randint(40,200),random.randint(40,200)))
    bg=bg.filter(ImageFilter.GaussianBlur(random.uniform(0.6,1.3)))
    import numpy as np
    a=np.array(bg).astype(float); a+=np.random.normal(0,8,a.shape); a=a*random.uniform(0.85,1.1)
    return Image.fromarray(a.clip(0,255).astype("uint8"))
if __name__=="__main__":
    out=sys.argv[1]; cases=[]
    for i,p in enumerate(PEOPLE):
        for kind in ("veche","cei"):
            imgs,truth=card(p,kind,i*10+(kind=="cei"))
            for variant in ("scan","foto"):
                files=[]
                for j,im in enumerate(imgs):
                    if variant=="foto": im=photo(im,i*100+j)
                    fn=f"{out}/ci_{i}_{kind}_{variant}_{j}.jpg"; im.save(fn,quality=80 if variant=="foto" else 92); files.append(fn)
                cases.append({"files":files,"kind":kind,"variant":variant,"truth":truth})
    json.dump(cases,open(f"{out}/cases.json","w"),ensure_ascii=False,indent=1); print(len(cases),"cazuri")
