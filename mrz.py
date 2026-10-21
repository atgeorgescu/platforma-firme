"""Parsare MRZ pentru cartea de identitate românească (CI veche TD2 2x36, CEI TD1 3x30)."""
import re
from datetime import date

def _val(c):
    if c.isdigit(): return int(c)
    if c.isalpha(): return ord(c) - 55
    return 0

def check_digit(s):
    return str(sum(_val(c) * w for c, w in zip(s, [7, 3, 1] * 20)) % 10)

def _date(yymmdd, future=False):
    try:
        y, m, d = int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:6])
    except ValueError:
        return None
    cur = date.today().year % 100
    y += 2000 if (future or y <= cur) else 1900
    try:
        return date(y, m, d)
    except ValueError:
        return None

def _names(s):
    s = s.strip("<")
    if "<<" in s:
        sur, given = s.split("<<", 1)
    else:
        sur, _, given = s.partition("<")
    return sur.replace("<", " ").strip(), given.replace("<", " ").strip().replace(" ", "-") if given.count("<") == 1 and "<<" not in given else given.replace("<", " ").strip()

# corecții OCR în câmpuri numerice
_DIG = str.maketrans({"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "Z": "2", "S": "5", "B": "8", "G": "6", "T": "7"})
_ALPHA = str.maketrans({"0": "O", "1": "I", "2": "Z", "5": "S", "8": "B", "6": "G"})
dig = lambda s: s.translate(_DIG)
alp = lambda s: s.translate(_ALPHA)

def clean_line(l):
    l = l.upper().replace(" ", "").replace("«", "<<").replace("‹", "<").replace("(", "<").replace("{", "<").replace("[", "<")
    return re.sub(r"[^A-Z0-9<]", "", l)

def find_mrz_all(lines):
    """Toate interpretările posibile (TD1 și TD2) – se alege cea cu cifre de control valide."""
    cand = [clean_line(l) for l in lines]
    cand = [re.sub(r"^[IT1L][DO0]R[O0]U", "IDROU", c) for c in cand if len(c) >= 10]
    out = []
    for i, c in enumerate(cand):
        if not c.startswith("IDROU"): continue
        nxt = cand[i + 1:i + 3] + ["", ""]
        out.append(("TD1", [_pad(c, 30), _pad(nxt[0], 30), _pad(nxt[1], 30)]))
        out.append(("TD2", [_pad(c, 36), _pad(nxt[0], 36)]))
    return out

def find_mrz(lines):
    """Primește liniile OCR și întoarce (tip, [linii])."""
    cand = [clean_line(l) for l in lines]
    cand = [re.sub(r"^[IT1L][DO0]R[O0]U", "IDROU", c) for c in cand if len(c) >= 10]
    for i, c in enumerate(cand):
        if not c.startswith("IDROU"): continue
        nxt = cand[i + 1:i + 3]
        if not nxt: continue
        n0 = dig(nxt[0][:7])
        if False and re.match(r"^\d{7}[MF<]", n0 + nxt[0][7:8]) or (len(c) <= 31 and len(nxt) >= 2 and len(nxt[0]) <= 31):
            if len(nxt) < 2: nxt.append("")
            return "TD1", [_pad(c, 30), _pad(nxt[0], 30), _pad(nxt[1], 30)]
        return "TD2", [_pad(c, 36), _pad(nxt[0], 36)]
    return None, []

def _pad(s, n):
    return (s + "<" * n)[:n]

def parse(kind, L):
    r = {"mrz_tip": kind, "checks": {}}
    if kind == "TD2":
        l1, l2 = L
        r["nume_mrz"], r["prenume_mrz"] = _names(l1[5:])
        doc = l2[0:9]; serie = alp(doc[:2]); nr = dig(doc[2:8])
        r["ci_serie"], r["ci_numar"] = serie, nr
        r["checks"]["document"] = check_digit(serie + nr + doc[8]) == dig(l2[9])
        r["cetatenie_cod"] = alp(l2[10:13])
        dob = dig(l2[13:19]); r["checks"]["data_nasterii"] = check_digit(dob) == dig(l2[19])
        r["sex"] = {"M": "M", "F": "F"}.get(l2[20], "")
        exp = dig(l2[21:27]); r["checks"]["expirare"] = check_digit(exp) == dig(l2[27])
        opt = dig(l2[28:35])
        r["checks"]["compus"] = check_digit(serie + nr + doc[8] + dig(l2[9]) + dob + dig(l2[19]) + exp + dig(l2[27]) + opt) == dig(l2[35])
        if re.fullmatch(r"\d{7}", opt):
            r["cnp_mrz"] = opt[0] + dob + opt[1:]
    else:
        l1, l2, l3 = L
        doc = l1[5:14]; serie = alp(doc[:2]); nr = dig(doc[2:8])
        r["ci_serie"], r["ci_numar"] = serie, nr
        r["checks"]["document"] = check_digit(doc) == dig(l1[14]) if doc[2:8].isdigit() or dig(doc[2:8]).isdigit() else False
        r["checks"]["document"] = check_digit(serie + nr + doc[8]) == dig(l1[14])
        opt1 = l1[15:30]
        m = re.search(r"\d{13}", dig(opt1))
        if m: r["cnp_mrz"] = m.group(0)
        dob = dig(l2[0:6]); r["checks"]["data_nasterii"] = check_digit(dob) == dig(l2[6])
        r["sex"] = {"M": "M", "F": "F"}.get(l2[7], "")
        exp = dig(l2[8:14]); r["checks"]["expirare"] = check_digit(exp) == dig(l2[14])
        r["cetatenie_cod"] = alp(l2[15:18])
        comp = l1[5:30] + l2[0:7] + l2[8:15] + l2[18:29]
        comp = serie + nr + doc[8] + dig(l1[14]) + opt1 + dob + dig(l2[6]) + exp + dig(l2[14]) + l2[18:29]
        r["checks"]["compus"] = check_digit(comp) == dig(l2[29])
        r["nume_mrz"], r["prenume_mrz"] = _names(l3)
    d = _date(dob); e = _date(exp, future=True)
    r["data_nasterii"] = d.strftime("%d.%m.%Y") if d else ""
    r["ci_valabilitate"] = e.strftime("%d.%m.%Y") if e else ""
    r["cetatenie"] = "română" if r.get("cetatenie_cod") == "ROU" else r.get("cetatenie_cod", "")
    return r

def make_td2(nume, prenume, serie, nr, dob, sex, exp, cnp):
    l1 = _pad("IDROU" + nume.upper().replace(" ", "<").replace("-", "<") + "<<" + prenume.upper().replace(" ", "<").replace("-", "<"), 36)
    doc = serie + nr + "<"; c1 = check_digit(doc); c2 = check_digit(dob); c3 = check_digit(exp); opt = cnp[0] + cnp[7:]
    comp = check_digit(doc + c1 + dob + c2 + exp + c3 + opt)
    return [l1, doc + c1 + "ROU" + dob + c2 + sex + exp + c3 + opt + comp]

def make_td1(nume, prenume, serie, nr, dob, sex, exp, cnp):
    doc = serie + nr + "<"; c1 = check_digit(doc); opt1 = _pad(cnp, 15)
    l1 = "IDROU" + doc + c1 + opt1
    c2 = check_digit(dob); c3 = check_digit(exp); opt2 = "<" * 11
    comp = check_digit(doc + c1 + opt1 + dob + c2 + exp + c3 + opt2)
    l2 = dob + c2 + sex + exp + c3 + "ROU" + opt2 + comp
    l3 = _pad(nume.upper().replace(" ", "<").replace("-", "<") + "<<" + prenume.upper().replace(" ", "<").replace("-", "<"), 30)
    return [l1, l2, l3]
