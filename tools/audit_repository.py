#!/usr/bin/env python3
"""Read-only integrity audit for the versioned company research catalog.

This checker intentionally distinguishes errors (invalid references/data) from
warnings (legacy inconsistencies requiring research or a scoring-version change).
No reports, ratings, symlinks, or PNGs are ever silently rewritten.

Run:
    python3 tools/audit_repository.py
    python3 tools/audit_repository.py --format json
    python3 tools/audit_repository.py --strict
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

DIMENSION_WEIGHTS = {
    "cashFlow": 0.45,
    "profitability": 0.20,
    "debt": 0.15,
    "operations": 0.10,
    "sustainability": 0.10,
}
GRADE_THRESHOLDS = (
    (85, "Excellent"),
    (70, "Moderate-High"),
    (55, "Moderate"),
    (40, "Moderate-Low"),
    (0, "High-Risk"),
)
EXPECTED_FIELDS = {
    "id", "name", "ind1", "ind2", "scores", "total", "grade", "report", "radar",
}
HEADER_RE = re.compile(
    r"^###\s*[1-5][.．、]\s*(.+?)\s*[（(]\s*(\d+(?:\.\d+)?)\s*/\s*100\s*[）)]",
    re.M,
)
HEADING_LABELS = {
    "cashFlow": ("现金流",),
    "profitability": ("盈利",),
    "debt": ("偿债", "债务"),
    "operations": ("运营",),
    "sustainability": ("可持续",),
}
# Only the conclusion anchors are scanned for grade words. Risk lists ("极高风险"),
# numeric ranges ("40-55%") and salary bands are never grade statements, and
# company names containing 卓越 are not grades at all.
GRADE_LABELS = {
    "Excellent": "优秀",
    "Moderate-High": "中等偏上",
    "Moderate": "中等",
    "Moderate-Low": "中等偏下",
    "High-Risk": "高风险",
}
GRADE_WORD_HEAD_RE = re.compile(r"^(优秀|中等偏上|中等偏下|中等|高风险)")
GRADE_LABEL_RE = re.compile(r"\*\*(健康等级|评级|综合评分|综合得分)")
GRADE_PREFIX_RE = re.compile(r"^[^\w\u4e00-\u9fff]*")
# Some reports put the five dimension scores in the score table and have no
# ``### N. 维度（xx/100）`` sub-heading at all, which used to make those scores
# invisible to this audit. These labels are matched exactly so that "pipe as
# separator" summary rows (``| 现金流 72.5|45%=32.6 |``) are ignored.
DIMENSION_LABELS = {
    "现金流质量": "cashFlow", "现金流": "cashFlow",
    "盈利能力": "profitability", "盈利": "profitability",
    "偿债能力": "debt", "偿债": "debt",
    "运营效率": "operations", "运营": "operations",
    "可持续发展能力": "sustainability", "可持续发展": "sustainability",
    "可持续": "sustainability",
}
DIMENSION_TABLE_SECTION_RE = re.compile(r"^##\s*[三3][、.．]?\s*(?:综合|评分).*$", re.M)
PLAIN_NUMBER_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def dimension_table_scores(report: str) -> dict[str, float]:
    """Dimension scores taken from the 综合评分 table, when there is one."""
    section = DIMENSION_TABLE_SECTION_RE.search(report)
    if not section:
        return {}
    tail = report[section.end():]
    stop = re.search(r"^##\s", tail, re.M)
    if stop:
        tail = tail[:stop.start()]
    scores: dict[str, float] = {}
    for line in tail.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip().strip("*").strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        key = DIMENSION_LABELS.get(cells[0])
        if key is None or key in scores:
            continue
        if not PLAIN_NUMBER_RE.match(cells[1]):
            continue
        scores[key] = float(cells[1])
    return scores


def report_grade_words(report: str) -> list[str]:
    """Grade words stated as a grade, in a report's conclusion anchors.

    Only the headline of the one-line conclusion and bolded grade labels
    (``**健康等级**：``) are read. Adjectives (``盈利能力优秀``), comparatives
    (``近优秀``), peer-comparison tables and numeric ranges are deliberately
    ignored so the check has no false positives.
    """
    lines = report.splitlines()
    words: list[str] = []
    start = next((i for i, line in enumerate(lines)
                  if re.match(r"^##\s*一句话结论", line)), None)
    if start is None:
        headline = next((line for line in lines[:6] if line.strip()), "")
    else:
        headline = ""
        for line in lines[start + 1:]:
            if re.match(r"^##\s", line):
                break
            if line.strip():
                headline = line
                break
    if headline and not headline.lstrip().startswith(("|", "#", ">")):
        head = GRADE_WORD_HEAD_RE.match(GRADE_PREFIX_RE.sub("", headline))
        if head:
            words.append(head.group(1))
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(("|", "#")):
            continue
        for match in GRADE_LABEL_RE.finditer(line):
            head = GRADE_WORD_HEAD_RE.match(GRADE_PREFIX_RE.sub("", line[match.end():]))
            if head:
                words.append(head.group(1))
    return words


def grade_for(score: float) -> str:
    return next(grade for threshold, grade in GRADE_THRESHOLDS if score >= threshold)


def audit_repository(root: Path) -> dict:
    root = root.resolve()
    catalog = root / "docs" / "companies.json"
    items = json.loads(catalog.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        raise ValueError("docs/companies.json must be a JSON array")
    issues: list[dict] = []
    stats = Counter()
    file_owners: dict[str, list[str]] = defaultdict(list)

    def issue(level: str, code: str, company: str, detail: str) -> None:
        issues.append({"level": level, "code": code, "company": company, "detail": detail})

    archive_by_target: dict[Path, list[Path]] = defaultdict(list)
    company_dir = root / "company"
    for path in company_dir.rglob("*"):
        if path.is_symlink():
            if not path.exists():
                issue("error", "broken_archive_symlink", str(path.relative_to(root)),
                      f"target={path.readlink()}")
            else:
                archive_by_target[path.resolve()].append(path)

    seen_ids = set()
    for index, c in enumerate(items):
        if not isinstance(c, dict):
            issue("error", "malformed_record", f"record-{index}", "Not a JSON object")
            continue
        cid = str(c.get("id", f"record-{index}"))
        name = str(c.get("name", cid))
        missing = EXPECTED_FIELDS - set(c)
        if missing:
            issue("error", "missing_fields", name, ", ".join(sorted(missing)))
            continue
        if cid in seen_ids:
            issue("error", "duplicate_id", name, cid)
        seen_ids.add(cid)

        dimensions = c.get("scores")
        if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSION_WEIGHTS):
            issue("error", "invalid_dimensions", name, "Expected five canonical camelCase keys")
            continue
        if any(type(dimensions[k]) not in (int, float)
               or not 0 <= dimensions[k] <= 100 for k in DIMENSION_WEIGHTS):
            issue("error", "score_out_of_range", name, repr(dimensions))
            continue
        total = c.get("total")
        if type(total) not in (int, float) or not 0 <= total <= 100:
            issue("error", "invalid_total", name, repr(total))
            continue

        calculated = sum(dimensions[k] * w for k, w in DIMENSION_WEIGHTS.items())
        # Stored dimensions have already been rounded; compare generously.
        # Round before comparing: 78 vs 77.45 is 0.5499999999999972 under
        # CPython 3.12 (compensated sum) and 0.55000000000001 under 3.11
        # (plain sum), so the raw comparison flips across Python versions.
        if round(abs(calculated - total), 6) > 0.55:
            issue("warning", "total_precision_drift", name,
                  f"catalog={total}; from rounded dimensions={calculated:.2f}")
        if c["grade"] != grade_for(total):
            issue("warning", "grade_boundary_ambiguity", name,
                  f"catalog={c['grade']}; displayed total={total} => {grade_for(total)}")

        for kind in ("report", "radar"):
            filename = c[kind]
            if not isinstance(filename, str) or Path(filename).name != filename:
                issue("error", "unsafe_filename", name, f"{kind}={filename!r}")
                continue
            artifact = root / "docs" / "examples" / filename
            if not artifact.is_file():
                issue("error", f"missing_{kind}", name, filename)
                continue
            file_owners[f"{kind}:{filename}"].append(name)
            archived = archive_by_target.get(artifact.resolve(), [])
            matches = [p for p in archived if len(p.relative_to(company_dir).parts) == 4
                       and p.relative_to(company_dir).parts[:2]
                       == (c["ind1"], c["ind2"])]
            if not matches:
                issue("warning", "archive_classification_drift", name,
                      f"{kind}: not linked under {c['ind1']}/{c['ind2']}")
            if kind == "report":
                try:
                    report = artifact.read_text(encoding="utf-8")
                except UnicodeError:
                    issue("error", "report_encoding", name, filename)
                    continue
                stats["reports_checked"] += 1
                if len(report.encode("utf-8")) < 3000:
                    stats["short_reports"] += 1
                if not re.search(r"https?://", report):
                    stats["reports_without_direct_url"] += 1
                for title, value in HEADER_RE.findall(report):
                    key = next((k for k, labels in HEADING_LABELS.items()
                                if any(label in title for label in labels)), None)
                    if key and abs(float(value) - dimensions[key]) > 1.05:
                        issue("warning", "report_score_drift", name,
                              f"{key}: report={value}, catalog={dimensions[key]}")
                if not HEADER_RE.search(report):
                    for key, value in dimension_table_scores(report).items():
                        if abs(value - dimensions[key]) > 1.05:
                            issue("warning", "report_score_drift", name,
                                  f"{key}: report table={value}, catalog={dimensions[key]}")
                expected_label = GRADE_LABELS.get(str(c.get("grade")))
                if expected_label:
                    stated = sorted(set(report_grade_words(report)) - {expected_label})
                    if stated:
                        issue("warning", "report_grade_word_differs_from_catalog", name,
                              f"catalog={c['grade']}({expected_label}); report states "
                              + "/".join(stated))

    for artifact, names in file_owners.items():
        if len(set(names)) > 1:
            issue("warning", "shared_artifact", ", ".join(names), artifact)

    counts = Counter(x["level"] for x in issues)
    return {
        "company_count": len(items),
        "industry_count": len({c.get("ind1") for c in items if isinstance(c, dict)}),
        "subindustry_count": len({(c.get("ind1"), c.get("ind2"))
                                 for c in items if isinstance(c, dict)}),
        "errors": counts["error"],
        "warnings": counts["warning"],
        "statistics": dict(stats),
        "issues": sorted(issues, key=lambda x: (x["level"] != "error", x["code"], x["company"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--baseline", type=Path,
                        help="Allow known historical warning identities, but fail on new warnings")
    args = parser.parse_args()
    result = audit_repository(args.root)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Companies: {result['company_count']} | "
              f"Industries: {result['industry_count']} | "
              f"Errors: {result['errors']} | Warnings: {result['warnings']}")
        print("Statistics:", json.dumps(result["statistics"], ensure_ascii=False))
        for problem in result["issues"]:
            print(f"  [{problem['level'].upper()}] {problem['code']}: "
                  f"{problem['company']} — {problem['detail']}")
    new_warnings = []
    if args.baseline is not None:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        if not isinstance(baseline, list):
            raise ValueError("Warning baseline must be an array")
        # Include the warning detail so score changes at the same company
        # cannot silently inherit an old warning's allowance.
        allowed = {(x["code"], x["company"], x["detail"]) for x in baseline}
        current = {(x["code"], x["company"], x["detail"]) for x in result["issues"]
                   if x["level"] == "warning"}
        new_warnings = sorted(current - allowed)
        print(f"Baseline: {len(current & allowed)} known, "
              f"{len(new_warnings)} unexpected, {len(allowed - current)} resolved")
        for code, company, detail in new_warnings:
            print(f"  [NEW WARNING] {code}: {company} — {detail}")
    return int(result["errors"] > 0 or (args.strict and result["warnings"] > 0)
               or bool(new_warnings))


if __name__ == "__main__":
    raise SystemExit(main())
