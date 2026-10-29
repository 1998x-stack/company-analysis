# Implementation and Acceptance — 2026-10-29

Branch: feat/research-factory-stages-1-5
PR: https://github.com/1998x-stack/company-analysis/pull/3

## Scope and verified results

The five research stages now have runnable MVP implementations and tests,
not merely architecture documents. GitHub Actions has run Python+Node tests,
repository audit, and two 230-company ledger generators.

Coverage from the real repository snapshot:
- Companies inventoried: 230 / 230
- Historical reports with no direct HTTP(S) URL: 227
- Reports shorter than 3KB: 111
- Companies with curated official source *candidates*: 3
- Historical score flags: 11 boundary + 10 precision
- Historical input rubrics recovered: 0 (not present in repository)
- Independent historical source/page checks completed: 0
- New evaluation deterministic replay: implemented + tested with synthetic inputs
- Industry scoring rubrics: 4 experimental sectors (not calibrated)
- Staged publication: working synthetic integration test, no auto deployment
- Pipeline: idempotent SQLite workflow + hash checking + local parser + approval
- External source retrieval: opt-in HTTPS allowlist helper, not automatic discovery

## Acceptance matrix

| Stage | Software MVP | Full real-data objective |
|---|---|---|
| S01 Evidence backfill | Implemented: 230-item ledger, URL/period hints, source candidate registry | OPEN: verified source and page-level citations for 230 |
| S02 Score reproduction | Implemented: interval diagnostics and exact replay for new inputs | OPEN: recover original 23-tier rubric inputs for historic reports |
| S03 Publishing Factory | Implemented: review-gated deterministic staged static website | OPEN: validated live production publishing and release rollback |
| S04 Sector scoring v2 | Implemented: 4 configurable provisional rubrics, ablation and missing-data gates | OPEN: empirical calibration, peer cohorts, public backtest |
| S05 Research Pipeline | Implemented: local SQLite state machine, source hashing, parser, scoring, review | OPEN: autonomous discovery, claim extraction/contradictions, LLM judge benchmarks |

## Design protection

No historical score, grade or claims were modified. Historical 21 audit warnings
stay visible and frozen as explicit baseline, and CI prevents new warnings.
Source candidate discovery must never be mislabeled verified. The current
pipeline cannot establish claim truth from a document hash alone. Human approval
of a stage does not substitute for a regulatory financial audit.

The static deployment and new schema/rubric should be reviewed before use for
employment, finance or investment decisions. No investment recommendations
are produced by these tools.

## Next necessary evidence steps

1. Batch-collect primary annual reports from official authorized sites.
2. Save document content hashes, page anchors and indicator-to-source mappings.
3. Independently verify claims and recover legacy rubric inputs; rerun exact checks.
4. Establish sector peer baselines with no forward-data leakage; run backtests.
5. Extend SQLite engine with controlled extractor and cross-checker adapters,
   human review, release approval, and deployment rollback.

This report tracks software completion separately from unavailable real-world
evidence. Never claim all historic companies are fact-checked based on CI alone.
