"""Recunoaștere CI românească: OCR (RapidOCR/ONNX, rulează local, fără servicii externe) + MRZ cu cifre de control."""
import re, io, unicodedata
import numpy as np
from PIL import Image, ImageOps
import mrz
from validators import cnp_valid

_engine = None
import os
MAXS = int(os.environ.get('OCR_MAX_SIDE', '1280'))
def engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
    return _engine

DIACR = {"Stefan": "Ștefan", "Razvan": "Răzvan", "Madalina": "Mădălina", "Stefania": "Ștefania", "Catalin": "Cătălin", "Catalina": "Cătălina", "Andreea": "Andreea", "Bogdan": "Bogdan", "Raluca": "Raluca", "Gratiela": "Grațiela", "Florentina": "Florentina", "Aurelia": "Aurelia", "Ionut": "Ionuț", "Costica": "Costică", "Mihaita": "Mihăiță", "Petrica": "Petrică", "Viorica": "Viorica", "Lacramioara": "Lăcrămioara", "Doina": "Doina", "Calin": "Călin", "Radita": "Rădița", "Bianca": "Bianca", "Tanase": "Tănase", "Stanescu": "Stănescu", "Taranu": "Țăranu", "Stoica": "Stoica", "Dragan": "Drăgan", "Draghici": "Drăghici", "Sandulescu": "Săndulescu", "Patrascu": "Pătrașcu", "Barbulescu": "Bărbulescu", "Tudosa": "Tudosă", "Anghelache": "Anghelache", "Neagu": "Neagu", "Raducanu": "Răducanu", "Badea": "Badea", "Simion": "Simion", "Paun": "Păun", "Costache": "Costache", "Matei": "Matei", "Ilie": "Ilie", "Dinca": "Dincă", "Popa": "Popa", "Raileanu": "Răileanu", "Ploiesti": "Ploiești", "Bucuresti": "București", "Brasov": "Brașov", "Constanta": "Constanța", "Iasi": "Iași", "Pitesti": "Pitești",
         "Campina": "Câmpina", "Busteni": "Bușteni", "Timisoara": "Timișoara", "Targoviste": "Târgoviște", "Galati": "Galați", "Floresti": "Florești",
         "Marasesti": "Mărășești", "Valeni": "Văleni", "Vălenii": "Vălenii", "Baicoi": "Băicoi", "Mizil": "Mizil", "Urlati": "Urlați", "Breaza": "Breaza",
         "Comarnic": "Comarnic", "Buzau": "Buzău", "Ramnicu": "Râmnicu", "Valcea": "Vâlcea", "Targu": "Târgu", "Mures": "Mureș", "Bacau": "Bacău",
         "Suceava": "Suceava", "Botosani": "Botoșani", "Sfantu": "Sfântu", "Calarasi": "Călărași", "Slobozia": "Slobozia", "Alexandria": "Alexandria",
         "Lunga": "Lungă", "Romana": "Română", "Orş": "Orș", "Ors": "Orș", "Strada": "Strada", "Soseaua": "Șoseaua", "Sos": "Șos", "Bd": "Bd", "Sec": "Sec"}

import difflib
_KEYS = list(DIACR.keys())
def _fix_word(w, fuzzy):
    if w in DIACR: return DIACR[w]
    if fuzzy and len(w) >= 6:
        c = [k for k in difflib.get_close_matches(w, _KEYS, n=3, cutoff=0.85) if abs(len(k) - len(w)) <= 1]
        if c: return DIACR[c[0]]
    return w
def _diacr(s, fuzzy=True):
    return re.sub(r"[A-Za-z]+", lambda m: _fix_word(m.group(0), fuzzy), s)

