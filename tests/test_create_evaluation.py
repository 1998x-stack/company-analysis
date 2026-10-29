"""Only synthetic fixture data is used; it never represents verified company facts."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("factory_eval", ROOT / "tools/create_evaluation.py")
factory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(factory)


def fixture():
    tiers = {dim: {key: ("good" if dim == "profitability" else "healthy") for key in keys}
            for dim, keys in factory.DIMENSIONS.items()}
    refs = {dim: {key: ["fixture-source"] for key in keys}
            for dim, keys in factory.DIMENSIONS.items()}
    return {
        "company_id": "unit-test-company",
        "as_of_date": "2026-08-14",
        "rubric_version": "financial-health-v1",
        "score_input": {"company": "Synthetic Test", **tiers},
        "sources": [{
            "evidence_id": "fixture-source",
            "source_url": "https://example.com/test-only",
            "publisher": "Synthetic Fixture",
            "retrieved_at": "2026-08-14",
            "reporting_period": "unit-test-2025",
            "document_sha256": "0" * 64,
        }],
        "indicator_evidence": refs,
    }


class NewEvaluationTests(unittest.TestCase):
    def test_fully_linked_snapshot_is_review_required(self):
        result = factory.calculate_snapshot(fixture())
        self.assertEqual(result["verification_status"], "requires_human_review")
        self.assertEqual(result["citation_link_coverage"], 1.0)
        self.assertEqual(result["score_result"]["company"], "Synthetic Test")

    def test_determinism_and_immutable_file(self):
        a, b = factory.calculate_snapshot(fixture()), factory.calculate_snapshot(fixture())
        self.assertEqual(a, b)
        with tempfile.TemporaryDirectory() as path:
            dest = factory.save_snapshot(a, Path(path))
            self.assertEqual(dest, factory.save_snapshot(b, Path(path)))
            self.assertEqual(json.loads(dest.read_text())["evaluation_id"], a["evaluation_id"])

    def test_missing_indicator_rejected(self):
        data = fixture()
        del data["score_input"]["cash_flow"]["cash_runway"]
        with self.assertRaisesRegex(ValueError, "missing or unknown"):
            factory.calculate_snapshot(data)

    def test_missing_citation_rejected(self):
        data = fixture()
        data["indicator_evidence"]["debt"]["cash_ratio"] = []
        with self.assertRaisesRegex(ValueError, "unsupported/empty"):
            factory.calculate_snapshot(data)

    def test_unsafe_url_rejected(self):
        data = fixture()
        data["sources"][0]["source_url"] = "file:///etc/passwd"
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            factory.calculate_snapshot(data)

    def test_unapproved_publication_flag_rejected(self):
        data = fixture()
        data["publication_status"] = "published"
        with self.assertRaisesRegex(ValueError, "Top-level fields"):
            factory.calculate_snapshot(data)

    def test_repeated_evidence_id_rejected(self):
        data = fixture()
        data["sources"].append(dict(data["sources"][0]))
        with self.assertRaisesRegex(ValueError, "repeated"):
            factory.calculate_snapshot(data)

    def test_bonus_evidence_is_required(self):
        data = fixture()
        data["score_input"]["debt"]["bonus_zero_debt_tax_a"] = True
        with self.assertRaisesRegex(ValueError, "every scored indicator"):
            factory.calculate_snapshot(data)
        data["indicator_evidence"]["debt"]["bonus_zero_debt_tax_a"] = ["fixture-source"]
        self.assertEqual(factory.calculate_snapshot(data)["score_result"]["scores"]["Debt Solvency"], 95)


if __name__ == "__main__":
    unittest.main()
