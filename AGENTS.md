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

## New evidence-linked evaluations

Run tools/create_evaluation.py with complete cited indicator assessments; it always emits requires_human_review and never publishes automatically. See docs/EVALUATION_INPUT_CONTRACT.md.

## Required checks

    make check

`make check` is the single entry point and runs exactly what CI runs:

    python3 -m unittest discover -s tests -p "test_*.py" -v
    node --test tests/frontend.test.mjs
    python3 tools/audit_repository.py --baseline docs/audit_warning_baseline.json
    python3 tools/verify_company_materials.py --baseline docs/material_review_baseline.json \
        --output build/company_materials.json
    python3 tools/backfill_evidence.py --output build/legacy_evidence_manifest.json
    python3 tools/reproduce_scores.py --output build/legacy_score_reproduction.json

The audit intentionally reports legacy warnings. Review warning deltas on each
PR: new warnings should not be introduced without an explicit explanation.
Do not turn off checks to make CI pass.

## Agent research pipeline (target, not present implementation)

DISCOVER -> COLLECT -> EXTRACT -> VERIFY -> NORMALIZE -> SCORE -> REVIEW
-> REPORT -> PUBLISH -> MONITOR

Store evidence references, source dates and retrieval timestamps, track
contradictions, and separate unknown/unavailable data from actual risk.

## Research factory stages

- S01: tools/backfill_evidence.py builds the 230-entry evidence gap ledger.
- S02: tools/reproduce_scores.py diagnoses legacy score drift;
  tools/replay_evaluations.py exactly replays NEW persisted inputs.
- S03: tools/publish_factory.py builds staged sites only after review.
- S04: tools/sector_scoring_v2.py is exploratory and NOT deployed to rankings.
- S05: tools/run_research_pipeline.py runs a checkpointed local workflow.
- Optional tools/collect_sources.py network access requires an explicit
  allowlisted HTTPS host and --allow-network. Source retrieval is NOT claim validation.
- Gate tooling: tools/audit_repository.py (catalog/report/archive integrity),
  tools/verify_company_materials.py (per-artifact hashes, image references,
  report score/date conflicts, orphan assets) and tools/radar_geometry.py
  (radar geometry vs catalog scores, used by the material verifier).
- Baselines are historical allowances, not approvals:
  docs/audit_warning_baseline.json (20 legacy audit warnings) and
  docs/material_review_baseline.json (2 legacy material conflicts). A new
  warning or conflict must be fixed, not registered.

The automated CI uploads two temporary, machine-readable research quality
ledgers. Do not commit downloaded copyrighted PDFs or personalized materials
into this public repository. Never mark a candidate source as verified.

## Done means

- Unit and regression tests are green.
- Every added catalog asset exists and has the expected provenance.
- Reports, scores, industry links, visualizations and website data agree.
- All newly researched claims link to dated, identifiable primary evidence.
- PR explains impact, migration, known limitations and a rollback path.
