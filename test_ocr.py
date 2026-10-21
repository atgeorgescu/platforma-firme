import difflib
import json, sys, time
from ci_ocr import extract
cases = json.load(open(sys.argv[1]))
FIELDS = ["nume", "cnp", "ci_serie", "ci_numar", "data_nasterii", "sex", "cetatenie", "ci_valabilitate", "ci_emitent", "domiciliu"]
import unicodedata
n = lambda s: unicodedata.normalize("NFKD", (s or "")).encode("ascii", "ignore").decode().lower().replace(" ", "")
tot = {}; ok = {}; ex = {}; sim = {}
for c in cases:
    t = time.time(); r = extract([open(f, "rb").read() for f in c["files"]]); dt = time.time() - t
    miss = []
    for k in FIELDS:
        if k == "domiciliu" and c["kind"] == "cei": continue
        tot[k] = tot.get(k, 0) + 1
        good = n(r.get(k)) == n(c["truth"][k]); exact = (r.get(k) or "").lower() == c["truth"][k].lower()
        sim.setdefault(k, []).append(difflib.SequenceMatcher(None, n(r.get(k)), n(c['truth'][k])).ratio()); ok[k] = ok.get(k, 0) + good; ex[k] = ex.get(k, 0) + exact
        if not good: miss.append(f"{k}: '{r.get(k)}' ≠ '{c['truth'][k]}'")
    print(f"{c['kind']:5} {c['variant']:4} {dt:4.1f}s MRZ={r.get('mrz',{}).get('verificari')} {'OK' if not miss else miss}")
print("\nCâmp: corect (fără diacritice) / exact (cu diacritice)")
for k in FIELDS: print(f"  {k:16} {ok[k]}/{tot[k]}   {ex[k]}/{tot[k]}   similaritate medie {100*sum(sim[k])/len(sim[k]):.0f}%")
import difflib
print("TOTAL", sum(ok.values()), "/", sum(tot.values()), " exact", sum(ex.values()))
