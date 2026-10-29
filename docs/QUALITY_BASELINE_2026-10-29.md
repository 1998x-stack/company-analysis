# Historical Quality Baseline — 2026-10-29

Commit under test: 77a5e613e78eadf20e1809388cb617c049234ce0
Branch: feat/company-analysis-quality-foundation
Base branch: master (dfa7c2911564ed974ee2edf454db035810655647)
Workflow: Quality Gate, initial PR run 40826530827 (passed).

## Inventory

- 230 JSON catalog records, 22 first-level industries.
- 230 canonical Markdown reports, 230 existing PNG files.
- 460 industry archive symbolic links.
- 12 Python unit/integrity tests passed; 4 Node frontend tests passed.
- New P0 auditor reported zero blocking errors and 31 warnings.

## Audit warning breakdown

| Check | Warnings |
|-------|---------:|
| Archive industry classification drift | 6 |
| Display-grade vs rounded-total ambiguity | 11 |
| Report header score differs from catalog | 3 |
| Reused radar chart basename | 1 |
| Composite score precision drift | 10 |
| TOTAL | 31 |

Additional research-quality indicators:
- 227 of 230 reports contain no direct HTTP/HTTPS URL.
- 111 of 230 reports are smaller than 3 KB.
These are triage signals, not proof every affected report is factually wrong.

## Known high-priority cases

- Longsys: case-sensitive missing image reference corrected in this branch.
- 崇达技术 and 阳光保险: both catalog records refer to Sunshine_health_radar.png.
  Regenerate the first from verified score JSON; do not copy the second image.
- Three report-vs-catalog dimension mismatches:
  欣旺达 (cash flow), 海王生物 (profitability),
  迈瑞医疗 (sustainability). Investigate original input before edits.
- Grade boundary conflicts at displayed 55, 70, 85 points should be resolved by
  publishing unrounded and rounded values with a single documented policy.
- Several industry archive locations conflict with catalog taxonomy.
- One report cited operational-efficiency weight 6% rather than the engine's 10%.

## Security and publishing notes

The repository is PUBLIC. The jobs JSONL contains personalized job matching
context. Audit it before republishing or broadening site exposure; avoid storing
personal employment information in public research fixtures. The scan found no
obvious credential-shaped strings in inspected memory and job files, which is
not equivalent to a complete security review.

## Baseline limitations

The checker does not verify source claims, whether PNG pixels match score JSON,
whether ranking formulas are causally useful, or whether an annual filing is
financially current. These require evidence ingestion, scoring-input retention,
and a reviewed methodological v2 migration.
