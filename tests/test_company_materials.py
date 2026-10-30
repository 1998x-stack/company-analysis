import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_company_materials import build


class CompanyMaterialsTests(unittest.TestCase):
    def test_every_catalog_company_has_a_material_result(self):
        catalog = json.loads((ROOT / "docs/companies.json").read_text(encoding="utf-8"))
        result = build(ROOT)
        rows = result["records"]
        self.assertEqual(len(rows), len(catalog))
        self.assertEqual({row["company_id"] for row in rows}, {company["id"] for company in catalog})
        self.assertTrue(all((ROOT / row["report"]["path"]).is_file() and
                            (ROOT / row["radar"]["path"]).is_file() and
                            row["radar"]["format_valid"] for row in rows))

    def test_report_internal_references_and_claim_conflicts_are_visible(self):
        result = build(ROOT)
        rows = {row["name"]: row for row in result["records"]}
        self.assertEqual(rows["江波龙"]["structural_errors"], [])
        self.assertEqual(sum(bool(row["structural_errors"]) for row in rows.values()), 0)
        self.assertIn("report_heading_date_differs_from_filename", rows["复星医药"]["review_flags"])
        # 金雅福集团 and 中集车辆 were repaired against their own weighted tables,
        # so a future regression must show up as a brand-new conflict again.
        for name in ("金雅福集团", "中集车辆"):
            self.assertEqual([flag for flag in rows[name]["review_flags"]
                              if flag == "report_conclusion_score_differs_from_catalog"], [])
        self.assertIn("radar_geometry_differs_from_catalog", rows["阳光保险"]["review_flags"])
        self.assertEqual(sum(row["radar"]["geometry"]["status"] == "geometry_matches_catalog"
                             for row in rows.values()), 229)
        baseline = json.loads((ROOT / "docs/material_review_baseline.json").read_text(encoding="utf-8"))
        self.assertEqual({(item["company_id"], item["code"], item["detail"])
                          for item in result["review_issues"]},
                         {(item["company_id"], item["code"], item["detail"])
                          for item in baseline})


if __name__ == "__main__":
    unittest.main()
