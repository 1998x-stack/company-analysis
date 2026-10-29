# Evidence-backed Evaluation Contract (v1)

This is an implemented CLI for **new, fully cited research inputs only**.
No missing source documents or rubric judgments are reconstructed for the 230
historical reports, which remain unverified legacy snapshots.

## Workflow

1. Collect permitted original documents and independently check their content.
2. Supply a stable company_id, as_of_date and rubric_version financial-health-v1.
3. Register each source with absolute HTTPS URL, publisher, retrieval date,
   reporting period and actual original-document SHA256.
4. Supply all 23 rubric indicator levels and their source evidence ID references.
5. Run a validation-only preview, then persist the deterministic snapshot.
6. Review the output before any publication.

Commands:

    python3 tools/create_evaluation.py --input path/to/input.json --dry-run
    python3 tools/create_evaluation.py --input path/to/input.json

Required input top-level fields: company_id, as_of_date, rubric_version,
sources, score_input, indicator_evidence.

The score_input field follows the existing
.claude/skills/company-health-eval/scripts/score_input_template.json structure,
with exactly four cash_flow indicators (not five). In indicator_evidence, each
dimension maps every assessed indicator to a non-empty list of registered
evidence_id strings. An optional enabled debt bonus must also be cited.

Output: data/evaluations/<company_id>/<evaluation_id>.json
where the evaluation ID depends on the canonical input SHA256. The output
records the frozen engine's SHA256 and always sets verification_status to
requires_human_review.

## Important constraints

- A linked source or document hash does **not** prove factual correctness.
  citation_link_coverage=1.0 describes reference completeness, not source truth.
- The factory refuses incomplete indicators rather than assigning unknowns a
  low financial health score. Partial research should remain an unpublished
  draft outside this scoring path.
- It does not fetch, scrape, validate, license, or publish raw evidence.
- It does not update existing rankings, the site, or old ratings.
- Do not commit private source documents, secrets or identifiable applicant
  information to this public repository.
