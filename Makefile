# Single entry point for the checks AGENTS.md requires.
# Usage: make check        (all gates, same commands CI runs)
#        make test         (fast: unit + frontend)
#        make ledgers      (regenerate the research ledgers into build/)
.PHONY: check test test-py test-node audit materials readme ledgers determinism clean

check: test audit materials readme-check determinism

test: test-py test-node

test-py:
	python3 -m unittest discover -s tests -p "test_*.py" -v

test-node:
	node --test tests/frontend.test.mjs

audit:
	python3 tools/audit_repository.py --baseline docs/audit_warning_baseline.json

materials:
	python3 tools/verify_company_materials.py --baseline docs/material_review_baseline.json --output build/company_materials.json

# The README tables are generated from the catalog; never hand-edit them.
readme:
	python3 tools/render_readme.py --write

readme-check:
	python3 tools/render_readme.py --check

ledgers:
	mkdir -p build
	python3 tools/backfill_evidence.py --output build/legacy_evidence_manifest.json
	python3 tools/reproduce_scores.py --output build/legacy_score_reproduction.json

# Same input must produce identical bytes; catches dict ordering/timestamp drift.
determinism: ledgers
	python3 tools/backfill_evidence.py --output build/legacy_evidence_manifest.repeat.json
	python3 tools/reproduce_scores.py --output build/legacy_score_reproduction.repeat.json
	cmp build/legacy_evidence_manifest.json build/legacy_evidence_manifest.repeat.json
	cmp build/legacy_score_reproduction.json build/legacy_score_reproduction.repeat.json

clean:
	rm -rf build
