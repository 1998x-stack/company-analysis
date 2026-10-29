# Stage 05: Checkpointed, human-gated Research Workflow

Implemented: local SQLite queue with deterministic job id, persisted transitions,
source SHA256 validation, PDF/HTML/TXT parsing, v1 rubric evaluation, explicit
review/approval gate, offline static publication and bounded retries.

Commands (example shapes):
- python3 tools/run_research_pipeline.py enqueue --input path/to/job.json
- python3 tools/run_research_pipeline.py run --id RUN_ID
- python3 tools/run_research_pipeline.py status --id RUN_ID
- python3 tools/run_research_pipeline.py approve --id RUN_ID --approval receipt.json
- python3 tools/run_research_pipeline.py publish --id RUN_ID --out /tmp/site

A job contains evaluation_input (the strict v1 contract), company_record, and
source_files mapping each evidence ID to a LOCAL file. No claims are invented.
The pipeline validates document hashes, parses text and computes a deterministic
snapshot from supplied indicator levels, then stops for human review.
The verification gate attests inputs; it cannot prove source content is true.
The optional source_collector.fetch helper implements explicitly allowlisted
HTTPS retrieval with DNS/IP checking, redirect refusal, byte and media limits.
It is not invoked automatically by default. PDF parsing uses optional pypdf.

This is a working single-host orchestration MVP, NOT a multi-agent LLM
autonomous research service. Real extraction-to-indicator classification,
fact-checking, multi-source conflicts, distributed scheduling and automatic
source discovery require separate audited adapters and a golden evaluation set.
