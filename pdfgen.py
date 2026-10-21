import os
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape as x

F = os.path.join(os.path.dirname(__file__), "fonts")
for n, f in [("Serif", "DejaVuSerif.ttf"), ("Serif-B", "DejaVuSerif-Bold.ttf"), ("Sans", "DejaVuSans.ttf"), ("Sans-B", "DejaVuSans-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(n, os.path.join(F, f)))
from reportlab.lib.fonts import addMapping
addMapping("Serif", 0, 0, "Serif"); addMapping("Serif", 1, 0, "Serif-B")

BODY = ParagraphStyle("b", fontName="Serif", fontSize=10.5, leading=15, alignment=TA_JUSTIFY, spaceAfter=5)
H1 = ParagraphStyle("h1", fontName="Serif-B", fontSize=15, leading=20, alignment=TA_CENTER, spaceAfter=4)
H2 = ParagraphStyle("h2", fontName="Serif-B", fontSize=11, leading=15, spaceBefore=8, spaceAfter=3)
SUB = ParagraphStyle("s", fontName="Serif", fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor("#444"), spaceAfter=10)
DRAFT_TXT = "PROIECT – DE VALIDAT DE AVOCAT"

def _page(c, doc):
    c.saveState()
    c.setFont("Sans-B", 36); c.setFillColor(colors.Color(0.85, 0.1, 0.1, alpha=0.10))
    c.translate(A4[0] / 2, A4[1] / 2); c.rotate(45); c.drawCentredString(0, 0, DRAFT_TXT); c.restoreState()
    c.saveState(); c.setFont("Sans", 7.5); c.setFillColor(colors.HexColor("#b00020"))
    c.drawString(18 * mm, 10 * mm, "Model generat automat – PROIECT. Nu are valoare juridică până la verificarea și validarea de către un avocat.")
    c.setFillColor(colors.grey); c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Pagina {doc.page}"); c.restoreState()

def _build(path, story, title):
    SimpleDocTemplate(path, pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=20 * mm, bottomMargin=20 * mm,
                      title=title, author="Platformă firme – prototip").build(story, onFirstPage=_page, onLaterPages=_page)

P = lambda t, s=BODY: Paragraph(t, s)
def b(t): return f"<b>{x(str(t))}</b>"
def fnum(v):
    v = float(v); return f"{v:,.0f}".replace(",", ".") if v == int(v) else f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def persoana(a):
    return (f"{b(a['nume'])}, cetățenie {x(a.get('cetatenie') or 'română')}, născut(ă) la data de {x(a.get('data_nasterii') or '—')} în {x(a.get('loc_nastere') or '—')}, "
            f"domiciliat(ă) în {x(a.get('domiciliu',''))}, identificat(ă) cu C.I. seria {x(a.get('ci_serie','').upper())} nr. {x(a.get('ci_numar',''))}, "
            f"eliberată de {x(a.get('ci_emitent') or '—')} la data de {x(a.get('ci_data') or '—')}, CNP {x(a.get('cnp',''))}")

def adresa(s):
    parts = [f"{s.get('localitate','')}", f"str. {s.get('strada','')} nr. {s.get('numar','')}"]
    for k, l in [("bloc", "bl."), ("scara", "sc."), ("etaj", "et."), ("ap", "ap.")]:
        if s.get(k): parts.append(f"{l} {s[k]}")
    parts.append(f"jud. {s.get('judet','')}")
    return ", ".join(parts)

def denumire(d): return d["denumire"].strip().upper().removesuffix(" SRL").removesuffix(" S.R.L.") + " S.R.L."

def act_constitutiv(d, path):
    den = denumire(d); asoc = d["asociati"]; cap = float(d["capital"]); vn = float(d["valoare_parte"]); n = round(cap / vn)
    unic = len(asoc) == 1
    st = [P("ACT CONSTITUTIV", H1), P(f"al societății {b(den)}", SUB)]
    st.append(P("<b>Capitolul I – Asociații</b>", H2))
    st.append(P(("Subsemnatul/Subsemnata, în calitate de asociat unic:" if unic else "Subsemnații:")))
    for i, a in enumerate(asoc, 1):
        st.append(P(f"{i}. {persoana(a)};"))
    st.append(P("am hotărât constituirea unei societăți cu răspundere limitată, în conformitate cu prevederile Legii societăților nr. 31/1990, republicată, cu modificările și completările ulterioare, și ale Legii nr. 265/2022 privind registrul comerțului, în următoarele condiții:"))
    st.append(P("<b>Capitolul II – Denumirea, forma juridică, sediul și durata</b>", H2))
    st.append(P(f"<b>Art. 1.</b> Denumirea societății este {b(den)}, conform dovezii de rezervare emise de Oficiul Registrului Comerțului. În toate actele și documentele emanând de la societate, denumirea va fi precedată sau urmată de cuvintele „societate cu răspundere limitată” sau de inițialele „S.R.L.”, de sediul social, numărul de ordine în registrul comerțului, codul unic de înregistrare și capitalul social."))
    st.append(P("<b>Art. 2.</b> Forma juridică a societății este societate cu răspundere limitată, persoană juridică română."))
    st.append(P(f"<b>Art. 3.</b> Sediul social al societății este în {b(adresa(d['sediu']))}. Sediul social poate fi schimbat prin hotărârea {'asociatului unic' if unic else 'adunării generale a asociaților'}. Societatea poate înființa sedii secundare (sucursale, puncte de lucru) în condițiile legii."))
    dur = "nelimitată" if d.get("durata") == "nelimitata" else f"de {int(d['durata_ani'])} ani"
    st.append(P(f"<b>Art. 4.</b> Durata de funcționare a societății este {b(dur)}, începând cu data înmatriculării în registrul comerțului."))
    st.append(P("<b>Capitolul III – Obiectul de activitate</b>", H2))
    st.append(P(f"<b>Art. 5.</b> Domeniul și activitatea principală, conform CAEN Rev. 3: {b(d['caen_principal'])}" + (f" – {x(d.get('caen_principal_desc',''))}" if d.get('caen_principal_desc') else "") + "."))
    sec = [c for c in d.get("caen_secundare", []) if c]
    st.append(P("Activitățile secundare: " + (", ".join(x(c) for c in sec) if sec else "nu se declară la constituire") + "."))
    st.append(P("<b>Capitolul IV – Capitalul social și părțile sociale</b>", H2))
    st.append(P(f"<b>Art. 6.</b> Capitalul social subscris și vărsat integral este de {b(fnum(cap) + ' lei')}, aport în numerar, divizat în {b(n)} părți sociale cu o valoare nominală de {b(fnum(vn) + ' lei')} fiecare, repartizate astfel:"))
    rows = [["Asociat", "Aport (lei)", "Nr. părți", "Cota (%)"]]
    for a in asoc:
        q = float(a["cota"]); np_ = round(n * q / 100)
        rows.append([a["nume"], fnum(np_ * vn), str(np_), f"{q:g}"])
    rows.append(["TOTAL", fnum(cap), str(n), "100"])
    t = Table(rows, colWidths=[75 * mm, 30 * mm, 25 * mm, 25 * mm])
    t.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "Serif", 9.5), ("FONT", (0, 0), (-1, 0), "Serif-B", 9.5), ("FONT", (0, -1), (-1, -1), "Serif-B", 9.5),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")), ("ALIGN", (1, 0), (-1, -1), "RIGHT")]))
    st += [t, Spacer(1, 6)]
    st.append(P("<b>Art. 7.</b> Participarea la beneficii și pierderi se face proporțional cu cota de participare la capitalul social. Părțile sociale pot fi transmise între asociați; transmiterea către persoane din afara societății este permisă numai dacă a fost aprobată de asociații reprezentând cel puțin trei pătrimi din capitalul social, potrivit art. 202 din Legea nr. 31/1990."))
    st.append(P("<b>Capitolul V – Conducerea și administrarea</b>", H2))
    st.append(P(f"<b>Art. 8.</b> {'Asociatul unic exercită atribuțiile adunării generale a asociaților.' if unic else 'Adunarea generală a asociaților decide asupra activității societății; hotărârile se iau prin votul asociaților reprezentând majoritatea absolută a asociaților și a părților sociale, cu excepția hotărârilor privind modificarea actului constitutiv, pentru care este necesar votul tuturor asociaților, dacă legea nu prevede altfel.'}"))
    adm = d["administratori"]
    st.append(P("<b>Art. 9.</b> Societatea este administrată de:"))
    for a in adm:
        st.append(P(f"– {persoana(a)}, numit(ă) administrator pe o durată {x(a.get('mandat') or 'nelimitată')}, cu puteri depline de reprezentare" + (", putând acționa separat" if len(adm) > 1 else "") + "."))
    st.append(P("Administratorul/administratorii au declarat pe propria răspundere că îndeplinesc condițiile prevăzute de art. 6 alin. (2) și art. 73<super>1</super> din Legea nr. 31/1990."))
    st.append(P("<b>Capitolul VI – Activitatea societății, dizolvarea și lichidarea</b>", H2))
    st.append(P("<b>Art. 10.</b> Exercițiul financiar începe la 1 ianuarie și se încheie la 31 decembrie al fiecărui an; primul exercițiu începe la data înmatriculării. Evidența contabilă și situațiile financiare se întocmesc potrivit legii."))
    st.append(P("<b>Art. 11.</b> Dizolvarea și lichidarea societății se fac în cazurile și cu procedura prevăzute de Legea nr. 31/1990."))
    st.append(P("<b>Art. 12.</b> Prevederile prezentului act constitutiv se completează cu dispozițiile Legii nr. 31/1990 și ale Codului civil."))
    st.append(P(f"Redactat și semnat în {len(asoc)+1} exemplare originale / în format electronic cu semnătură electronică calificată, astăzi, {date.today():%d.%m.%Y}."))
    st.append(Spacer(1, 10)); st.append(P("<b>Asociați:</b>"))
    for a in asoc: st.append(P(f"{x(a['nume'])} ............................................"))
    _build(path, st, "Act constitutiv " + den)

def declaratie(d, pers, roluri, path):
    den = denumire(d)
    st = [P("DECLARAȚIE PE PROPRIA RĂSPUNDERE", H1), P("conform art. 6 alin. (2) și art. 73<super>1</super> din Legea nr. 31/1990 și art. 82 din Legea nr. 265/2022", SUB)]
    st.append(P(f"Subsemnatul/Subsemnata {persoana(pers)}, în calitate de {b(' și '.join(roluri))} al/a societății {b(den)}, în curs de înmatriculare, cunoscând prevederile art. 326 din Codul penal privind falsul în declarații, declar pe propria răspundere că:"))
    items = [
        "îndeplinesc condițiile legale pentru a avea calitatea de " + " și ".join(roluri) + ", prevăzute de Legea nr. 31/1990;",
        "nu am fost condamnat(ă) definitiv pentru gestiune frauduloasă, abuz de încredere, fals, uz de fals, înșelăciune, delapidare, mărturie mincinoasă, dare sau luare de mită, pentru infracțiunile prevăzute de Legea nr. 129/2019 pentru prevenirea și combaterea spălării banilor și a finanțării terorismului, pentru infracțiunile prevăzute de Legea nr. 85/2014 privind procedurile de prevenire a insolvenței și de insolvență, pentru infracțiunile prevăzute de Legea nr. 241/2005 pentru prevenirea și combaterea evaziunii fiscale sau pentru alte infracțiuni care împiedică, potrivit legii, exercitarea acestei calități (art. 6 alin. (2) din Legea nr. 31/1990);",
        "nu sunt decăzut(ă) din dreptul de a fi administrator / nu mi s-a aplicat pedeapsa complementară a interzicerii dreptului de a exercita profesia sau activitatea în executarea căreia am săvârșit fapta;",
    ]
    if "administrator" in roluri:
        items.append("accept numirea în funcția de administrator și nu mă aflu în niciuna dintre situațiile de incompatibilitate prevăzute de lege; îmi asum îndeplinirea obligațiilor prevăzute de art. 73<super>1</super> și următoarele din Legea nr. 31/1990;")
    items.append("datele declarate sunt reale, complete și corespund actelor de identitate prezentate.")
    for i, t in enumerate(items, 1): st.append(P(f"{i}. {t}"))
    st.append(Spacer(1, 14))
    st.append(Table([[P(f"Data: {date.today():%d.%m.%Y}"), P("Semnătura: ...............................")]], colWidths=[80 * mm, 86 * mm]))
    _build(path, st, "Declaratie " + pers["nume"])

def specimen(d, a, path):
    den = denumire(d)
    st = [P("SPECIMEN DE SEMNĂTURĂ", H1), P(f"societatea {b(den)} – în curs de înmatriculare", SUB)]
    st.append(P(f"Subsemnatul/Subsemnata {persoana(a)}, în calitate de {b('administrator')} al societății {b(den)}, cu sediul social în {x(adresa(d['sediu']))}, depun prezentul specimen de semnătură, conform art. 82 și următoarele din Legea nr. 265/2022."))
    st.append(Spacer(1, 10))
    box = Table([["Semnătura 1", "Semnătura 2", "Semnătura 3"], ["", "", ""]], colWidths=[52 * mm] * 3, rowHeights=[8 * mm, 32 * mm])
    box.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "Serif", 9), ("GRID", (0, 0), (-1, -1), 0.6, colors.black), ("ALIGN", (0, 0), (-1, 0), "CENTER"), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7"))]))
    st += [box, Spacer(1, 12)]
    st.append(P("Notă: potrivit Legii nr. 265/2022, specimenul de semnătură poate fi dat olograf în fața funcționarului ORC / a notarului / avocatului care atestă identitatea, sau poate fi înlocuit de semnătura electronică calificată la depunerea online."))
    st.append(P(f"Data: {date.today():%d.%m.%Y}"))
    _build(path, st, "Specimen " + a["nume"])

