# Research Factory — Stages 01–05

This repository now has runnable **MVP implementations** of the five requested
stages. It does NOT have complete independently reviewed evidence for the
230 historical companies, calibrated multi-sector models, or a general-purpose
autonomous LLM researching service.

## 1. Evidence backfill
Run: python3 tools/backfill_evidence.py --output build/evidence.json
Result: one complete record per legacy company. Source URLs and reporting
period mentions are unverified textual candidates. Three official-source
leads are included; no new financial claims were inferred.

## 2. Score replay diagnostics
Run: python3 tools/reproduce_scores.py --output build/scores.json
Result: 230 records flagging 11 grade-boundary and 10 total precision anomalies.
None has original v1 indicator inputs; no reconstructed financial tier is
fabricated. Restore source inputs to enable exact replay.

## 3. Static publishing
Run tools/create_evaluation.py on evidence-linked fully populated input,
then tools/publish_factory.py with a matching, explicit human approval
receipt. The new package includes full legacy static assets, a versioned
report, SVG, ranking, sector catalog and companies.json. Original files are
never overwritten.

## 4. Sector v2 experiments
Run tools/sector_scoring_v2.py --input metrics.json.
Four prototype sector rubrics, interval scoring, evidence refs, minimum
coverage and leave-one-factor-out sensitivity are implemented.
Parameters are uncalibrated and cannot be promoted to production rankings
without benchmark validation.

## 5. Research pipeline
Run tools/run_research_pipeline.py enqueue --input job.json, then
run --id ID, status --id ID, approve --id ID --approval receipt.json,
publish --id ID --out /tmp/new-site.
Local SQLite persists state and retries. Original document hashes are
checked before parsing HTML/TXT/PDF; scoring is performed only on completely
supplied indicators. Human review is a mandatory publishing gate.

Optional network collection:
python3 tools/collect_sources.py --url https://example.com/report.pdf
--allowed-host example.com --allow-network --output-dir data/runtime/downloaded

Network collection downloads raw source files with limits and does not
automatically assert that any report statements are factual. Reuse and
redistribution of the source content are subject to the original license.

## CI
The Quality Gate runs all tests, repository integrity checks and a full
230-company ledger build. The two full ledgers are retained as workflow
artifacts and do not need to be committed to the public source repository.

## Remaining work (requires facts, data or human decisions)
- Verify source pages and original indicator assessments for 230 companies.
- Correct 21 historical precision/grade flags from verified inputs.
- Build an annotated financial extraction benchmark, evaluate false claims,
  tune sector thresholds, and run historical backtests.
- Integrate authorized live document search and LLM extractors with review;
  the current pipeline is local and sourced from user-provided documents.
