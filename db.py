"""Persistență: Postgres (DATABASE_URL pe Render) sau SQLite local."""
import os, json, datetime as dt
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, select, or_, func, delete, update, insert

url = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(os.path.dirname(__file__), "local.sqlite")
if url.startswith("postgres://"):
    url = "postgresql://" + url[len("postgres://"):]
engine = create_engine(url, pool_pre_ping=True, pool_size=3, max_overflow=2) if url.startswith("postgresql") else create_engine(url)
md = MetaData()
from zoneinfo import ZoneInfo
_TZ = ZoneInfo("Europe/Bucharest")
now = lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)

persons = Table("persons", md,
    Column("id", Integer, primary_key=True), Column("cnp", String(13), unique=True, index=True),
    Column("nume", String(200), index=True), Column("data", Text), Column("created_at", DateTime, default=now), Column("updated_at", DateTime, default=now))
companies = Table("companies", md,
    Column("id", Integer, primary_key=True), Column("denumire", String(200), unique=True, index=True),
    Column("data", Text), Column("created_at", DateTime, default=now), Column("updated_at", DateTime, default=now))
dossiers = Table("dossiers", md,
    Column("id", Integer, primary_key=True), Column("tip", String(40), default="infiintare_srl"),
    Column("denumire", String(200), index=True), Column("status", String(40), default="draft"),
    Column("data", Text), Column("created_by", String(80)), Column("created_at", DateTime, default=now), Column("updated_at", DateTime, default=now))
md.create_all(engine)

def _row(r):
    d = dict(r._mapping); d["data"] = json.loads(d["data"] or "{}")
    for k in ("created_at", "updated_at"):
        if d.get(k): d[k] = d[k].replace(tzinfo=dt.timezone.utc).astimezone(_TZ).strftime("%d.%m.%Y %H:%M")
    return d

PERSON_KEYS = ["nume", "cnp", "cetatenie", "data_nasterii", "loc_nastere", "sex", "ci_serie", "ci_numar", "ci_emitent", "ci_data", "ci_valabilitate", "domiciliu"]

def upsert_person(p):
    cnp = (p.get("cnp") or "").strip()
    if not cnp: return None
    data = {k: p.get(k, "") for k in PERSON_KEYS if p.get(k)}
    with engine.begin() as c:
        r = c.execute(select(persons).where(persons.c.cnp == cnp)).first()
        if r:
            merged = {**json.loads(r.data or "{}"), **data}
            c.execute(update(persons).where(persons.c.id == r.id).values(nume=p.get("nume") or r.nume, data=json.dumps(merged, ensure_ascii=False), updated_at=now()))
            return r.id
        return c.execute(insert(persons).values(cnp=cnp, nume=p.get("nume", ""), data=json.dumps(data, ensure_ascii=False))).inserted_primary_key[0]

def list_persons(q=""):
    s = select(persons).order_by(persons.c.nume)
    if q: s = s.where(or_(persons.c.nume.ilike(f"%{q}%"), persons.c.cnp.like(f"%{q}%")))
    with engine.connect() as c: return [_row(r) for r in c.execute(s.limit(500))]

def delete_person(pid):
    with engine.begin() as c: c.execute(delete(persons).where(persons.c.id == pid))

def upsert_company(d):
    den = d["denumire"].strip().upper()
    data = {"denumire": d["denumire"], "sediu": d.get("sediu"), "caen_principal": d.get("caen_principal"), "capital": d.get("capital")}
    with engine.begin() as c:
        r = c.execute(select(companies).where(companies.c.denumire == den)).first()
        if r: c.execute(update(companies).where(companies.c.id == r.id).values(data=json.dumps(data, ensure_ascii=False), updated_at=now())); return r.id
        return c.execute(insert(companies).values(denumire=den, data=json.dumps(data, ensure_ascii=False))).inserted_primary_key[0]

def list_companies(q=""):
    s = select(companies).order_by(companies.c.denumire)
    if q: s = s.where(companies.c.denumire.ilike(f"%{q}%"))
    with engine.connect() as c: return [_row(r) for r in c.execute(s.limit(500))]

def save_dossier(d, user, did=None, status="generat"):
    vals = dict(denumire=d.get("denumire", ""), data=json.dumps(d, ensure_ascii=False), status=status, updated_at=now())
    with engine.begin() as c:
        if did:
            c.execute(update(dossiers).where(dossiers.c.id == did).values(**vals)); return did
        return c.execute(insert(dossiers).values(created_by=user, **vals)).inserted_primary_key[0]

def get_dossier(did):
    with engine.connect() as c:
        r = c.execute(select(dossiers).where(dossiers.c.id == did)).first()
        return _row(r) if r else None

def list_dossiers(q=""):
    s = select(dossiers).order_by(dossiers.c.updated_at.desc())
    if q: s = s.where(or_(dossiers.c.denumire.ilike(f"%{q}%"), dossiers.c.data.ilike(f"%{q}%")))
    with engine.connect() as c:
        out = []
        for r in c.execute(s.limit(500)):
            d = _row(r); data = d.pop("data")
            d["asociati"] = ", ".join(a.get("nume", "") for a in data.get("asociati", []))
            out.append(d)
        return out

def delete_dossier(did):
    with engine.begin() as c: c.execute(delete(dossiers).where(dossiers.c.id == did))

def export_all():
    out = {}
    with engine.connect() as c:
        for t in (persons, companies, dossiers):
            out[t.name] = [{**dict(r._mapping), "created_at": str(r.created_at), "updated_at": str(r.updated_at)} for r in c.execute(select(t))]
    return out

def import_all(blob):
    n = 0
    for p in blob.get("persons", []):
        d = json.loads(p["data"]) if isinstance(p.get("data"), str) else p.get("data", {})
        upsert_person({**d, "cnp": p["cnp"], "nume": p["nume"]}); n += 1
    for co in blob.get("companies", []):
        d = json.loads(co["data"]) if isinstance(co.get("data"), str) else co.get("data", {})
        if d.get("denumire"): upsert_company(d); n += 1
    with engine.begin() as c:
        existing = {(r.denumire, r.data) for r in c.execute(select(dossiers.c.denumire, dossiers.c.data))}
        for ds in blob.get("dossiers", []):
            data = ds["data"] if isinstance(ds["data"], str) else json.dumps(ds["data"], ensure_ascii=False)
            if (ds["denumire"], data) in existing: continue
            c.execute(insert(dossiers).values(denumire=ds["denumire"], data=data, status=ds.get("status", "generat"), created_by=ds.get("created_by"))); n += 1
    return n
