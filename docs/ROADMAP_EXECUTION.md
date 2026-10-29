# Execution Plan: Company Analysis Factory P0–P4

Status: ordered backlog. The quality-foundation PR is merged. PR #2 implements selected P0 repairs and
starts P1 contracts; later stages remain proposed until verified.

## P0 — Make the existing catalog trustworthy (next)

Tasks:
- Resolve the 31 baseline warnings with original evidence, never invented data.
- Correct the two-company Sunshine PNG collision by regenerating from each
  company's checked scores; store unique artifact_id rather than name.
- Normalize taxonomies and archive symlinks; preserve historical URL redirects.
- Keep score_v1 frozen and publish precise total alongside integer display.
- Repair report header score discrepancies, revalidate summary tables.
- Review public repository files for personal data and unsupported allegations.
- Stabilize quality gate: all new warnings fail CI after a warning allowlist.

Deliverables: repair manifest, no broken references, no new warning count,
reviewed PR and baseline test suite. Do not infer false data precision from
rounded catalog values.

## P1 — Evidence and scoring input contract

Tasks:
- Persist raw evidence snapshots with license-safe metadata and content hashes.
- Save indicator input JSON per evaluation (not in temporary directories).
- Create versioned JSON schemas for Company, Evidence, Observation, Evaluation.
- Preserve period/unit/currency/source/estimate flags for each financial value.
- Extract structured facts from documents, with page anchors and human review.
- Move ranking/industry/report index generation to one deterministic command.
- Add golden-fixture tests for at least 10 companies across sectors.

Success: every NEW evaluation has provenance, saved input, reproducible total,
grade and asset; zero manual table duplication. Legacy evaluations are marked
'unverified_v1' until backfilled, not silently treated as verified.

## P2 — Sector rubrics and methodological evaluation

Tasks:
- Decompose financial soundness, employer attractiveness and investment valuation.
- Design sector metrics for banks, insurers, biotech, SaaS, manufacturing,
  construction/real estate, government-backed research and early-stage AI.
- Separate evidence coverage from estimated enterprise quality.
- Validate percentile comparisons on aligned periods and peer populations.
- Run weight sensitivity/leave-one-factor-out ablations; compare to v1.
- Backtest against historic financial distress and discontinued operations with
  no forward-looking data leakage. Audit cohort imbalance.

Success: versioned v2 rubric with benchmark dataset, confidence/coverage scores,
disagreement analysis, ablation report and documented migration policy.

## P3 — Controlled agent research orchestration

Tasks:
- Use typed workflow states: queued, searching, extracting, verifying,
  scoring, review_required, published, failed.
- Tool contracts for filing search, document retrieval, metric extraction,
  citation resolution and contradiction detection.
- Key each run by company_id + as_of_date + rubric_version + source_hash.
- Add retries with backoff, idempotency, dead-letter queue and checkpointing.
- Separate automatic drafts from human-reviewed public outputs.
- Evaluate document-to-metric extraction precision/recall and citations.

Success: reproducible run manifests and failure recovery, demonstrated by an
offline corpus of golden reports and simulated source failures.

## P4 — Research interface and operations

Tasks:
- Separate frontend components; retain static deployment until server needed.
- Add search by sector/ticker, dynamic filtering, compare 2–5 companies,
  historical timelines, source drilldown and freshness indicators.
- Support export: JSON/CSV/Markdown; provide self-contained comparison views.
- Add accessible tables, responsive layouts and browser E2E checks.
- Add scheduled refresh policies dependent on report type, with data-source rate
  limits and evidence aging; avoid treating stale estimates as current.

Success: site performance and accessibility budgets, complete E2E flows,
transparent uncertainty display and no unsourced live-data claims.

## Target architecture dependency sequence

P0 integrity -> P1 evidence+schema -> P2 validated rubrics
             -> P3 agent workflow -> P4 interactive product.

The agent layer must not fabricate missing facts to satisfy completeness.
The user interface must always expose 'as of' and evidence coverage.
