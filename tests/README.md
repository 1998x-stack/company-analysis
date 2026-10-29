# Quality foundation

This folder establishes read-only regression checks for the existing company
research catalog. It does not change historical risk ratings or the evaluation
methodology. See docs/ARCHITECTURE_V2.md for proposed future architecture.

## Commands

- python3 -m unittest discover -s tests -p "test_*.py" -v
- node --test tests/frontend.test.mjs
- python3 tools/audit_repository.py
- python3 tools/audit_repository.py --format json
- python3 tools/audit_repository.py --strict

Default audit mode fails only on fatal reference or schema errors. Legacy
warnings are displayed, not hidden. Strict mode is an explicit future gate.

The Python tests use the standard library. The frontend tests require Node 20+
but do not install browser or frontend dependencies.
