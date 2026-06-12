#!/usr/bin/env python3
"""Standardized 5-dimension scoring engine for company health evaluation.

Translates qualitative indicator assessments into deterministic 0-100 scores
using the framework defined in SKILL.md. Each indicator's rubric level is
mapped to a fixed point value — no subjective "base minus deduction" logic.

Usage:
  python3 score.py --data /tmp/score_input.json
  python3 score.py --data /tmp/score_input.json --output /tmp/score_result.json
"""

import argparse
import json
import sys

# -- Indicator-to-score mappings ------------------------------------

# 3-tier: healthy / warning / danger
# danger=15 not 0 — even worst measurable indicators get a floor above zero
LEVEL_3 = {"healthy": 90, "warning": 55, "danger": 15}

# 4-tier: excellent / good / average / alert
LEVEL_4 = {"excellent": 95, "good": 75, "average": 50, "alert": 15}

# Special 4-tier for 研发费用率 (non-linear — 10-25% is ideal)
LEVEL_RD = {"excellent": 95, "good": 70, "average": 50, "alert": 15}

# -- Dimension scoring functions ------------------------------------

def score_cash_flow(d: dict) -> float:
    """4 indicators × 25% each. receivable_turnover lives in operations only."""
    w = {"operating_cf": 0.25, "cash_runway": 0.25,
         "debt_level": 0.25, "cf_to_ni_ratio": 0.25}
    return _weighted(d, w, {k: LEVEL_3 for k in w})


def score_profitability(d: dict) -> float:
    """5 indicators × 20% each. rd_ratio uses special LEVEL_RD scale."""
    w = {"gross_margin": 0.20, "net_margin": 0.20,
         "revenue_growth": 0.20, "rd_ratio": 0.20,
         "revenue_per_head": 0.20}
    return _weighted(d, w, {
        "gross_margin": LEVEL_4, "net_margin": LEVEL_4,
        "revenue_growth": LEVEL_4, "rd_ratio": LEVEL_RD,
        "revenue_per_head": LEVEL_4,
    })


def score_debt(d: dict) -> float:
    """5 indicators × 20% each + bonus for zero interest debt + tax A-grade."""
    w = {"debt_to_assets": 0.20, "interest_bearing_debt": 0.20,
         "current_ratio": 0.20, "cash_ratio": 0.20, "pledge_ratio": 0.20}
    base = _weighted(d, w, {k: LEVEL_3 for k in w})
    if d.get("bonus_zero_debt_tax_a", False):
        base = min(base + 5, 100)
    return base


def score_operations(d: dict) -> float:
    """4 indicators × 25% each."""
    w = {"receivable_turnover": 0.25, "customer_concentration": 0.25,
         "employee_trend": 0.25, "executive_stability": 0.25}
    return _weighted(d, w, {k: LEVEL_3 for k in w})


def score_sustainability(d: dict) -> float:
    """5 indicators × 20% each."""
    w = {"market_growth": 0.20, "tech_moat": 0.20, "diversification": 0.20,
         "capital_support": 0.20, "policy_risk": 0.20}
    return _weighted(d, w, {k: LEVEL_3 for k in w})


# -- Helpers --------------------------------------------------------

def _weighted(d: dict, weights: dict, level_maps: dict) -> float:
    """Weighted average. Redistributes weight of missing indicators."""
    total, used_weight = 0.0, 0.0
    for key, weight in weights.items():
        entry = d.get(key)
        if entry is None:
            continue
        if not isinstance(entry, str):
            continue
        level_map = level_maps.get(key, LEVEL_3)
        if entry not in level_map:
            valid = list(level_map.keys())
            print(f"WARNING: '{entry}' is not a valid level for '{key}' (expected: {valid})",
                  file=sys.stderr)
            continue
        total += level_map[entry] * weight
        used_weight += weight
    if used_weight == 0:
        return 0.0
    return round(total / used_weight, 1)


# -- Grade ----------------------------------------------------------

def get_grade(score: float) -> dict:
    """Return English grade key + Chinese display label in one call."""
    if score >= 85:
        return {"grade": "Excellent", "grade_label": "优秀"}
    if score >= 70:
        return {"grade": "Moderate-High", "grade_label": "中等偏上"}
    if score >= 55:
        return {"grade": "Moderate", "grade_label": "中等"}
    if score >= 40:
        return {"grade": "Moderate-Low", "grade_label": "中等偏下"}
    return {"grade": "High-Risk", "grade_label": "高风险"}


# -- Main entry point -----------------------------------------------

WEIGHTS = {
    "Cash Flow Quality": 0.45,
    "Profitability": 0.20,
    "Debt Solvency": 0.15,
    "Operational Efficiency": 0.10,
    "Sustainability": 0.10,
}


def _safe_dim(data: dict, key: str) -> dict:
    """Return dimension dict or empty dict if key is missing or null."""
    val = data.get(key) if isinstance(data, dict) else None
    return val if isinstance(val, dict) else {}


def calculate(input_data: dict) -> dict:
    """Compute all dimension scores and weighted total from input data."""
    if not isinstance(input_data, dict):
        raise TypeError(f"Input must be a JSON object, got {type(input_data).__name__}")

    dims = {
        "Cash Flow Quality": score_cash_flow(_safe_dim(input_data, "cash_flow")),
        "Profitability": score_profitability(_safe_dim(input_data, "profitability")),
        "Debt Solvency": score_debt(_safe_dim(input_data, "debt")),
        "Operational Efficiency": score_operations(_safe_dim(input_data, "operations")),
        "Sustainability": score_sustainability(_safe_dim(input_data, "sustainability")),
    }

    dims = {k: max(v, 15.0) for k, v in dims.items()}

    total = sum(dims[name] * WEIGHTS[name] for name in dims)
    total = round(total, 1)

    grade_info = get_grade(total)

    return {
        "company": input_data.get("company", "Unknown"),
        "scores": dims,
        "weights": WEIGHTS,
        "total_score": total,
        "grade": grade_info["grade"],
        "grade_label": grade_info["grade_label"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Standardized company health scoring engine")
    parser.add_argument("--data", required=True, help="Path to JSON input file")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    with open(args.data) as f:
        input_data = json.load(f)

    result = calculate(input_data)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Score result → {args.output}")

    # Always print summary
    print(f"\n{'='*50}")
    print(f"  {result['company']}")
    print(f"{'='*50}")
    for dim, score in result["scores"].items():
        weight = result["weights"][dim]
        weighted = round(score * weight, 1)
        print(f"  {dim:30s}  {score:5.1f} × {weight:.0%} = {weighted:5.1f}")
    print(f"  {'─'*48}")
    print(f"  {'Total':30s}  {result['total_score']:5.1f} / 100")
    print(f"  {'Grade':30s}  {result['grade_label']} ({result['grade']})")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
