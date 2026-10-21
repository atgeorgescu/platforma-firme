"""Rulează OCR-ul într-un proces separat, de scurtă durată: memoria (~300 MB) se eliberează după fiecare scanare,
iar imaginile circulă doar prin pipe (nu se scriu pe disc)."""
import sys, json, base64, subprocess, fcntl, os, tempfile

LOCK = os.path.join(tempfile.gettempdir(), "ocr.lock")

def run(images, timeout=170):
    payload = json.dumps([base64.b64encode(b).decode() for b in images]).encode()
    with open(LOCK, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)  # o singură scanare odată (limită RAM pe planul gratuit)
        p = subprocess.run([sys.executable, os.path.abspath(__file__)], input=payload, capture_output=True, timeout=timeout,
                           cwd=os.path.dirname(os.path.abspath(__file__)), env={**os.environ, "OMP_NUM_THREADS": "1"})
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode(errors="ignore")[-500:])
    return json.loads(p.stdout.decode().strip().splitlines()[-1])

if __name__ == "__main__":
    imgs = [base64.b64decode(x) for x in json.loads(sys.stdin.buffer.read())]
    from ci_ocr import extract
    r = extract(imgs); r.pop("linii_ocr", None)
    sys.stdout.write("\n" + json.dumps(r, ensure_ascii=False) + "\n")
