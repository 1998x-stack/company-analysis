#!/usr/bin/env python3
"""Review-gated static site builder. Never overwrites the source repository."""
import argparse,importlib.util,json,hashlib,re,shutil,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MAP={"Cash Flow Quality":"cashFlow","Profitability":"profitability",
     "Debt Solvency":"debt","Operational Efficiency":"operations","Sustainability":"sustainability"}
LABEL={"Excellent":"优秀","Moderate-High":"中等偏上","Moderate":"中等",
       "Moderate-Low":"中等偏下","High-Risk":"高风险"}

def check_approval(s,a):
    fields={"evaluation_id","input_sha256","engine_sha256","reviewer","decision","approved_at"}
    if not isinstance(a,dict) or set(a)!=fields:raise ValueError("Approval fields invalid")
    if s["verification_status"]!="requires_human_review":raise ValueError("Invalid snapshot review state")
    for k in ("evaluation_id","input_sha256","engine_sha256"):
        if s[k]!=a[k]:raise ValueError("Approval hash mismatch")
    if a["decision"]!="approve" or not isinstance(a["reviewer"],str) or not a["reviewer"].strip():
        raise ValueError("Human approval required")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}",a["approved_at"]):raise ValueError("Approval date invalid")

def check_snapshot(s):
    spec=importlib.util.spec_from_file_location("publication_evaluation",ROOT/"tools/create_evaluation.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    fresh=module.calculate_snapshot(s["payload"])
    fields=("evaluation_id","company_id","as_of_date","rubric_version","input_sha256","engine_sha256","score_result")
    if any(s.get(field)!=fresh[field] for field in fields):
        raise ValueError("Snapshot differs from exact scoring replay")

def radar_svg(scores,total):
    keys=list(scores);cx,cy,R=240,190,120
    def point(i,score):
        th=-math.pi/2+2*math.pi*i/5
        return f"{cx+R*score/100*math.cos(th):.2f},{cy+R*score/100*math.sin(th):.2f}"
    grid="".join('<polygon points="'+ " ".join(point(i,n) for i in range(5))+
                 '" stroke="#475569" fill="none"/>' for n in (20,40,60,80,100))
    shape=" ".join(point(i,scores[k]) for i,k in enumerate(keys))
    names="".join(f'<text x="15" y="{345+i*19}" fill="white" font-size="12">{k}: {scores[k]}</text>'
                  for i,k in enumerate(keys))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="510" height="490" viewBox="0 0 510 490">'
            '<title>Five dimension financial health radar</title>'
            '<rect width="510" height="490" fill="#0f172a"/>'+grid+
            '<polygon points="'+shape+'" fill="#d4a853" fill-opacity=".25" stroke="#eab308" stroke-width="2"/>'+
            names+f'<text x="245" y="470" fill="white" text-anchor="middle">{total}/100</text></svg>\n')

def report_text(s,approval,company,radar):
    score=s["score_result"]
    rows=["# "+company["name"],"","Source-linked, human-reviewed input snapshot (not an independent audit).","",
          "Evaluation: "+s["evaluation_id"],"Reviewer: "+approval["reviewer"],
          "As of: "+s["as_of_date"],"Input SHA256: "+s["input_sha256"],
          "Engine SHA256: "+s["engine_sha256"],"",
          "| Dimension | Score |","|---|---:|"]
    for name,v in score["scores"].items():rows.append(f"| {name} | {v:.1f} |")
    rows+=["",f"Total: {score['total_score']:.1f}/100 ({score['grade']})","",
           "![Scoring radar]("+radar+")","","## Source registry"]
    for item in s["payload"]["sources"]:
        rows.append(f"- {item['evidence_id']} : {item['source_url']} "
                    f"({item['reporting_period']}; document_sha256 {item['document_sha256']})")
    rows+=["","## Scored indicators (evidence IDs are links, not proof)"]
    for dim,values in s["payload"]["score_input"].items():
        if dim=="company":continue
        rows+=["",f"### {dim}"]
        for key,value in values.items():
            ids=s["payload"]["indicator_evidence"][dim].get(key,[])
            rows.append(f"- {key}: {value} [evidence IDs: {', '.join(ids)}]")
    return "\n".join(rows)+"\n"

