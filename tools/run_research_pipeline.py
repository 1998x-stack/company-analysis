#!/usr/bin/env python3
"""Resumable SQLite research workflow with explicit source and publication gates.

States: queued -> collected -> parsed -> review_required -> approved -> staged.
Automated steps verify hashes/parse documents/run a *submitted* rubric; they
never invent missing indicators or claim that sources prove the judgments.
"""
import argparse,hashlib,importlib.util,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(file,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"tools"/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
factory=load("create_evaluation.py","evaluation_factory")
publisher=load("publish_factory.py","static_publisher")
collector=load("collect_sources.py","source_collector")

def connect(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""CREATE TABLE IF NOT EXISTS runs(
      run_id TEXT PRIMARY KEY,state TEXT NOT NULL,
      request_json TEXT NOT NULL,artifacts_json TEXT NOT NULL,
      attempts INTEGER NOT NULL DEFAULT 0,last_error TEXT)""")
    db.execute("""CREATE TABLE IF NOT EXISTS transitions(
      run_id TEXT NOT NULL,state TEXT NOT NULL,
      note TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    db.commit();return db

def job_id(job):
    return hashlib.sha256(json.dumps(job,sort_keys=True,ensure_ascii=False,
                        separators=(",",":")).encode("utf-8")).hexdigest()[:24]

def enqueue(db,job):
    if set(job)!={"evaluation_input","company_record","source_files"}:
        raise ValueError("Job requires three fields: evaluation_input/company_record/source_files")
    factory.validate_input(job["evaluation_input"])
    if job["company_record"]["id"]!=job["evaluation_input"]["company_id"]:
        raise ValueError("Company identity mismatch")
    ids={s["evidence_id"] for s in job["evaluation_input"]["sources"]}
    if set(job["source_files"])!=ids:raise ValueError("Exactly one local document per evidence ID")
    key=job_id(job)
    db.execute("INSERT OR IGNORE INTO runs VALUES(?, 'queued', ?, '{}', 0, NULL)",
               (key,json.dumps(job,ensure_ascii=False,sort_keys=True)))
    db.commit();return key

def row(db,key):
    v=db.execute("SELECT * FROM runs WHERE run_id=?",(key,)).fetchone()
    if v is None:raise KeyError("Unknown run ID")
    return v

def advance(db,key,store):
    r=row(db,key);state=r["state"];job=json.loads(r["request_json"])
    metadata=json.loads(r["artifacts_json"])
    store.mkdir(parents=True,exist_ok=True)
    try:
        if state=="queued":
            docs={}
            for item in job["evaluation_input"]["sources"]:
                path=Path(job["source_files"][item["evidence_id"]])
                if not path.is_file():raise FileNotFoundError(path)
                content=path.read_bytes()
                sha=hashlib.sha256(content).hexdigest()
                if sha.lower()!=item["document_sha256"].lower():
                    raise ValueError("Source document SHA256 mismatch")
                if len(content)>8_000_000:raise ValueError("Source exceeds limit")
                docs[item["evidence_id"]]={"path":str(path),"sha256":sha,"bytes":len(content)}
            metadata["documents"]=docs;next_state="collected"
        elif state=="collected":
            parsed={}
            for source in job["evaluation_input"]["sources"]:
                sid=source["evidence_id"]
                path=Path(metadata["documents"][sid]["path"])
                content=path.read_bytes()
                if hashlib.sha256(content).hexdigest()!=metadata["documents"][sid]["sha256"]:
                    raise ValueError("Document changed after collection")
                suffix=path.suffix.lower()
                media="application/pdf" if suffix==".pdf" else "text/html" if suffix in (".html",".htm") else "text/plain"
                text=collector.extract_text(content,media)
                if not text.strip():raise ValueError("Empty parsed document")
                parsed[sid]={"characters":len(text),"extract_sha256":hashlib.sha256(text.encode()).hexdigest()}
                # Avoid storing copyrighted source text in this repository.
            metadata["extraction"]=parsed;next_state="parsed"
        elif state=="parsed":
            snap=factory.calculate_snapshot(job["evaluation_input"])
            output=factory.save_snapshot(snap,store/"evaluations")
            metadata["snapshot_path"]=str(output)
            next_state="review_required"
        else:raise ValueError("Cannot automatically advance state "+state)
        with db:
            db.execute("UPDATE runs SET state=?,artifacts_json=?,last_error=NULL WHERE run_id=?",
                       (next_state,json.dumps(metadata,sort_keys=True),key))
            db.execute("INSERT INTO transitions(run_id,state,note) VALUES(?,?,?)",
                       (key,next_state,"automated step"))
        return next_state
    except Exception as exc:
        with db:
            db.execute("UPDATE runs SET state='failed',attempts=attempts+1,last_error=? WHERE run_id=?",
                       (str(exc),key))
            db.execute("INSERT INTO transitions(run_id,state,note) VALUES(?,?,?)",
                       (key,"failed",str(exc)[:300]))
        raise

def run_to_review(db,key,store):
    while row(db,key)["state"] in ("queued","collected","parsed"):
        advance(db,key,store)
    return row(db,key)["state"]

def retry(db,key,max_attempts=3):
    r=row(db,key)
    if r["state"]!="failed":raise ValueError("Only failed runs can retry")
    if r["attempts"]>=max_attempts:raise ValueError("Retry budget exhausted")
    with db:
        db.execute("UPDATE runs SET state='queued',artifacts_json='{}',last_error=NULL WHERE run_id=?",(key,))

def approve(db,key,receipt):
    r=row(db,key)
    if r["state"]!="review_required":raise ValueError("Run is not pending review")
    m=json.loads(r["artifacts_json"])
    snap=json.loads(Path(m["snapshot_path"]).read_text(encoding="utf-8"))
    publisher.check_approval(snap,receipt)
    m["approval"]=receipt
    with db:
        db.execute("UPDATE runs SET state='approved',artifacts_json=? WHERE run_id=?",
                   (json.dumps(m,sort_keys=True),key))
    return "approved"

def stage(db,key,out):
    r=row(db,key)
    if r["state"]!="approved":raise ValueError("Human approval required before publication")
    meta=json.loads(r["artifacts_json"])
    snap=json.loads(Path(meta["snapshot_path"]).read_text(encoding="utf-8"))
    job=json.loads(r["request_json"])
    result=publisher.publish(snap,meta["approval"],job["company_record"],out)
    meta["publication"]=result
    with db:
        db.execute("UPDATE runs SET state='staged',artifacts_json=? WHERE run_id=?",
                   (json.dumps(meta,sort_keys=True),key))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["enqueue","run","retry","status","approve","publish"])
    p.add_argument("--db",type=Path,default=ROOT/"data/runtime/research.sqlite")
    p.add_argument("--store",type=Path,default=ROOT/"data/runtime")
    p.add_argument("--input",type=Path)
    p.add_argument("--id")
    p.add_argument("--approval",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args();db=connect(a.db)
    try:
        if a.action=="enqueue":
            if not a.input:raise ValueError("--input required")
            print(enqueue(db,json.loads(a.input.read_text(encoding="utf-8"))))
        elif a.action=="run":print(run_to_review(db,a.id,a.store))
        elif a.action=="retry":retry(db,a.id);print("queued")
        elif a.action=="status":
            r=row(db,a.id)
            print(json.dumps({k:r[k] for k in ("run_id","state","attempts","last_error")},indent=2))
        elif a.action=="approve":
            if not a.approval:raise ValueError("--approval required")
            print(approve(db,a.id,json.loads(a.approval.read_text(encoding="utf-8"))))
        elif a.action=="publish":
            if not a.out:raise ValueError("--out required")
            print(json.dumps(stage(db,a.id,a.out),ensure_ascii=False,indent=2))
    finally:db.close()
if __name__=="__main__":main()
