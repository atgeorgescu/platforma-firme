import re
from datetime import date

CAPITAL_MINIM = 500  # lei, SRL nou-înființat – art. VI alin. (2) Legea 239/2025 (în vigoare 18.12.2025)

def cnp_valid(cnp: str) -> bool:
    if not re.fullmatch(r"\d{13}", cnp or ""):
        return False
    w = "279146358279"
    s = sum(int(a) * int(b) for a, b in zip(cnp[:12], w)) % 11
    c = 1 if s == 10 else s
    if c != int(cnp[12]):
        return False
    sx = int(cnp[0]); yy = int(cnp[1:3]); mm = int(cnp[3:5]); dd = int(cnp[5:7])
    if sx == 0:
        return False
    sec = {1: 1900, 2: 1900, 3: 1800, 4: 1800, 5: 2000, 6: 2000, 7: 1900, 8: 1900, 9: 1900}[sx]
    try:
        date(sec + yy, mm, dd)
    except ValueError:
        return False
    return True

def caen_valid(c):
    return bool(re.fullmatch(r"\d{4}", (c or "").strip()))

def validate(d):
    e = []
    req = lambda v: bool(str(v or "").strip())
    if not req(d.get("denumire")): e.append("Denumirea principală este obligatorie.")
    alts = [a for a in d.get("alternative", []) if req(a)]
    if len(alts) < 2: e.append("Introduceți două denumiri alternative.")
    s = d.get("sediu", {})
    for k, n in [("localitate", "localitatea"), ("judet", "județul"), ("strada", "strada"), ("numar", "numărul")]:
        if not req(s.get(k)): e.append(f"Sediu: lipsește {n}.")
    p = s.get("proprietar", {})
    if not req(p.get("nume")): e.append("Sediu: numele proprietarului este obligatoriu.")
    if not cnp_valid(p.get("cnp", "")): e.append("Sediu: CNP-ul proprietarului nu este valid.")
    asoc = d.get("asociati", [])
    if not asoc: e.append("Adăugați cel puțin un asociat.")
    total = 0.0
    for i, a in enumerate(asoc, 1):
        if not req(a.get("nume")): e.append(f"Asociatul {i}: numele este obligatoriu.")
        if not cnp_valid(a.get("cnp", "")): e.append(f"Asociatul {i}: CNP invalid (cifră de control sau dată greșită).")
        if not re.fullmatch(r"[A-Z]{2}", (a.get("ci_serie") or "").upper()): e.append(f"Asociatul {i}: seria CI trebuie să aibă 2 litere.")
        if not re.fullmatch(r"\d{6}", a.get("ci_numar") or ""): e.append(f"Asociatul {i}: numărul CI trebuie să aibă 6 cifre.")
        if not req(a.get("domiciliu")): e.append(f"Asociatul {i}: domiciliul este obligatoriu.")
        try:
            q = float(a.get("cota", 0))
            if q <= 0: raise ValueError
            total += q
        except (TypeError, ValueError):
            e.append(f"Asociatul {i}: cota trebuie să fie un număr pozitiv.")
    if asoc and abs(total - 100) > 0.001: e.append(f"Suma cotelor este {total:g}%, trebuie să fie 100%.")
    adm = d.get("administratori", [])
    if not adm: e.append("Desemnați cel puțin un administrator.")
    for i, a in enumerate(adm, 1):
        if not req(a.get("nume")): e.append(f"Administratorul {i}: numele este obligatoriu.")
        if not cnp_valid(a.get("cnp", "")): e.append(f"Administratorul {i}: CNP invalid.")
    try:
        cap = float(d.get("capital", 0)); vn = float(d.get("valoare_parte", 0))
        if cap < CAPITAL_MINIM: e.append(f"Capitalul social minim pentru un SRL nou este {CAPITAL_MINIM} lei (Legea 239/2025).")
        if vn < 1: e.append("Valoarea unei părți sociale trebuie să fie de cel puțin 1 leu.")
        elif abs(cap / vn - round(cap / vn)) > 1e-9: e.append("Capitalul trebuie să se împartă exact la valoarea unei părți sociale.")
        elif asoc and abs(total - 100) <= 0.001:
            n = round(cap / vn)
            for i, a in enumerate(asoc, 1):
                x = n * float(a.get("cota", 0)) / 100
                if abs(x - round(x)) > 1e-6: e.append(f"Asociatul {i}: cota de {a.get('cota')}% nu corespunde unui număr întreg de părți sociale ({n} părți).")
    except (TypeError, ValueError):
        e.append("Capitalul și valoarea părții sociale trebuie să fie numere.")
    if not caen_valid(d.get("caen_principal")): e.append("Codul CAEN principal trebuie să aibă 4 cifre.")
    for c in d.get("caen_secundare", []):
        if c and not caen_valid(c): e.append(f"Cod CAEN secundar invalid: {c}.")
    dur = d.get("durata", "nelimitata")
    if dur != "nelimitata":
        try:
            if int(d.get("durata_ani", 0)) < 1: raise ValueError
        except (TypeError, ValueError):
            e.append("Durata limitată trebuie exprimată în ani (minim 1).")
    return e
