# AGENTS.md — Company Analysis Factory contribution contract

Applies to AI coding agents and human contributors. The current site and catalog
are a public, historical research snapshot. Do not assume published figures are
current or independently verified.

## Repository map

- .claude/skills/company-health-eval/ — legacy v1 evaluation rubric
- .claude/skills/company-health-eval/scripts/score.py — v1 deterministic scoring
- .claude/skills/company-health-eval/scripts/radar_chart.py — radar renderer
- docs/companies.json — 230 catalog entries and static frontend data
- docs/examples/ — canonical Markdown reports and radar images
- company/ — industry-classified symlinks to canonical artifacts
- index.html — static website; no backend API
- tools/audit_repository.py — read-only consistency checker
- tests/ — Python score/catalog tests and Node frontend tests
- docs/ARCHITECTURE_V2.md — roadmap/RFC, not already implemented

## Change discipline

1. Work on a topic branch and propose a PR; do not push directly to master.
2. Record the branch base commit SHA before modifying data.
3. For any score update, save raw indicator input, evidence/period, engine
   version and output. Never adjust only a published total, grade or radar.
4. Company names, exchange tickers and legal entities are not interchangeable.
5. Avoid silently duplicating Markdown or PNGs; ensure referenced paths exist.
6. Keep existing v1 scores unchanged during v2 experimentation.
7. Research claims and rankings must label estimates, dates and uncertainty.
8. Do not commit secrets, private resumes, unpublished personal details or
   user-specific matching notes into a public repo.
9. Do not cite AI-produced summaries as independent confirmation.
10. If primary evidence is unavailable, state uncertainty rather than invent.

## Required checks

    python3 -m unittest discover -s tests -p "test_*.py" -v
    node --test tests/frontend.test.mjs
    python3 tools/audit_repository.py

The audit intentionally reports legacy warnings. Review warning deltas on each
PR: new warnings should not be introduced without an explicit explanation.
Do not turn off checks to make CI pass.

## Agent research pipeline (target, not present implementation)

DISCOVER -> COLLECT -> EXTRACT -> VERIFY -> NORMALIZE -> SCORE -> REVIEW
-> REPORT -> PUBLISH -> MONITOR

Store evidence references, source dates and retrieval timestamps, track
contradictions, and separate unknown/unavailable data from actual risk.

## Done means

- Unit and regression tests are green.
- Every added catalog asset exists and has the expected provenance.
- Reports, scores, industry links, visualizations and website data agree.
- All newly researched claims link to dated, identifiable primary evidence.
- PR explains impact, migration, known limitations and a rollback path.