def comodat(d, path):
    den = denumire(d); s = d["sediu"]; p = s["proprietar"]; adm = d["administratori"][0]
    st = [P("CONTRACT DE COMODAT", H1), P(f"nr. ____ din {date.today():%d.%m.%Y}", SUB)]
    st.append(P("<b>I. Părțile contractante</b>", H2))
    st.append(P(f"1.1. {b(p['nume'])}, domiciliat(ă) în {x(p.get('domiciliu') or '—')}, identificat(ă) cu C.I. seria {x((p.get('ci_serie') or '').upper())} nr. {x(p.get('ci_numar') or '')}, CNP {x(p.get('cnp',''))}, în calitate de {b('COMODANT')} (proprietar), și"))
    st.append(P(f"1.2. {b(den)}, societate în curs de înmatriculare, reprezentată de administrator {b(adm['nume'])}, CNP {x(adm['cnp'])}, în calitate de {b('COMODATAR')},"))
    st.append(P("au convenit încheierea prezentului contract de comodat, cu respectarea art. 2146–2157 din Codul civil, în următoarele condiții:"))
    st.append(P("<b>II. Obiectul contractului</b>", H2))
    st.append(P(f"2.1. Comodantul dă în folosință gratuită comodatarului imobilul situat în {b(adresa(s))}" + (f", înscris în cartea funciară nr. {x(s.get('carte_funciara'))}" if s.get('carte_funciara') else "") + ", cu destinația de <b>sediu social</b>" + (" și desfășurare de activitate" if s.get("activitate_la_sediu") else ", fără desfășurarea activității la sediu") + "."))
    st.append(P("2.2. Comodantul declară că este proprietarul imobilului și că acesta nu face obiectul vreunui litigiu care să împiedice folosința."))
    st.append(P("<b>III. Durata</b>", H2))
    st.append(P(f"3.1. Contractul se încheie pe o durată de {b(str(s.get('durata_comodat') or 5) + ' ani')}, începând cu data înmatriculării societății, și poate fi prelungit prin act adițional."))
    st.append(P("<b>IV. Obligațiile părților</b>", H2))
    st.append(P("4.1. Comodatarul se obligă să folosească bunul potrivit destinației, să îl păstreze în bune condiții și să îl restituie la încetarea contractului. 4.2. Comodantul se obligă să asigure folosința liniștită a bunului pe durata contractului. 4.3. Cheltuielile de folosință se suportă conform înțelegerii părților."))
    st.append(P("<b>V. Încetarea contractului</b>", H2))
    st.append(P("5.1. Contractul încetează la expirarea duratei, prin acordul părților, prin denunțare unilaterală cu un preaviz de 30 de zile sau în cazurile prevăzute de lege."))
    st.append(P("<b>VI. Dispoziții finale</b>", H2))
    st.append(P("6.1. Litigiile se soluționează pe cale amiabilă, iar în caz contrar de instanțele competente. Contractul a fost încheiat în 3 exemplare originale, câte unul pentru fiecare parte și unul pentru Oficiul Registrului Comerțului, sau în format electronic semnat cu semnătură electronică calificată."))
    st.append(Spacer(1, 14))
    st.append(Table([[P("<b>COMODANT</b><br/>" + x(p['nume']) + "<br/><br/>.........................."), P("<b>COMODATAR</b><br/>" + x(den) + "<br/>prin " + x(adm['nume']) + "<br/>..........................")]], colWidths=[83 * mm, 83 * mm]))
    _build(path, st, "Contract comodat")

