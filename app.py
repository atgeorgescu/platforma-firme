import os, uuid, io, zipfile, tempfile, shutil, time
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file, abort
from validators import validate, CAPITAL_MINIM
from pdfgen import genereaza

app = Flask(__name__)
OUT = os.path.join(tempfile.gettempdir(), "dosare")
os.makedirs(OUT, exist_ok=True)

def cleanup(max_age=3600):
    now = time.time()
    for d in os.listdir(OUT):
        p = os.path.join(OUT, d)
        if os.path.isdir(p) and now - os.path.getmtime(p) > max_age:
            shutil.rmtree(p, ignore_errors=True)

@app.get("/")
def index():
    return render_template("index.html", capital_minim=CAPITAL_MINIM)

@app.post("/api/genereaza")
def api_gen():
    cleanup()
    d = request.get_json(force=True, silent=True) or {}
    errs = validate(d)
    if errs:
        return jsonify(ok=False, erori=errs), 400
    did = uuid.uuid4().hex[:12]
    files = genereaza(d, os.path.join(OUT, did))
    return jsonify(ok=True, id=did, fisiere=files)

def _safe(did):
    if not did.isalnum(): abort(404)
    p = os.path.join(OUT, did)
    if not os.path.isdir(p): abort(404)
    return p

@app.get("/dosar/<did>/<name>")
def fisier(did, name):
    return send_from_directory(_safe(did), name, as_attachment=request.args.get("dl") == "1")

@app.get("/dosar/<did>.zip")
def arhiva(did):
    p = _safe(did); buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(p)): z.write(os.path.join(p, f), f)
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=f"dosar_infiintare_{did}.zip")

@app.get("/healthz")
def health(): return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5055)))
