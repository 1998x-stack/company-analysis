#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree

from audit_repository import audit_repository
from backfill_evidence import build as build_evidence
from radar_geometry import verify as verify_radar
from reproduce_scores import build as build_scores

ROOT = Path(__file__).resolve().parents[1]
IMAGE_REF = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
DATE = re.compile(r"20\d{2}-\d{2}-\d{2}")
SCORE = re.compile(r"(?<!\d)(\d+(?:\.\d+)?)\s*/\s*100")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def image_details(path: Path) -> dict:
    raw = path.read_bytes()
    result = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    if path.suffix.lower() == ".png":
        result["format_valid"] = raw.startswith(PNG_SIGNATURE) and raw[12:16] == b"IHDR"
        if result["format_valid"] and len(raw) >= 24:
            result["width"], result["height"] = struct.unpack(">II", raw[16:24])
    elif path.suffix.lower() == ".svg":
        try:
            result["format_valid"] = ElementTree.parse(path).getroot().tag.endswith("svg")
        except ElementTree.ParseError:
            result["format_valid"] = False
    else:
        result["format_valid"] = False
    return result


def build(root: Path = ROOT) -> dict:
    root = root.resolve()
    catalog = json.loads((root / "docs/companies.json").read_text(encoding="utf-8"))
    candidates = json.loads((root / "data/source_candidates.json").read_text(encoding="utf-8"))
    evidence = {row["company_id"]: row for row in build_evidence(root, candidates)["records"]}
    scores = {row["company_id"]: row for row in build_scores(root)["records"]}
    audited = audit_repository(root)
    warnings = defaultdict(list)
    for issue in audited["issues"]:
        warnings[issue["company"]].append(issue["code"])

    archive = defaultdict(list)
    for link in (root / "company").rglob("*"):
        if link.is_symlink() and link.exists():
            archive[link.resolve()].append(link.relative_to(root).as_posix())

    radar_hashes = defaultdict(list)
    for company in catalog:
        path = root / "docs/examples" / company["radar"]
        if path.is_file():
            radar_hashes[hashlib.sha256(path.read_bytes()).hexdigest()].append(company["id"])

    records = []
    review_issues = []
    referenced = set()
    for company in catalog:
        cid = company["id"]
        report_path = root / "docs/examples" / company["report"]
        radar_path = root / "docs/examples" / company["radar"]
        referenced.update((company["report"], company["radar"]))
        text = report_path.read_text(encoding="utf-8")
        heading = text.splitlines()[0] if text else ""
        heading_date = DATE.search(heading)
        report_date = evidence[cid]["report_date"]
        conclusion = text.split("## 一句话结论", 1)[1].split("\n## ", 1)[0] if "## 一句话结论" in text else text[:500]
        conclusion_score_match = SCORE.search(conclusion)
        conclusion_score = float(conclusion_score_match.group(1)) if conclusion_score_match else None
        image_refs = [match.strip().split(" ")[0] for match in IMAGE_REF.findall(text)]
        missing_images = [name for name in image_refs
                          if not name.startswith(("https://", "http://"))
                          and not (report_path.parent / name).is_file()]
        report_links = [link for link in archive[report_path.resolve()]
                        if link.startswith(f"company/{company['ind1']}/{company['ind2']}/")]
        radar_links = [link for link in archive[radar_path.resolve()]
                       if link.startswith(f"company/{company['ind1']}/{company['ind2']}/")]
        radar = image_details(radar_path)
        radar_geometry = verify_radar(radar_path, company["scores"])
        structural = []
        if missing_images:
            structural.append("broken_report_image")
        if not report_links:
            structural.append("missing_industry_report_link")
        if not radar_links:
            structural.append("missing_industry_radar_link")
        if not radar["format_valid"]:
            structural.append("invalid_radar_file")
        if radar_geometry["status"] == "geometry_unavailable":
            structural.append("radar_geometry_unavailable")
        review = []
        if heading_date and heading_date.group() != report_date:
            review.append("report_heading_date_differs_from_filename")
            review_issues.append({"company_id": cid,
                                  "code": "report_heading_date_differs_from_filename",
                                  "detail": f"filename={report_date}; heading={heading_date.group()}"})
        if conclusion_score is not None and abs(conclusion_score - company["total"]) > 0.51:
            review.append("report_conclusion_score_differs_from_catalog")
            review_issues.append({"company_id": cid,
                                  "code": "report_conclusion_score_differs_from_catalog",
                                  "detail": f"catalog={company['total']}; conclusion={conclusion_score:g}"})
        if radar_geometry["status"] == "geometry_differs_from_catalog":
            review.append("radar_geometry_differs_from_catalog")
            review_issues.append({"company_id": cid,
                                  "code": "radar_geometry_differs_from_catalog",
                                  "detail": f"radar_sha256={radar['sha256']}; "
                                            f"catalog_scores={','.join(str(company['scores'][key]) for key in ('cashFlow', 'profitability', 'debt', 'operations', 'sustainability'))}"})
        if len(text.encode("utf-8")) < 3000:
            review.append("short_report_under_3000_bytes")
        if not evidence[cid]["direct_urls_in_report"]:
            review.append("no_direct_source_url")
        review.extend(warnings[company["name"]])
        records.append({
            "company_id": cid, "name": company["name"],
            "industry": [company["ind1"], company["ind2"]],
            "catalog_display": {"name_en": company.get("nameEn", ""),
                                "ticker_text": company.get("ticker", ""),
                                "employees_text": company.get("employees", ""),
                                "revenue_text": company.get("revenue", ""),
                                "one_line": company.get("oneLine", ""),
                                "status": "historical_unverified_text"},
            "report": {"path": report_path.relative_to(root).as_posix(),
                       "sha256": evidence[cid]["report_sha256"],
                       "bytes": len(text.encode("utf-8")), "filename_date": report_date,
                       "heading": heading, "catalog_name_exact_in_heading": company["name"] in heading,
                       "heading_date": heading_date.group() if heading_date else None,
                       "conclusion_score": conclusion_score,
                       "image_refs": image_refs, "missing_image_refs": missing_images,
                       "industry_links": sorted(report_links)},
            "radar": {"path": radar_path.relative_to(root).as_posix(), **radar,
                      "geometry": radar_geometry,
                      "industry_links": sorted(radar_links),
                      "same_bytes_company_ids": sorted(x for x in radar_hashes[radar["sha256"]]
                                                       if x != cid)},
            "score": {"total": company["total"], "grade": company["grade"],
                      "dimension_scores": company["scores"],
                      "precision_drift": scores[cid]["precision_drift"],
                      "grade_boundary_ambiguous": scores[cid]["grade_boundary_ambiguous"],
                      "original_input_available": False},
            "evidence": {"direct_urls": evidence[cid]["direct_urls_in_report"],
                         "candidate_count": len(evidence[cid]["source_candidates"]),
                         "verified_page_anchors": 0,
                         "status": "unverified_legacy_report"},
            "structural_errors": sorted(set(structural)),
            "review_flags": sorted(set(review)),
        })

    catalog_ids = [company["id"] for company in catalog]
    if len(catalog_ids) != len(set(catalog_ids)) or len(records) != len(catalog_ids):
        raise ValueError("Company coverage is incomplete or IDs are duplicated")
    extras = sorted(path.name for path in (root / "docs/examples").iterdir()
                    if path.is_file() and path.name not in referenced)
    return {
        "schema_version": "1.0",
        "scope": "local_material_consistency_only",
        "review_issues": sorted(review_issues, key=lambda item: (item["code"], item["company_id"])),
        "summary": {"companies": len(records),
                    "structural_errors": sum(bool(row["structural_errors"]) for row in records),
                    "reports_without_direct_url": sum(not row["evidence"]["direct_urls"] for row in records),
                    "reports_shorter_than_3000_bytes": sum(row["report"]["bytes"] < 3000 for row in records),
                    "report_date_mismatches": sum("report_heading_date_differs_from_filename" in row["review_flags"] for row in records),
                    "report_conclusion_score_mismatches": sum("report_conclusion_score_differs_from_catalog" in row["review_flags"] for row in records),
                    "radar_geometry_mismatches": sum("radar_geometry_differs_from_catalog" in row["review_flags"] for row in records),
                    "reports_without_parsed_conclusion_score": sum(row["report"]["conclusion_score"] is None for row in records),
                    "unreferenced_assets": extras,
                    "review_flag_counts": dict(sorted(Counter(flag for row in records
                                                            for flag in row["review_flags"]).items()))},
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory local materials for every catalog company")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    result = build(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    new_issues = set()
    if args.baseline:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        allowed = {(item["company_id"], item["code"], item["detail"]) for item in baseline}
        current = {(item["company_id"], item["code"], item["detail"])
                   for item in result["review_issues"]}
        new_issues = current - allowed
        print(f"Material baseline: {len(current & allowed)} known, "
              f"{len(new_issues)} unexpected, {len(allowed - current)} resolved")
        for company_id, code, detail in sorted(new_issues):
            print(f"  [NEW REVIEW ISSUE] {company_id}: {code}: {detail}")
    return int(result["summary"]["structural_errors"] > 0 or bool(new_issues))


if __name__ == "__main__":
    raise SystemExit(main())
