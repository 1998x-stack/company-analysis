#!/usr/bin/env python3
"""Regenerate the README tables from docs/companies.json.

The root README used to carry two 230-row tables that had to be edited by hand
whenever a score changed (see CLAUDE.md). They drifted: by 2026-10 the ranking
table still pointed 崇达技术 at the radar chart of a different company, and two
tickers were stale. The tables are now generated between markers and checked in
CI, so the catalog stays the single source of truth.

Usage:
    python3 tools/render_readme.py --write     # rewrite the marked blocks
    python3 tools/render_readme.py --check     # exit 1 if README is stale
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GRADE_EMOJI = {
    "优秀": "🟢",
    "中等偏上": "🟡",
    "中等": "🟠",
    "中等偏下": "🔴",
    "高风险": "⚫",
}

RANKING_BEGIN = "<!-- BEGIN GENERATED: RANKING (make readme) -->"
RANKING_END = "<!-- END GENERATED: RANKING -->"
DIMENSIONS_BEGIN = "<!-- BEGIN GENERATED: DIMENSIONS (make readme) -->"
DIMENSIONS_END = "<!-- END GENERATED: DIMENSIONS -->"

RANKING_HEADER = (
    "| # | 公司 | 行业 | 综合得分 | 等级 | 报告 | 雷达图 |\n"
    "|---|------|------|----------|------|------|--------|\n"
)
DIMENSIONS_HEADER = (
    "| 公司 | 现金流 (45%) | 盈利 (20%) | 偿债 (15%) | 运营 (10%) | 可持续 (10%) | 综合 |\n"
    "|---|---|---|---|---|---|---|\n"
)


# Parentheses and spaces terminate a Markdown link destination early, so one
# catalog file ("Sea Limited(Shopee)-…md") produced a dead link on GitHub.
MARKDOWN_ESCAPES = {"(": "%28", ")": "%29", " ": "%20", "#": "%23", "?": "%3F"}


def link_path(filename: str) -> str:
    return "".join(MARKDOWN_ESCAPES.get(char, char) for char in filename)


def display_name(company: dict) -> str:
    """Company name plus ticker, except for placeholder tickers like "—（非上市）"."""
    ticker = company.get("ticker") or ""
    return company["name"] + (f" ({ticker})" if ticker and not ticker.startswith("—") else "")


def ranked(catalog: list[dict]) -> list[dict]:
    return sorted(catalog, key=lambda c: (-c["total"], c["name"]))


def render_ranking(catalog: list[dict]) -> str:
    rows = [
        f"| {index} | {display_name(c)} | {c['ind1']} · {c['ind2']} | {c['total']} | "
        f"{GRADE_EMOJI[c['gradeLabel']]} | [报告](docs/examples/{link_path(c['report'])}) | "
        f"[PNG](docs/examples/{link_path(c['radar'])}) |"
        for index, c in enumerate(ranked(catalog), 1)
    ]
    return RANKING_HEADER + "\n".join(rows)


def render_dimensions(catalog: list[dict]) -> str:
    rows = [
        f"| {c['name']} | {c['scores']['cashFlow']} | {c['scores']['profitability']} | "
        f"{c['scores']['debt']} | {c['scores']['operations']} | "
        f"{c['scores']['sustainability']} | **{c['total']}** |"
        for c in ranked(catalog)
    ]
    return DIMENSIONS_HEADER + "\n".join(rows)


def _replace_block(text: str, begin: str, end: str, body: str) -> str:
    start = text.find(begin)
    stop = text.find(end)
    if start < 0 or stop < 0 or stop < start:
        raise ValueError(f"README is missing the generated block markers: {begin}")
    return text[: start + len(begin)] + "\n" + body + "\n" + text[stop:]


def render_readme(text: str, catalog: list[dict]) -> str:
    text = _replace_block(text, RANKING_BEGIN, RANKING_END, render_ranking(catalog))
    return _replace_block(text, DIMENSIONS_BEGIN, DIMENSIONS_END, render_dimensions(catalog))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="rewrite the generated blocks")
    group.add_argument("--check", action="store_true", help="fail if the blocks are stale")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    readme_path = args.root / "README.md"
    catalog = json.loads((args.root / "docs/companies.json").read_text(encoding="utf-8"))
    current = readme_path.read_text(encoding="utf-8")
    try:
        expected = render_readme(current, catalog)
    except ValueError as error:
        print(error)
        return 1
    if args.write:
        readme_path.write_text(expected, encoding="utf-8")
        print(f"README tables regenerated from {len(catalog)} catalog records")
        return 0
    if expected != current:
        print("README tables are stale; run: python3 tools/render_readme.py --write")
        return 1
    print(f"README tables match the catalog ({len(catalog)} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
