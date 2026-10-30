#!/usr/bin/env python3
"""Legacy score audit: interval analysis, NOT reconstruction of lost inputs."""
import argparse,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEIGHTS={"cashFlow":.45,"profitability":.2,"debt":.15,"operations":.1,"sustainability":.1}
THRESHOLDS=[(85,"Excellent"),(70,"Moderate-High"),(55,"Moderate"),(40,"Moderate-Low"),(0,"High-Risk")]
def grade(value):return next(g for t,g in THRESHOLDS if value>=t)
def analyze(c):
    raw=sum(c["scores"][k]*w for k,w in WEIGHTS.items())
    return {"company_id":c["id"],"name":c["name"],"published_score":c["total"],
            "published_grade":c["grade"],"from_rounded_dimensions":round(raw,4),
            "possible_unrounded_total":[round(max(0,raw-.5),4),round(min(100,raw+.5),4)],
            "precision_drift":round(abs(c["total"]-raw),6)>.55,
            "grade_boundary_ambiguous":c["grade"]!=grade(c["total"]),
            "reproduction_status":"needs_original_inputs",
            "verified_original_indicator_input":False}
def build(root=ROOT):
    catalog=json.loads((root/"docs/companies.json").read_text(encoding="utf-8"))
    rows=[analyze(c) for c in catalog];stats=Counter()
    for row in rows:
        stats["companies"]+=1
        stats["precision_drift"]+=int(row["precision_drift"])
        stats["grade_boundary_ambiguous"]+=int(row["grade_boundary_ambiguous"])
    return {"schema_version":"1.0","summary":dict(stats),"records":rows}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,default=ROOT/"data/legacy_score_reproduction.json")
    p.add_argument("--check",action="store_true")
    a=p.parse_args();v=build(a.root)
    payload=json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if a.check:
        if not a.output.exists() or a.output.read_text(encoding="utf-8")!=payload:
            print("Score manifest stale");return 1
    else:
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(payload,encoding="utf-8")
    print(json.dumps(v["summary"],ensure_ascii=False));return 0
if __name__=="__main__":raise SystemExit(main())
