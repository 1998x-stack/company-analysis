"""Legacy regression fixtures pin display data; they do not prove financial facts."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GoldenCatalogTests(unittest.TestCase):
    def test_fourteen_cross_sector_records(self):
        catalog = {c["id"]: c for c in json.loads(
            (ROOT / "docs/companies.json").read_text(encoding="utf-8"))}
        gold = json.loads((ROOT / "tests/golden_catalog_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(len(gold), 14)
        for c in gold:
            with self.subTest(id=c["id"]):
                current = catalog[c["id"]]
                for key in ("name", "total", "grade", "scores", "radar"):
                    self.assertEqual(current[key], c[key])

    def test_chongda_radar_is_not_insurance_radar(self):
        catalog = json.loads((ROOT / "docs/companies.json").read_text(encoding="utf-8"))
        company = next(x for x in catalog if x["id"] == "sdgt")
        insurer = next(x for x in catalog if x["id"] == "sunshine_ins")
        self.assertNotEqual(company["radar"], insurer["radar"])
        svg = (ROOT / "docs/examples" / company["radar"]).read_text(encoding="utf-8")
        self.assertIn('data-company-id="sdgt"', svg)


if __name__ == "__main__":
    unittest.main()
