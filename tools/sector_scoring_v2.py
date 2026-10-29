#!/usr/bin/env python3
"""Experimental, sector-aware scoring and deterministic ablation.

Rubric thresholds are hypotheses, NOT empirically calibrated financial advice.
Missing data lowers coverage instead of automatically receiving a low score.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"configs/sector_rubrics_v2.json"

def rubric():
    return json.loads(CONFIG.read_text(encoding="utf-8"))

def validate_config(config):
    if config.get("status")!="uncalibrated_research_prototype":
        raise ValueError("Rubric must be flagged uncalibrated")
    for name,sector in config["sectors"].items():
        w=sum(d["weight"] for d in sector["metrics"].values())
        if abs(w-1)>1e-8:raise ValueError(f"{name}: weights must sum to 1")
        for k,d in sector["metrics"].items():
            if d["good"]==d["bad"] or d["weight"]<=0:
                raise ValueError(f"{name}.{k}: malformed anchors")

def score_metric(v,good,bad):
    if not math.isfinite(v):raise ValueError("Non-finite metric")
    ratio=(v-bad)/(good-bad)
    return round(max(10.0,min(90.0,10.0+80.0*ratio)),4)

def evaluate(data,config=None):
    cfg=config or rubric()
    validate_config(cfg)
    if not isinstance(data,dict) or data.get("sector") not in cfg["sectors"]:
        raise ValueError("Unsupported sector")
    definition=cfg["sectors"][data["sector"]]["metrics"]
    supplied=data.get("metrics")
    if not isinstance(supplied,dict) or set(supplied)-set(definition):
        raise ValueError("Invalid metric set")
    rows=[];covered=0.0
    for key,d in definition.items():
        item=supplied.get(key)
        if item is None or item.get("value") is None:
            rows.append({"metric":key,"status":"missing","weight":d["weight"]})
            continue
        if (type(item["value"]) not in (int,float) or
            not isinstance(item.get("evidence_ids"),list) or
            not item["evidence_ids"] or
            any(not isinstance(x,str) or not x for x in item["evidence_ids"])):
            raise ValueError(f"{key}: numeric value and nonempty evidence IDs required")
        if not isinstance(item.get("period"),str) or not item["period"]:
            raise ValueError(f"{key}: reporting period required")
        points=score_metric(item["value"],d["good"],d["bad"])
        rows.append({"metric":key,"status":"observed","weight":d["weight"],
                     "score":points,"value":item["value"],"period":item["period"],
                     "evidence_ids":item["evidence_ids"]})
        covered+=d["weight"]
    actual=[x for x in rows if x["status"]=="observed"]
    raw=sum(x["weight"]*x["score"] for x in actual)/covered if covered else None
    eligible=covered+1e-12>=cfg["minimum_coverage"]
    ablations={}
    if eligible:
        for row in actual:
            rem=covered-row["weight"]
            ablations[row["metric"]]=round(
                sum(x["weight"]*x["score"] for x in actual if x is not row)/rem,2
            ) if rem>0 else None
    weighted_interval=(min([raw]+[x for x in ablations.values() if x is not None]),
                       max([raw]+[x for x in ablations.values() if x is not None])) if eligible else None
    periods=sorted(set(x["period"] for x in actual))
    return {
        "model_version":cfg["schema_version"],"sector":data["sector"],
        "status":"experimental_unvalidated" if eligible else "insufficient_coverage",
        "metric_coverage":round(covered,4),"minimum_coverage":cfg["minimum_coverage"],
        "score_experimental":round(raw,2) if eligible else None,
        "reporting_periods":periods,
        "mixed_reporting_periods":len(periods)>1,
        "sensitivity_leave_one_out":ablations,
        "sensitivity_range":list(weighted_interval) if weighted_interval else None,
        "metrics":rows,
        "caution":"Uncalibrated sector anchors; do not compare scores across sectors or use as investment advice",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    data=evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    out=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(exist_ok=True,parents=True)
        args.output.write_text(out,encoding="utf-8")
    else:print(out)
if __name__=="__main__":main()
