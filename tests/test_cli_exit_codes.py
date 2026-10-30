"""CLI exit codes are the only thing CI enforces, so they must be proven to fail.

Every tool's ``main()`` is exercised in a subprocess against a temporary root so
that a broken gate cannot pass silently.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT):
    return subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True)


class AuditExitCodeTests(unittest.TestCase):
    def test_broken_catalog_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "docs").mkdir()
            (root / "docs/companies.json").write_text(json.dumps([{
                "id": "broken", "name": "Broken", "ind1": "I", "ind2": "S",
                "scores": {"cashFlow": 90, "profitability": 90, "debt": 90,
                           "operations": 90, "sustainability": 90},
                "total": 90, "grade": "Excellent",
                "report": "missing.md", "radar": "missing.png",
            }]), encoding="utf-8")
            result = run("tools/audit_repository.py", "--root", str(root))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("missing_report", result.stdout)

    def test_clean_repository_exits_zero_and_json_is_parseable(self):
        result = run("tools/audit_repository.py", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["errors"], 0)
        self.assertGreater(payload["company_count"], 0)


class LedgerCheckModeTests(unittest.TestCase):
    """``--check`` must report staleness instead of silently rewriting files."""

    def assert_check_mode(self, tool: str):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "ledger.json"
            missing = run(tool, "--check", "--output", str(out))
            self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
            self.assertIn("stale", missing.stdout.lower())

            generated = run(tool, "--output", str(out))
            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertTrue(out.is_file())

            fresh = run(tool, "--check", "--output", str(out))
            self.assertEqual(fresh.returncode, 0, fresh.stdout + fresh.stderr)

            out.write_text(out.read_text(encoding="utf-8") + " ", encoding="utf-8")
            tampered = run(tool, "--check", "--output", str(out))
            self.assertEqual(tampered.returncode, 1, tampered.stdout + tampered.stderr)

    def test_backfill_evidence_check_mode(self):
        self.assert_check_mode("tools/backfill_evidence.py")

    def test_reproduce_scores_check_mode(self):
        self.assert_check_mode("tools/reproduce_scores.py")


class MaterialsExitCodeTests(unittest.TestCase):
    def test_new_material_conflict_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / "materials.json"
            baseline = Path(d) / "baseline.json"
            baseline.write_text("[]", encoding="utf-8")  # allow nothing
            result = run("tools/verify_company_materials.py",
                         "--baseline", str(baseline), "--output", str(output))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("unexpected", result.stdout)


if __name__ == "__main__":
    unittest.main()
