# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Company financial health evaluation reports using a structured 5-dimension framework (cash flow quality 45%, profitability 20%, debt solvency 15%, operational efficiency 10%, sustainability 10%). Produces scored reports in Chinese with radar chart visualizations.

Reports live in `docs/examples/`. Methodology docs live in `docs/企业健康度评估体系/`.

## Core Workflow

When asked to evaluate a company (`/company-health-eval`):

1. **Research (parallel)** — launch 5 Explore subagents in one message, all `run_in_background: true`, covering: company basics & funding, revenue & financials, employees & labor, industry benchmarks & competitors, policy & risk. Do not search serially.
2. **Score** — apply the 5-dimension rubric from `.claude/skills/company-health-eval/SKILL.md`.
3. **Generate radar chart** — write `/tmp/radar_input.json` (English labels only), run `python3 .claude/skills/company-health-eval/scripts/radar_chart.py --data /tmp/radar_input.json --output docs/examples/<company_en>_health_radar.png`. Embed into report at section 三.
4. **Write report** — save to `docs/examples/<公司名>-财务健康评估-YYYY-MM-DD.md`.

## Radar Chart Script

```
python3 .claude/skills/company-health-eval/scripts/radar_chart.py --data /tmp/radar_input.json --output docs/examples/<name>.png
```

Requires matplotlib. All chart labels are English (avoids CJK font issues). Filename supports Chinese characters. JSON keys: `company`, `scores` (5 dimensions), `weights`, `total_score`, `grade` (one of Excellent/Moderate-High/Moderate/Moderate-Low/High-Risk).

## Git Workflow

**Commit after every completed report or skill change.** Never batch unrelated work into one commit. Format:

```
feat: evaluate <company name> with radar chart
```

Push to `origin/master` after each commit. Remote: `github.com/1998x-stack/company-analysis` (private).
