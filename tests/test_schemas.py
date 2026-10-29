"""Validate all four schemas and all 230 existing catalog records."""
import importlib.util
import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


class SchemaTests(unittest.TestCase):
    def test_schema_documents(self):
        for path in sorted(SCHEMAS.glob("*.schema.json")):
            with self.subTest(schema=path.name):
                Draft202012Validator.check_schema(json.loads(path.read_text()))

    def test_catalog_records(self):
        schema = json.loads((SCHEMAS / "company.schema.json").read_text())
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        catalog = json.loads((ROOT / "docs/companies.json").read_text())
        self.assertEqual(len(catalog), 230)
        for company in catalog:
            with self.subTest(company=company["id"]):
                self.assertEqual(list(validator.iter_errors(company)), [])

    def test_synthetic_snapshot_matches_schema(self):
        spec = importlib.util.spec_from_file_location("factory", ROOT / "tools/create_evaluation.py")
        factory = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(factory)
        from test_create_evaluation import fixture
        snapshot = factory.calculate_snapshot(fixture())
        schema = json.loads((SCHEMAS / "evaluation.schema.json").read_text())
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(snapshot)), [])
        evidence = json.loads((SCHEMAS / "evidence.schema.json").read_text())
        for doc in snapshot["payload"]["sources"]:
            self.assertEqual(list(Draft202012Validator(evidence).iter_errors(doc)), [])


if __name__ == "__main__":
    unittest.main()