def indexes(catalog):
    ranks=["# Generated company ranking","", "Historical scores require verification.","",
           "| Company | Industry | Score | Grade |","|---|---|---:|---|"]
    sectors={}
    for c in sorted(catalog,key=lambda x:(-x["total"],x["id"])):
        ranks.append(f"| {c['name'].replace('|',' ')} | {c['ind1']} | {c['total']} | {c['grade']} |")
        sectors.setdefault(c["ind1"],[]).append(c)
    industry=["# Generated industry catalog",""]
    for sector,group in sorted(sectors.items()):
        industry+=[f"## {sector} ({len(group)})",""]
        industry += [f"- {x['name']}: {x['total']}" for x in group]
        industry.append("")
    return "\n".join(ranks)+"\n","\n".join(industry)+"\n"

def publish(snapshot,approval,company,out,root=ROOT):
    check_approval(snapshot,approval)
    check_snapshot(snapshot)
    if snapshot["company_id"]!=company["id"]:raise ValueError("Company ID mismatch")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+",company["id"]):raise ValueError("Unsafe company ID")
    if out.exists() and any(out.iterdir()):raise FileExistsError("Output must be empty")
    x=snapshot["score_result"]
    scores={MAP[k]:v for k,v in x["scores"].items()}
    if len(scores)!=5:raise ValueError("Five scores required")
    stem=snapshot["evaluation_id"]
    if not re.fullmatch(r"[a-zA-Z0-9_-]+",stem):raise ValueError("Unsafe ID")
    if any((root/"docs/examples"/(stem+suffix)).exists() for suffix in (".md",".svg")):
        raise ValueError("Evaluation asset already exists")
    record={"id":company["id"],"name":company["name"],"nameEn":company["nameEn"],
            "ticker":company.get("ticker",""),"ind1":company["ind1"],"ind2":company["ind2"],
            "scores":scores,"total":x["total_score"],"grade":x["grade"],
            "gradeLabel":LABEL[x["grade"]],"report":stem+".md","radar":stem+".svg",
            "oneLine":"人工审核的评估快照；证据链接不代表事实已核验","employees":"—","revenue":"—",
            "evaluation_id":stem,"verification_status":"reviewer_attested",
            "as_of_date":snapshot["as_of_date"],"rubric_version":snapshot["rubric_version"]}
    existing=json.loads((root/"docs/companies.json").read_text(encoding="utf-8"))
    catalog={c["id"]:c for c in existing}
    if record["id"] in catalog:
        historical=catalog[record["id"]]
        if any(company[key]!=historical[key] for key in ("name","ind1","ind2")):
            raise ValueError("Existing company identity or industry mismatch")
        versions=historical.get("evaluations",[])
        if any(item["evaluation_id"]==stem for item in versions):
            raise ValueError("Evaluation version already exists")
        catalog[record["id"]]={**historical,"evaluations":versions+[record]}
    else:
        catalog[record["id"]]=record
    out.mkdir(parents=True,exist_ok=True)
    dest=out/"docs/examples"
    shutil.copytree(root/"docs/examples",dest)
    shutil.copy2(root/"index.html",out/"index.html")
    shutil.copy2(root/"docs/material_review_baseline.json",out/"docs/material_review_baseline.json")
    shutil.copytree(root/"docs/企业健康度评估体系",out/"docs/企业健康度评估体系")
    (dest/record["radar"]).write_text(radar_svg(scores,x["total_score"]),encoding="utf-8")
    (dest/record["report"]).write_text(report_text(snapshot,approval,company,record["radar"]),encoding="utf-8")
    ordered=sorted(catalog.values(),key=lambda c:c["id"])
    (out/"docs/companies.json").write_text(json.dumps(ordered,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"company").mkdir()
    rank,industry=indexes(ordered)
    (out/"company/index.md").write_text(rank,encoding="utf-8")
    (out/"company/README.md").write_text(industry,encoding="utf-8")
    manifest={"evaluation_id":stem,"report":record["report"],"radar":record["radar"],
              "companies":len(ordered),"publication_kind":"new_version" if record["id"] in {c["id"] for c in existing} else "new_company",
              "status":"staged_not_deployed"}
    (out/"publication_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest

def main():
    p=argparse.ArgumentParser()
    for key in ("snapshot","approval","company","output_root"):
        p.add_argument("--"+key.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    m=publish(json.loads(a.snapshot.read_text(encoding="utf-8")),
              json.loads(a.approval.read_text(encoding="utf-8")),
              json.loads(a.company.read_text(encoding="utf-8")),a.output_root)
    print(json.dumps(m,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
