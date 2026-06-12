# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Company financial health evaluation reports using a structured 5-dimension framework (cash flow quality 45%, profitability 20%, debt solvency 15%, operational efficiency 10%, sustainability 10%). Produces scored reports in Chinese with radar chart visualizations.

Reports live in `docs/examples/`. Methodology docs live in `docs/企业健康度评估体系/`. Reports are indexed by industry under `company/` via a two-level classification tree with symlinks — see `company/README.md` and `company/index.md`.

## Core Workflow

When asked to evaluate a company (`/company-health-eval`):

1. **Research (parallel)** — launch 5 Explore subagents in one message, all `run_in_background: true`, covering: company basics & funding, revenue & financials, employees & labor, industry benchmarks & competitors, policy & risk. Do not search serially.
2. **Score** — use the standardized engine. Create `/tmp/score_input.json` with indicator levels per the rubric in `.claude/skills/company-health-eval/SKILL.md`, then run `python3 .claude/skills/company-health-eval/scripts/score.py --data /tmp/score_input.json`. Never score subjectively ("base N minus deductions"). All dimension scores come from this script.
3. **Generate radar chart** — use the score.py output JSON directly: `python3 .claude/skills/company-health-eval/scripts/radar_chart.py --data /tmp/score_output.json --output docs/examples/<company_en>_health_radar.png`. Embed into report at section 三.
4. **Write report** — save to `docs/examples/<公司名>-财务健康评估-YYYY-MM-DD.md`. The dimension scores and total in the report must exactly match the engine output.
5. **Archive to company/ tree** — create `company/<一级行业>/<二级行业>/<公司名>/`, symlink the `.md` report and `.png` radar chart into it. Relative symlink target: `../../../../docs/examples/<file>`. See `company/README.md` for existing classifications. New industries get new directories.
6. **Update data files** — after the report is written: (a) append entry to `docs/companies.json` with short camelCase score keys, (b) update `company/index.md` ranking table, stats, and industry sections, (c) update `company/README.md` classification table sorted by score. See "Data File Consistency" section below for exact key mapping and verification.

## Scoring Engine

```
python3 .claude/skills/company-health-eval/scripts/score.py --data /tmp/score_input.json
```

Standardized engine documented in `.claude/skills/company-health-eval/ALGORITHM.md`. Indicator levels map to fixed scores: 3-tier (healthy=90, warning=55, danger=15), 4-tier (excellent=95, good=75, average=50, alert=15). All 5 dimensions use `_weighted()` with explicit per-indicator weights. Missing indicators auto-skipped with weight redistribution. Unrecognized level strings warn to stderr. Empty dimensions floor at 15 (same as all-danger — "we don't know" is not worse than "we know and it's terrible"). No manual score adjustments allowed.

## Radar Chart Script

```
python3 .claude/skills/company-health-eval/scripts/radar_chart.py --data /tmp/score_output.json --output docs/examples/<name>.png
```

Feed it the score.py output JSON directly (has `company`, `scores`, `weights`, `total_score`, `grade`, `grade_label`). Requires matplotlib. All chart labels are English (avoids CJK font issues). Filename supports Chinese characters.

## Data File Consistency (critical — read before changing scores)

Scores flow through 5+ layers. Any engine or indicator change requires updating ALL of them. A single mismatch (e.g., wrong JSON key) silently breaks the web UI for all companies.

### Score key mapping

The scoring engine outputs long English keys. `companies.json` must use short camelCase keys for `index.html`:

| Engine output | companies.json |
|---------------|---------------|
| `Cash Flow Quality` | `cashFlow` |
| `Profitability` | `profitability` |
| `Debt Solvency` | `debt` |
| `Operational Efficiency` | `operations` |
| `Sustainability` | `sustainability` |

If `companies.json` uses the long keys, `index.html` reads `undefined` for every dimension — score bars break, grade colors break, comparison radar breaks. This bug survived multiple commits before detection.

### Verification script (run after any score change)

```bash
python3 -c "
import json, os, re, subprocess

# 1. Rescore all companies through engine
for fname in sorted(os.listdir('/tmp/score_inputs')):
    subprocess.run(['python3','.claude/skills/company-health-eval/scripts/score.py',
                   '--data',f'/tmp/score_inputs/{fname}',
                   '--output',f'/tmp/score_outputs/{fname}'], capture_output=True)

# 2. Cross-check companies.json ↔ engine
with open('docs/companies.json') as f:
    companies = json.load(f)
KEY_MAP = {'Cash Flow Quality':'cashFlow','Profitability':'profitability',
           'Debt Solvency':'debt','Operational Efficiency':'operations',
           'Sustainability':'sustainability'}
for c in companies:
    with open(f'/tmp/score_outputs/{c[\"id\"]}.json') as f:
        e = json.load(f)
    assert round(e['total_score']) == c['total'], f\"{c['name']}: JSON={c['total']} engine={round(e['total_score'])}\"
    for ek, ev in e['scores'].items():
        assert int(ev) == c['scores'][KEY_MAP[ek]], f\"{c['name']} {ek}: JSON={c['scores'][KEY_MAP[ek]]} engine={int(ev)}\"

# 3. Cross-check report markdowns ↔ engine
for path, cid in report_map.items():
    with open(path) as f:
        content = f.read()
    with open(f'/tmp/score_outputs/{cid}.json') as f:
        e = json.load(f)
    # Check dimension headers: ### N. 维度名（X/100）
    for cn_pat, ek in dim_patterns:
        m = re.search(rf'### \\d+\\. {cn_pat}（(\\d+)/100）', content)
        assert m and int(m.group(1)) == int(e['scores'][ek])
    # Check total row: | **综合得分** | **X/100** |
    m = re.search(r'\\*\\*综合得分\\*\\*\\s*\\|\\s*\\*?\\*?(\\d+)/100', content)
    assert m and int(m.group(1)) == round(e['total_score'])

print('All layers consistent.')
"
```

### Layers that must agree after any scoring change

| # | Layer | Check |
|---|-------|-------|
| 1 | `score.py` engine | Run on all 20+ input files, zero warnings |
| 2 | `docs/companies.json` | Total + 5 dimension scores per company match engine |
| 3 | 20 report markdowns | Dimension headers, score table, one-liner match engine |
| 4 | 20 radar PNGs | Regenerated from engine output JSON |
| 5 | `company/index.md` | Ranking table + industry section scores match JSON |
| 6 | `company/README.md` | Classification table scores match JSON, sorted desc |
| 7 | `company/` symlinks | 2 per company (report + radar), 40+ total |

### Common failure modes

- **Key mismatch**: engine has `"Cash Flow Quality"` but JSON has `"cashFlow"` — all scores `undefined` in UI
- **int() truncation**: `int(78.9)` = 78 but `round(78.9)` = 79 — always use `round()` for display scores
- **Stale radar PNGs**: scores changed but chart not regenerated — visual doesn't match numbers
- **Report format variants**: some reports use `可持续发展` others `可持续发展能力` — regex patterns must handle both
- **External modifications**: `index.md` and `README.md` may be edited by other tools; always read before writing

## Git Workflow

**Commit after every completed report or skill change.** Never batch unrelated work into one commit. Format:

```
feat: evaluate <company name> with radar chart
```

Push to `origin/master` after each commit. Remote: `github.com/1998x-stack/company-analysis` (private).