def _space_addr(s):
    s = re.sub(r"(?<=\.)l(?=[a-z])", "I", s)
    s = re.sub(r"([a-zăâîșț])([A-ZĂÂÎȘȚ])", r"\1 \2", s)
    s = re.sub(r"(Jud\.[A-Z]{1,2})(?=[A-Z][a-z])", r"\1 ", s)
    s = re.sub(r"(?<=[a-zăâîșțA-Z0-9])(Mun\.|Orș\.|Ors\.|Or\.|Com\.|Sat\.|Sec\.|Str\.|Bd\.|Sos\.|Șos\.|Cal\.|Al\.|Piata|nr\.|bl\.|sc\.|et\.|ap\.)", r" \1", s)
    s = re.sub(r"(Mun\.|Orș\.|Ors\.|Com\.|Str\.|Bd\.|nr\.|bl\.|sc\.|et\.|ap\.)\s*", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()

def _title(s):
    return "-".join(" ".join(w.capitalize() for w in part.split()) for part in s.split("-"))

def _prep(data):
    im = Image.open(io.BytesIO(data)); im = ImageOps.exif_transpose(im).convert("RGB")
    if max(im.size) > MAXS:
        im.thumbnail((MAXS, MAXS))
    elif max(im.size) < MAXS:
        k = MAXS / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    return np.array(im)

def _sorted(res):
    res.sort(key=lambda r: (round(min(p[1] for p in r[0]) / 12), min(p[0] for p in r[0])))
    return res

def _mrz_count(lines):
    return sum(1 for l in lines if l.count("<") >= 2 or re.match(r"^[I1][DO0]R[O0]U", l.replace(" ", "")))

def ocr_lines(data):
    img = _prep(data)
    res, _ = engine()(img)
    if not res: return [], []
    res = _sorted(res); lines = [r[1] for r in res]
    # A doua trecere pe zona MRZ (detectorul sare uneori rânduri): decupăm de la primul rând MRZ în jos și mărim 2x
    first = next((r for r in res if re.match(r"^[I1][DO0]R[O0]U", r[1].replace(" ", ""))), None)
    if first is not None:
        ys = [p[1] for p in first[0]]; h = max(ys) - min(ys)
        y0 = max(0, int(min(ys) - h * 0.6)); y1 = min(img.shape[0], int(max(ys) + h * 4.2))
        xs = [p[0] for p in first[0]]
        x0 = max(0, int(min(xs) - h)); x1 = min(img.shape[1], int(max(xs) + h * 3))
        crop = ImageOps.autocontrast(Image.fromarray(img[y0:y1, x0:x1]).convert("L"), cutoff=1)
        g = np.array(crop).astype(float)
        dark = (g < min(70, g.mean() - g.std())).sum(axis=1)
        thr = max(3, dark.max() * 0.15); rows = dark > thr
        bands = []; st = None
        for i, v in enumerate(list(rows) + [False]):
            if v and st is None: st = i
            if not v and st is not None:
                if h * 0.4 <= i - st <= h * 2: bands.append((st, i))
                st = None
        l2 = []
        for (b0, b1) in bands[:3]:
            pad = int((b1 - b0) * 0.25)
            strip = crop.crop((0, max(0, b0 - pad), crop.width, min(crop.height, b1 + pad)))
            strip = strip.resize((int(strip.width * 48 / strip.height), 48), Image.LANCZOS).convert("RGB")
            best_t, best_s = None, -1
            for H, rot in ((48, 0), (40, 0), (32, 0), (48, 180)):
                st2 = strip.resize((int(strip.width * H / 48), H), Image.LANCZOS)
                if rot: st2 = st2.rotate(rot)
                rr, _ = engine()(np.array(st2), use_det=False, use_cls=False, use_rec=True)
                if not rr: continue
                t = rr[0][1] if len(rr[0]) > 2 else rr[0][0]
                try: sc = float(rr[0][-1])
                except (TypeError, ValueError): sc = 0
                if ">" in t: sc -= 0.5
                sc += 0.01 * len(mrz.clean_line(t))
                if sc > best_s: best_t, best_s = t, sc
            if best_t: l2.append(best_t)
        l2 = [l for l in l2 if len(mrz.clean_line(l)) >= 25]
        if len(l2) >= 2:
            return lines, l2
    return lines, []

def _norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()

def extract(images):
    """images: listă de bytes (față și/sau verso). Imaginile nu sunt salvate pe disc."""
    lines = []; alts = []
    for b in images:
        l, a = ocr_lines(b); lines += l
        if a: alts.append(a)
    fix = lambda ls: [re.sub(r"^(1DROU|IOROU|IDR0U|1DR0U|IOR0U)", "IDROU", mrz.clean_line(l)) if ("<" in l or re.match(r"^[I1][DO0]R[O0]U", l.replace(" ", ""))) else l for l in ls]
    out = {"avertismente": [], "linii_ocr": lines}
    m = {}; kind = None; best = -1
    for cand in [fix(lines)] + [fix(a) for a in alts]:
        for k, L in mrz.find_mrz_all(cand):
            try: pm = mrz.parse(k, L)
            except Exception: continue
            sc = sum(pm["checks"].values())
            if sc > best: best, m, kind = sc, pm, k; mL = L
        if best == 4: break
    if kind and best <= 1:
        out["avertismente"].append("MRZ citit, dar cifrele de control nu se verifică – datele din MRZ au fost ignorate.")
        m = {}; kind = None
    if kind:
        L = mL; out["mrz"] = {"tip": "CI veche (TD2)" if kind == "TD2" else "CEI nouă (TD1)", "verificari": m["checks"], "linii": L}
        bad = [k for k, v in m["checks"].items() if not v]
        if bad: out["avertismente"].append("Cifre de control MRZ invalide pentru: " + ", ".join(bad) + " – verificați manual.")
    else:
        out["avertismente"].append("Zona MRZ (rândurile cu <<<) nu a fost găsită; încărcați o poză clară, inclusiv verso pentru CEI.")
    text = "\n".join(lines); low = [_norm(l) for l in lines]
    # CNP din zona vizuală
    cnps = [c for c in re.findall(r"(?<!\d)([1-9]\d{12})(?!\d)", re.sub(r"(?<=\d)[ ](?=\d)", "", text)) if cnp_valid(c)]
    cnp_v = cnps[0] if cnps else ""
    cnp_m = m.get("cnp_mrz", "")
    if cnp_m and not cnp_valid(cnp_m): cnp_m = ""
    out["cnp"] = cnp_v or cnp_m
    if cnp_v and cnp_m and cnp_v[0] + cnp_v[7:] != cnp_m[0] + cnp_m[7:] and cnp_v != cnp_m:
        out["avertismente"].append("CNP-ul din zona vizuală diferă de cel din MRZ.")
    # Validare CNP vs data nașterii / sex din MRZ
    if out["cnp"] and m.get("data_nasterii"):
        c = out["cnp"]; dn = f"{c[5:7]}.{c[3:5]}"
        if m["data_nasterii"][:5] != dn or m["data_nasterii"][-2:] != c[1:3]:
            out["avertismente"].append("Data nașterii din CNP nu corespunde cu MRZ.")
        sx = "M" if c[0] in "13579" else "F"
        if m.get("sex") and m["sex"] != sx: out["avertismente"].append("Sexul din CNP nu corespunde cu MRZ.")
        out["cnp_confirmat_mrz"] = not any("CNP" in a for a in out["avertismente"])
    # Serie / număr
    out["ci_serie"] = m.get("ci_serie", ""); out["ci_numar"] = m.get("ci_numar", "")
    sm = re.search(r"SERIA\s*([A-Z]{2})\s*N[RT]\.?\s*(\d{6})", text.upper().replace(" ", "").replace("SERIA", "SERIA "))
    if sm and not out["ci_serie"]: out["ci_serie"], out["ci_numar"] = sm.group(1), sm.group(2)
    # Nume
    def after(label_words, stop=1):
        for i, l in enumerate(low):
            if any(w in l.replace(" ", "") for w in label_words) and "/" in lines[i]:
                vals = [lines[j] for j in range(i + 1, min(i + 4, len(lines))) if "/" not in lines[j] or re.search(r"\d", lines[j])]
                return vals[:stop]
        return []
    nume = mrz.alp(m.get("nume_mrz", "")); pren = mrz.alp(m.get("prenume_mrz", ""))
    v = after(["nume/nom", "nume/last"])
    if v and re.fullmatch(r"[A-ZĂÂÎȘȚŞŢ\- ]{2,}", v[0].strip()) and (not nume or difflib.SequenceMatcher(None, _norm(v[0]), _norm(nume)).ratio() > 0.6): nume = v[0]
    v = after(["prenume/"])
    if v and re.fullmatch(r"[A-ZĂÂÎȘȚŞŢ\- ]{2,}", v[0].strip()) and (not pren or difflib.SequenceMatcher(None, _norm(v[0]), _norm(pren)).ratio() > 0.6): pren = v[0]
    if not v and kind == "TD2" and re.search(r"K{2,}", pren): pren = re.sub(r"K+$", "", pren)
    out["nume_familie"] = _diacr(_title(nume), False); out["prenume"] = _diacr(_title(pren), False)
    out["nume"] = (out["nume_familie"] + " " + out["prenume"]).strip()
    out["sex"] = m.get("sex", ""); out["data_nasterii"] = m.get("data_nasterii", ""); out["cetatenie"] = m.get("cetatenie", "") or ("română" if "ROU" in text.upper() else "")
    # Loc naștere
    v = after(["locnastere", "loculnasterii", "locnaster"])
    out["loc_nastere"] = _diacr(_space_addr(v[0])) if v else ""
    # Domiciliu (doar CI veche – CEI nu are domiciliul tipărit)
    out["domiciliu"] = ""
    for i, l in enumerate(low):
        if "domiciliu" in l.replace(" ", ""):
            parts = []
            for j in range(i + 1, min(i + 6, len(lines))):
                lj = low[j].replace(" ", "")
                if any(k in lj for k in ("emis", "valabil", "delivr", "issued")) or re.search(r"\d{2}\.\d{2}\.\d{2}", lines[j]) or lines[j].upper().startswith("SPC"): continue
                if "<" in lines[j]: break
                if re.search(r"(jud|mun|str|bd|com|sat|sec|nr|bl|ap|or[sș])\.", lj): parts.append(lines[j])
            out["domiciliu"] = _diacr(_space_addr(" ".join(parts)))
            break
    is_addr = lambda l: bool(re.search(r"(jud|mun|str|bd|com|sat|sec|or[sș])\.", _norm(l).replace(" ", "")))
    if not out["domiciliu"] and out.get("mrz", {}).get("tip", "").startswith("CI veche"):
        addr = [i for i, l in enumerate(lines) if is_addr(l) and "<" not in l and "/" not in l]
        if len(addr) >= 2:
            if not out["loc_nastere"]: out["loc_nastere"] = _diacr(_space_addr(lines[addr[0]]))
            out["domiciliu"] = _diacr(_space_addr(" ".join(lines[i] for i in addr[1:3])))
    if not out["domiciliu"]:
        out["avertismente"].append("Domiciliul nu a fost găsit (CEI nouă nu are adresa tipărită – completați din certificatul de atestare a domiciliului).")
    # Emitent
    em = next((l for l in lines if re.match(r"^\s*(SPC|S\.P\.C|POL|DEPABD|DGEP)", l.upper())), "")
    em = re.sub(r"^(SPCLEP|SPCJEP|SPCEP)(?=\S)", r"\1 ", em.strip())
    em = re.sub(r"^SPC\w{1,4}(?=[A-Z][a-z])", "SPCLEP ", em) if re.match(r"^SPC\w{1,4}[A-Z][a-z]", em) else em
    out["ci_emitent"] = _diacr(em)
    # Valabilitate
    vm = re.search(r"(\d{2}\.\d{2}\.\d{2,4})\s*-\s*(\d{2}\.\d{2}\.\d{4})", text)
    if vm:
        e = vm.group(1)
        if len(e) == 8: e = e[:6] + "20" + e[6:]
        out["ci_data"] = e; out["ci_valabilitate"] = vm.group(2)
    else:
        out["ci_data"] = ""; out["ci_valabilitate"] = m.get("ci_valabilitate", "")
    if m.get("ci_valabilitate") and out["ci_valabilitate"] and m["ci_valabilitate"] != out["ci_valabilitate"]:
        out["avertismente"].append("Data expirării din zona vizuală diferă de MRZ.")
    # Completări din CNP când MRZ lipsește
    c = out.get("cnp")
    if c and cnp_valid(c):
        sec = {"1": 1900, "2": 1900, "3": 1800, "4": 1800, "5": 2000, "6": 2000}.get(c[0], 1900)
        dn = f"{c[5:7]}.{c[3:5]}.{sec + int(c[1:3])}"
        if not out.get("data_nasterii"): out["data_nasterii"] = dn
        if not out.get("sex"): out["sex"] = "M" if c[0] in "1357" else "F"
    if not re.fullmatch(r"[a-zăâîșțA-Z]+", out.get("cetatenie") or ""):
        out["cetatenie"] = "română" if re.search(r"R[O0]U|Rom[aâ]n", text) else ""
    if not out.get("ci_valabilitate"):
        dm = re.findall(r"\b(\d{2}\.\d{2}\.20\d{2})\b", text)
        fut = [d for d in dm if int(d[-4:]) >= 2024]
        if fut: out["ci_valabilitate"] = fut[-1]
    out["tip_document"] = out.get("mrz", {}).get("tip", "necunoscut")
    return out
