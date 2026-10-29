# Stages 01–02: Evidence backfill and historical score diagnostics

These stages generate honest, complete machine-readable work queues for 230 legacy reports.
They never infer missing original financial indicator levels.

Commands:
- python3 tools/backfill_evidence.py
- python3 tools/reproduce_scores.py
- Append --check to verify that generated manifests are up to date.

Outputs: data/legacy_evidence_manifest.json and data/legacy_score_reproduction.json.

There are three curated official-source leads in data/source_candidates.json.
They are not downloaded, hashed or claim-verified. A URL in a report does not
prove its assertions. A reporting period mention is an extraction heuristic.

All historical scores retain needs_original_inputs. The precision interval
assumes the stored dimension ratings were rounded to nearest integer, which
is not necessarily true of every legacy report. Do not use it as recovered data.
