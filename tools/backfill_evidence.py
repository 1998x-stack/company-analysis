#!/usr/bin/env python3
"""Create 230-row research gap ledger; observed links are not verified sources."""
import argparse,hashlib,json,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
URL=re.compile(r"https?://[^\s<>)\]\"']+")
YEAR=re.compile(r"(?<!\d)(20\d{2})\s*(?:年|FY|年度|财年|Q[1-4])")
def build(root=ROOT,candidates=None):
    catalog=json.loads((root/"docs/companies.json").read_text(encoding="utf-8"))
    sources={}
    for c in candidates or []:
        if not all(k in c for k in ("company_id","url","publisher","reporting_period")) or not c["url"].startswith("https://"):
            raise ValueError("Invalid source candidate")
        sources.setdefault(c["company_id"],[]).append(c)
    rows=[];stats=Counter()
    for c in catalog:
        raw=(root/"docs/examples"/c["report"]).read_bytes()
        text=raw.decode("utf-8")
        urls=sorted(set(URL.findall(text)))
        d=re.search(r"20\d{2}-\d{2}-\d{2}",c["report"])
        rows.append({
            "company_id":c["id"],"name":c["name"],"report":c["report"],
            "report_date":d.group() if d else None,
            "report_sha256":hashlib.sha256(raw).hexdigest(),
            "period_mentions":sorted(set(YEAR.findall(text))),
            "direct_urls_in_report":urls,
            "source_candidates":sources.get(c["id"],[]),
            "verification_status":"unverified_legacy_report",
            "verified_page_anchors":0,"original_score_input_available":False,
            "next_action":"verify_original_filings_and_indicator_assessments"})
        stats["companies"]+=1
        stats["without_direct_urls"]+=int(not urls)
        stats["short_reports_under_3000_bytes"]+=int(len(raw)<3000)
        stats["candidate_source_companies"]+=int(bool(sources.get(c["id"])))
    return {"schema_version":"1.0","summary":dict(stats),"records":rows}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,default=ROOT/"data/legacy_evidence_manifest.json")
    p.add_argument("--candidates",type=Path,default=ROOT/"data/source_candidates.json")
    p.add_argument("--check",action="store_true")
    a=p.parse_args()
    seed=json.loads(a.candidates.read_text(encoding="utf-8")) if a.candidates.exists() else []
    data=build(a.root,seed);payload=json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if a.check:
        if not a.output.exists() or a.output.read_text(encoding="utf-8")!=payload:
            print("Evidence manifest stale");return 1
    else:
        a.output.parent.mkdir(exist_ok=True,parents=True)
        a.output.write_text(payload,encoding="utf-8")
    print(json.dumps(data["summary"],ensure_ascii=False));return 0
if __name__=="__main__":raise SystemExit(main())
