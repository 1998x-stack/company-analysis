"""Contract checks: the catalog must keep resolvable paths and stable identifiers."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repository_audit", ROOT / "tools/audit_repository.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class CatalogIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit.audit_repository(ROOT)

    def test_catalog_is_substantial(self):
        self.assertGreaterEqual(self.result["company_count"], 200)
        self.assertGreaterEqual(self.result["industry_count"], 20)

    def test_no_fatal_reference_errors(self):
        errors = [x for x in self.result["issues"] if x["level"] == "error"]
        self.assertEqual(errors, [], f"Fatal catalog errors: {errors[:10]}")

    def test_reports_processed(self):
        self.assertEqual(self.result["statistics"]["reports_checked"],
                         self.result["company_count"])

    def test_historical_warnings_are_reported_not_hidden(self):
        self.assertIn("warnings", self.result)
        self.assertIsInstance(self.result["issues"], list)


if __name__ == "__main__":
    unittest.main()
