#!/usr/bin/env python3
"""Exact replay of persisted *new* v1 evaluations, with integrity checks.

This is separate from historical 230-company forensic diagnostics, since the
original indicator inputs for those reports have not been recovered.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from create_evaluation import ENGINE_PATH,canonical,calculate_snapshot

def replay(snapshot):
    if snapshot.get("rubric_version")!="financial-health-v1":
        raise ValueError("Unsupported rubric version")
    if snapshot.get("engine_sha256")!=hashlib.sha256(ENGINE_PATH.read_bytes()).hexdigest():
        raise ValueError("Engine version mismatch: replay needs recorded code")
    if not isinstance(snapshot.get("payload"),dict):
        raise ValueError("Missing original indicator payload")
    fresh=calculate_snapshot(snapshot["payload"])
    if fresh["input_sha256"]!=snapshot.get("input_sha256"):
        raise ValueError("Input SHA256 mismatch")
    if fresh["evaluation_id"]!=snapshot.get("evaluation_id"):
        raise ValueError("Evaluation ID mismatch")
    if fresh["score_result"]!=snapshot.get("score_result"):
        raise ValueError("Score differs from original stored result")
    return {"evaluation_id":snapshot["evaluation_id"],"company_id":snapshot["company_id"],
            "status":"exact_replay_verified","engine_sha256":snapshot["engine_sha256"],
            "input_sha256":snapshot["input_sha256"],"score":fresh["score_result"]["total_score"]}

def replay_dir(path):
    results=[];errors=[]
    for file in sorted(path.rglob("*.json")):
        try:
            results.append(replay(json.loads(file.read_text(encoding="utf-8"))))
        except (ValueError,KeyError,TypeError) as error:
            errors.append({"file":str(file),"error":str(error)})
    return {"scanned":len(results)+len(errors),"verified":len(results),
            "failed":len(errors),"results":results,"errors":errors}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path)
    p.add_argument("--directory",type=Path)
    a=p.parse_args()
    if bool(a.input)==bool(a.directory):raise SystemExit("Choose exactly one of --input or --directory")
    result=replay(json.loads(a.input.read_text(encoding="utf-8"))) if a.input else replay_dir(a.directory)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if isinstance(result,dict) and result.get("failed",0)>0:raise SystemExit(1)
if __name__=="__main__":main()
