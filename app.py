import os, uuid, io, zipfile, tempfile, shutil, time, hmac, hashlib, json, secrets
from datetime import timedelta
from functools import wraps
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file, abort, session, redirect, url_for, g
from validators import validate, CAPITAL_MINIM
from pdfgen import genereaza
import db

app = Flask(__name__)
app.config.update(MAX_CONTENT_LENGTH=15 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")), PERMANENT_SESSION_LIFETIME=timedelta(hours=12))

def _users():
    """APP_USERS="ana:parola1,mihai:parola2" sau APP_PASSWORD (utilizator implicit „admin”)."""
    u = {}
    for pair in (os.environ.get("APP_USERS") or "").split(","):
        if ":" in pair:
            k, v = pair.split(":", 1); u[k.strip().lower()] = v.strip()
    if os.environ.get("APP_PASSWORD"):
        u.setdefault("admin", os.environ["APP_PASSWORD"])
    return u

_seed = os.environ.get("SECRET_KEY") or hashlib.sha256(("pf-" + json.dumps(sorted(_users().items()))).encode()).hexdigest()
app.secret_key = _seed if _users() or os.environ.get("SECRET_KEY") else secrets.token_hex(32)
OUT = os.path.join(tempfile.gettempdir(), "dosare"); os.makedirs(OUT, exist_ok=True)
_fails = {}

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("user"):
            if request.path.startswith("/api/") or request.method != "GET": return jsonify(ok=False, erori=["Sesiune expirată – autentificați-vă din nou."]), 401
            return redirect(url_for("login", next=request.path))
        if request.method in ("POST", "DELETE", "PUT") and request.headers.get("X-Requested-With") != "fetch" and request.endpoint not in ("logout",):
            abort(403)
        g.user = session["user"]; return f(*a, **k)
    return w

@app.route("/login", methods=["GET", "POST"])
def login():
    err = None
    if request.method == "POST":
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0]
        n, t = _fails.get(ip, (0, 0))
        if n >= 5 and time.time() - t < 300:
            err = "Prea multe încercări. Reîncercați peste 5 minute."
        else:
            user = (request.form.get("user") or "admin").strip().lower(); pw = request.form.get("parola", "")
            exp = _users().get(user)
            if exp and hmac.compare_digest(exp.encode(), pw.encode()):
                session.clear(); session.permanent = True; session["user"] = user; _fails.pop(ip, None)
                nxt = request.args.get("next", "/")
                return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else "/")
            _fails[ip] = (n + 1, time.time()); err = "Utilizator sau parolă greșită."
    return render_template("login.html", err=err, configurat=bool(_users()))

