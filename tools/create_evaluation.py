#!/usr/bin/env python3
"""Create deterministic, cited, review-required company evaluations from v1 inputs.

This does NOT fetch evidence or verify sources. It rejects missing indicators
rather than treating unknown information as financial distress.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / ".claude/skills/company-health-eval/scripts/score.py"
DIMENSIONS = {
    "cash_flow": ("operating_cf", "cash_runway", "debt_level", "cf_to_ni_ratio"),
    "profitability": ("gross_margin", "net_margin", "revenue_growth", "rd_ratio", "revenue_per_head"),
    "debt": ("debt_to_assets", "interest_bearing_debt", "current_ratio", "cash_ratio", "pledge_ratio"),
    "operations": ("receivable_turnover", "customer_concentration", "employee_trend", "executive_stability"),
    "sustainability": ("market_growth", "tech_moat", "diversification", "capital_support", "policy_risk"),
}
LEVELS_3 = {"healthy", "warning", "danger"}
LEVELS_4 = {"excellent", "good", "average", "alert"}
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
EVIDENCE_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def fail(message: str) -> None:
    raise ValueError(message)


def canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def check_date(value: object, field: str) -> None:
    try:
        if not isinstance(value, str):
            raise TypeError("date must be a string")
        date.fromisoformat(value)
    except (TypeError, ValueError):
        fail(f"{field} requires ISO date YYYY-MM-DD")


def validate_input(data: dict) -> None:
    if not isinstance(data, dict):
        fail("Input must be a JSON object")
    fields = {"company_id", "as_of_date", "rubric_version", "score_input", "sources", "indicator_evidence"}
    if set(data) != fields:
        fail("Top-level fields mismatch")
    if not isinstance(data["company_id"], str) or not ID_RE.fullmatch(data["company_id"]):
        fail("Invalid company_id")
    check_date(data["as_of_date"], "as_of_date")
    if data["rubric_version"] != "financial-health-v1":
        fail("Unsupported rubric_version")
    sources = data["sources"]
    if not isinstance(sources, list) or not sources:
        fail("At least one source is required")
    ids = set()
    required = {"evidence_id", "source_url", "publisher", "retrieved_at", "document_sha256", "reporting_period"}
    extras = {"published_at", "document_locator", "page", "classification"}
    for source in sources:
        if not isinstance(source, dict) or required - set(source) or set(source) - (required | extras):
            fail("Malformed source fields")
        sid = source["evidence_id"]
        if not isinstance(sid, str) or not EVIDENCE_RE.fullmatch(sid) or sid in ids:
            fail("Invalid or repeated evidence_id")
        ids.add(sid)
        url = source["source_url"]
        parsed = urlparse(url) if isinstance(url, str) else None
        if parsed is None or parsed.scheme != "https" or not parsed.hostname:
            fail("Sources require an absolute HTTPS URL")
        if not isinstance(source["publisher"], str) or not source["publisher"].strip():
            fail("Publisher required")
        if not isinstance(source["reporting_period"], str) or not source["reporting_period"].strip():
            fail("Reporting period required")
        if not isinstance(source["document_sha256"], str) or not SHA_RE.fullmatch(source["document_sha256"]):
            fail("Document SHA256 required")
        check_date(source["retrieved_at"], "retrieved_at")
        if source.get("published_at") is not None:
            check_date(source["published_at"], "published_at")
        if "page" in source and (type(source["page"]) is not int or source["page"] < 1):
            fail("Page must be a positive integer")
        if "classification" in source and source["classification"] not in (
            "primary", "secondary", "user_supplied", "unknown"
        ):
            fail("Invalid source classification")
    raw = data["score_input"]
    links = data["indicator_evidence"]
    if not isinstance(raw, dict) or set(raw) != {"company", *DIMENSIONS}:
        fail("score_input must include company and all five dimensions")
    if not isinstance(raw["company"], str) or not raw["company"].strip():
        fail("Company name required")
    if not isinstance(links, dict) or set(links) != set(DIMENSIONS):
        fail("indicator_evidence must include all dimensions")
    for dimension, keys in DIMENSIONS.items():
        indicators = raw[dimension]
        references = links[dimension]
        if not isinstance(indicators, dict) or not isinstance(references, dict):
            fail(f"{dimension}: expects objects")
        expected = set(keys)
        bonus = dimension == "debt" and "bonus_zero_debt_tax_a" in indicators
        if bonus:
            if type(indicators["bonus_zero_debt_tax_a"]) is not bool:
                fail("Bonus must be boolean")
            if indicators["bonus_zero_debt_tax_a"]:
                expected.add("bonus_zero_debt_tax_a")
        if set(indicators) - {"bonus_zero_debt_tax_a"} != set(keys):
            fail(f"{dimension}: missing or unknown indicators")
        if set(references) != expected:
            fail(f"{dimension}: every scored indicator needs evidence references")
        for key in keys:
            options = LEVELS_4 if dimension == "profitability" else LEVELS_3
            if not isinstance(indicators[key], str) or indicators[key] not in options:
                fail(f"{dimension}.{key}: invalid level")
        for key, citations in references.items():
            if not isinstance(citations, list) or not citations or any(
                not isinstance(x, str) or x not in ids for x in citations
            ):
                fail(f"{dimension}.{key}: unsupported/empty evidence reference")


def calculate_snapshot(data: dict) -> dict:
    validate_input(data)
    spec = importlib.util.spec_from_file_location("company_score_v1", ENGINE_PATH)
    if spec is None or spec.loader is None:
        fail("Cannot load v1 scoring engine")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = module.calculate(data["score_input"])
    input_hash = digest(canonical(data))
    return {
        "schema_version": "1.0",
        "evaluation_id": data["company_id"] + "-" + input_hash[:16],
        "company_id": data["company_id"],
        "as_of_date": data["as_of_date"],
        "rubric_version": data["rubric_version"],
        "verification_status": "requires_human_review",
        "input_sha256": input_hash,
        "engine_sha256": digest(ENGINE_PATH.read_bytes()),
        "citation_link_coverage": 1.0,
        "payload": data,
        "score_result": output,
    }


def save_snapshot(snapshot: dict, output_root: Path) -> Path:
    dest = output_root / snapshot["company_id"] / (snapshot["evaluation_id"] + ".json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    if dest.exists() and dest.read_text(encoding="utf-8") != content:
        fail(f"Immutable evaluation conflict at {dest}")
    if not dest.exists():
        dest.write_text(content, encoding="utf-8")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-root", type=Path, default=ROOT / "data/evaluations")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    snapshot = calculate_snapshot(payload)
    if not args.dry_run:
        print(save_snapshot(snapshot, args.output_root))
    print(json.dumps({
        "evaluation_id": snapshot["evaluation_id"],
        "score": snapshot["score_result"]["total_score"],
        "grade": snapshot["score_result"]["grade"],
        "verification_status": snapshot["verification_status"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
