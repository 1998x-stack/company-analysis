# Quality foundation

This folder establishes read-only regression checks for the existing company
research catalog. It does not change historical risk ratings or the evaluation
methodology. See docs/ARCHITECTURE_V2.md for proposed future architecture.

## Commands

Fastest path — `make check` runs every gate exactly as CI does:

    make check          # unit + frontend + audit + materials + determinism
    make test           # unit + frontend only
    make audit          # repository audit against the warning baseline
    make materials      # material verifier against the review baseline
    make determinism    # ledgers must be byte-identical for identical input
    make readme         # regenerate the README tables from the catalog

Individual commands:

- python3 -m unittest discover -s tests -p "test_*.py" -v
- node --test tests/frontend.test.mjs
- python3 tools/audit_repository.py --baseline docs/audit_warning_baseline.json
- python3 tools/verify_company_materials.py --baseline docs/material_review_baseline.json \
      --output build/company_materials.json
- python3 tools/audit_repository.py --format json
- python3 tools/audit_repository.py --strict

`--strict` treats warnings as failures and therefore fails today on the 20
frozen legacy warnings; `--baseline` is the supported CI gate.

## Dependencies

Python tests need `jsonschema`, `pypdf`, `Pillow` and `matplotlib`
(see `requirements-dev.txt`). The frontend tests need Node 20+ but no browser
or frontend dependencies.

## Test layout

| File | Guards |
|---|---|
| `test_data_contract.py` | catalog/report/archive integrity, report grade words, score tables |
| `test_audit_negative.py` | every audit issue code, by breaking one thing at a time in a temp tree |
| `test_constant_consistency.py` | grade thresholds, labels and dimension weights across engine/audit/publisher/frontend |
| `test_cli_exit_codes.py` | CLI exit codes for the audit, ledger `--check` modes and material verifier |
| `test_company_materials.py` | material verifier output vs its baseline |
| `test_render_readme.py` | README tables are generated from the catalog and every generated link resolves |
| `test_legacy_golden.py` (via `golden_catalog_v1.json`) | 14 historical score records must not drift |
| `frontend.test.mjs` | Markdown renderer, sanitising, routing titles, sidebar order, report cache |

Golden fixtures and the two baselines are historical allowances, not approvals:
new warnings or new material conflicts must be fixed, not registered.