@app.post("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

def cleanup(max_age=3600):
    now = time.time()
    for d in os.listdir(OUT):
        p = os.path.join(OUT, d)
        if os.path.isdir(p) and now - os.path.getmtime(p) > max_age: shutil.rmtree(p, ignore_errors=True)

@app.get("/")
@login_required
def index():
    return render_template("index.html", capital_minim=CAPITAL_MINIM, user=g.user, dosar_id=request.args.get("dosar", type=int))

@app.get("/dosare")
@login_required
def page_dosare():
    q = request.args.get("q", "").strip()
    return render_template("dosare.html", items=db.list_dossiers(q), q=q, user=g.user)

@app.get("/persoane")
@login_required
def page_persoane():
    q = request.args.get("q", "").strip()
    return render_template("persoane.html", items=db.list_persons(q), q=q, user=g.user)

@app.get("/firme")
@login_required
def page_firme():
    q = request.args.get("q", "").strip()
    return render_template("firme.html", items=db.list_companies(q), q=q, user=g.user)

def _gen(d):
    cleanup(); tid = uuid.uuid4().hex[:12]
    return tid, genereaza(d, os.path.join(OUT, tid))

@app.post("/api/genereaza")
@login_required
def api_gen():
    body = request.get_json(force=True, silent=True) or {}
    d = body.get("data", body); did = body.get("dosar_id")
    errs = validate(d)
    if errs: return jsonify(ok=False, erori=errs), 400
    for p in d.get("asociati", []) + d.get("administratori", []) + [d.get("sediu", {}).get("proprietar", {})]:
        db.upsert_person(p)
    db.upsert_company(d)
    did = db.save_dossier(d, g.user, did)
    tid, files = _gen(d)
    return jsonify(ok=True, id=tid, dosar_id=did, fisiere=files)

@app.post("/api/dosare/<int:did>/regenereaza")
@login_required
def api_regen(did):
    ds = db.get_dossier(did) or abort(404)
    tid, files = _gen(ds["data"]); return jsonify(ok=True, id=tid, dosar_id=did, fisiere=files)

@app.get("/api/dosare/<int:did>")
@login_required
def api_dosar(did):
    return jsonify(db.get_dossier(did) or abort(404))

@app.delete("/api/dosare/<int:did>")
@login_required
def api_dosar_del(did):
    db.delete_dossier(did); return jsonify(ok=True)

@app.get("/api/persoane")
@login_required
def api_persoane():
    return jsonify(db.list_persons(request.args.get("q", "")))

@app.delete("/api/persoane/<int:pid>")
@login_required
def api_persoana_del(pid):
    db.delete_person(pid); return jsonify(ok=True)

@app.get("/api/firme")
@login_required
def api_firme():
    return jsonify(db.list_companies(request.args.get("q", "")))

@app.post("/api/ci")
@login_required
def api_ci():
    """Recunoaștere CI. Imaginile sunt procesate exclusiv în memorie și nu sunt salvate."""
    files = [f.read() for f in request.files.getlist("imagini") if f and f.filename][:2]
    if not files: return jsonify(ok=False, erori=["Încărcați cel puțin o imagine."]), 400
    try:
        from ocr_worker import run
        r = run(files)
    except Exception as e:
        app.logger.exception("OCR"); return jsonify(ok=False, erori=[f"Imaginea nu a putut fi procesată ({type(e).__name__})."]), 400
    finally:
        files.clear()
    r.pop("linii_ocr", None)
    return jsonify(ok=True, rezultat=r)

@app.get("/api/backup")
@login_required
def api_backup():
    buf = io.BytesIO(json.dumps(db.export_all(), ensure_ascii=False, indent=1, default=str).encode())
    return send_file(buf, mimetype="application/json", as_attachment=True, download_name=f"backup_platforma_{time.strftime('%Y%m%d_%H%M')}.json")

@app.post("/api/import")
@login_required
def api_import():
    f = request.files.get("fisier")
    if not f: return jsonify(ok=False, erori=["Lipsește fișierul."]), 400
    n = db.import_all(json.load(f)); return jsonify(ok=True, importate=n)

def _safe(did):
    if not did.isalnum(): abort(404)
    p = os.path.join(OUT, did)
    if not os.path.isdir(p): abort(404)
    return p

@app.get("/dosar/<did>/<name>")
@login_required
def fisier(did, name):
    return send_from_directory(_safe(did), name, as_attachment=request.args.get("dl") == "1")

@app.get("/dosar/<did>.zip")
@login_required
def arhiva(did):
    p = _safe(did); buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(p)): z.write(os.path.join(p, f), f)
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=f"dosar_{did}.zip")

@app.context_processor
def ctx():
    return {"db_efemer": not db.url.startswith("postgresql") and bool(os.environ.get("RENDER"))}

@app.get("/healthz")
def health(): return "ok"

@app.after_request
def headers(r):
    r.headers["X-Frame-Options"] = "DENY"; r.headers["X-Content-Type-Options"] = "nosniff"; r.headers["Referrer-Policy"] = "same-origin"
    if request.path.startswith(("/api/", "/dosar")): r.headers["Cache-Control"] = "no-store"
    return r

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5055)))