def checklist(d, path):
    den = denumire(d)
    st = [P("CHECKLIST ȘI PAȘII URMĂTORI", H1), P(f"Dosar înființare {b(den)}", SUB)]
    st.append(P("<b>A. Documente generate de platformă (incluse în acest pachet)</b>", H2))
    for t in ["Act constitutiv (proiect)", "Declarații pe propria răspundere pentru fiecare asociat/administrator", "Specimen de semnătură pentru fiecare administrator", "Contract de comodat pentru sediul social"]:
        st.append(P("<font name=\"Sans\">☑</font> " + t))
    st.append(P("<b>B. Documente pe care trebuie să le furnizați</b>", H2))
    items = ["Copie după actul de identitate al fiecărui asociat și administrator (scan color, lizibil)",
             "Actul de proprietate al spațiului (contract de vânzare-cumpărare / certificat de moștenitor etc.) și extras de carte funciară, dacă este solicitat",
             "Copie după actul de identitate al proprietarului spațiului (comodant)",
             "Acordul asociației de proprietari / al vecinilor, dacă la sediu se desfășoară activitate într-un bloc de locuințe (după caz)",
             "Dovada rezervării denumirii (o obținem pe baza celor 3 variante propuse)",
             "Dovada vărsării capitalului social, dacă banca o solicită (după caz)",
             "Declarația privind beneficiarul real (Legea nr. 129/2019) – se completează în formularul ONRC",
             "Pentru cetățeni străini: pașaport, traduceri autorizate și, după caz, certificat de cazier fiscal"]
    for t in items: st.append(P("<font name=\"Sans\">☐</font> " + x(t)))
    st.append(P("<b>C. Pașii următori</b>", H2))
    steps = ["<b>Verificare juridică:</b> un avocat partener verifică datele și documentele generate (acestea sunt proiecte).",
             "<b>Semnătură electronică calificată:</b> toți asociații semnează actul constitutiv, iar administratorii semnează declarațiile și specimenul, olograf sau cu semnătură electronică calificată (art. 82 din Legea nr. 265/2022). Dacă nu aveți una, se poate emite la distanță printr-un furnizor acreditat, cu verificare video a identității.",
             "<b>Depunere online la ONRC:</b> dosarul se depune prin avocat, pe bază de împuternicire avocațială (art. 79 și 84 din Legea nr. 265/2022), sau de dvs., prin portalul ONRC, cu semnătură electronică calificată.",
             "<b>Taxe:</b> taxele ONRC și tariful de publicare în Monitorul Oficial se achită conform notei de calcul emise după admiterea cererii.",
             "<b>Soluționare:</b> registratorul soluționează cererea, de regulă, într-o zi lucrătoare. Primiți electronic certificatul de înregistrare (CUI) și încheierea.",
             "<b>După înmatriculare:</b> deschideți contul bancar, contractați un contabil, înregistrați-vă în SPV/e-Factura și, după caz, în scopuri de TVA."]
    for i, t in enumerate(steps, 1): st.append(P(f"{i}. {t}"))
    st.append(Spacer(1, 8))
    st.append(P("<font color='#b00020'><b>Important:</b> toate documentele sunt modele generate automat (PROIECT) și trebuie verificate și validate de un avocat înainte de semnare și depunere. Prototipul nu transmite nimic la ONRC și nu procesează plăți.</font>"))
    _build(path, st, "Checklist")

def genereaza(d, outdir):
    os.makedirs(outdir, exist_ok=True)
    files = []
    def add(name, fn, *args):
        p = os.path.join(outdir, name); fn(*args, p); files.append(name)
    add("01_act_constitutiv.pdf", act_constitutiv, d)
    pers = {}
    for a in d["asociati"]: pers.setdefault(a["cnp"], (a, []))[1].append("asociat")
    for a in d["administratori"]: pers.setdefault(a["cnp"], (a, []))[1].append("administrator")
    for i, (a, r) in enumerate(pers.values(), 1):
        add(f"02_declaratie_{i}_{_slug(a['nume'])}.pdf", declaratie, d, a, r)
    for i, a in enumerate(d["administratori"], 1):
        add(f"03_specimen_semnatura_{i}_{_slug(a['nume'])}.pdf", specimen, d, a)
    add("04_contract_comodat_sediu.pdf", comodat, d)
    add("05_checklist_pasi_urmatori.pdf", checklist, d)
    return files

def _slug(s):
    import unicodedata, re
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:30]
