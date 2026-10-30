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

    def test_warning_baseline_covers_all_remaining_legacy_flags(self):
        import json
        baseline = json.loads((ROOT / "docs/audit_warning_baseline.json").read_text())
        allowed = {(x["code"], x["company"], x["detail"]) for x in baseline}
        current = {(x["code"], x["company"], x["detail"]) for x in self.result["issues"]
                   if x["level"] == "warning"}
        self.assertFalse(current - allowed, f"New warnings: {current - allowed}")


if __name__ == "__main__":
    unittest.main()


class ReportGradeWordTests(unittest.TestCase):
    """The catalog grade label and the report's own grade statement must agree."""

    def test_headline_grade_statement_is_detected(self):
        md = "# X 财务健康评估（2026-06-12）\n\n## 一句话结论\n\n⚫ **高风险（44/100）** | 亏损\n"
        self.assertEqual(audit.report_grade_words(md), ["高风险"])

    def test_bolded_label_grade_statement_is_detected(self):
        md = "## 三、综合\n\n**健康等级**：🟠 **中等（Moderate）** — 说明\n"
        self.assertEqual(audit.report_grade_words(md), ["中等"])
        md = "## 三、综合\n\n**评级：🟠 中等（68, 边界）** — 说明\n"
        self.assertEqual(audit.report_grade_words(md), ["中等"])

    def test_adjectives_comparatives_and_tables_are_not_grades(self):
        # "近优秀" is a qualifier on 中等偏上, not a grade of its own.
        self.assertEqual(audit.report_grade_words("**评级：🟡 中等偏上（近优秀）** — 工控龙头"),
                         ["中等偏上"])
        for text in (
            "**健康等级**：🔴 **中等偏下** — 盈利能力优秀但现金流差",
            "| 2025综合得分 | **85 🟢 优秀** | 待评估 | 89 🟢 优秀 |",
            "> 注：综合得分84分在70-85的「中等偏上」区间高位，接近「优秀」等级门槛。",
            "> **更新说明**：取代此前基于FY2024数据的旧版（55分/中等偏下）。",
            "**小结**：AAA类信用评级使融资成本低，偿债能力中等。",
        ):
            self.assertNotIn("优秀", audit.report_grade_words(text), text)
            self.assertLessEqual(len(audit.report_grade_words(text)), 1, text)

    def test_no_catalog_report_states_a_conflicting_grade(self):
        result = audit.audit_repository(ROOT)
        conflicting = [x for x in result["issues"]
                       if x["code"] == "report_grade_word_differs_from_catalog"]
        self.assertEqual(conflicting, [], f"Grade statements conflict: {conflicting[:5]}")


class DimensionTableTests(unittest.TestCase):
    """Dimension scores must be readable even when a report has no ### headings."""

    TABLE = (
        "## 三、综合评分\n\n"
        "| 维度 | 得分 | 权重 | 加权 |\n|------|:----:|:----:|:----:|\n"
        "| 现金流质量 | 55.0 | 45% | 24.8 |\n| 盈利能力 | 50.0 | 20% | 10.0 |\n"
        "| 偿债能力 | 62.0 | 15% | 9.3 |\n| 运营效率 | 72.0 | 10% | 7.2 |\n"
        "| 可持续发展 | 76.0 | 10% | 7.6 |\n| **综合** | **59** | 100% | 58.9 |\n\n"
        "## 四、核心风险\n\n1. 无关内容\n"
    )

    def test_score_table_is_parsed(self):
        self.assertEqual(audit.dimension_table_scores(self.TABLE), {
            "cashFlow": 55.0, "profitability": 50.0, "debt": 62.0,
            "operations": 72.0, "sustainability": 76.0})

    def test_pipe_summary_rows_are_not_mistaken_for_dimensions(self):
        md = ("## 三、综合\n\n"
              "| 15|45%=6.8 | 41|20%=8.2 | 15|15%=2.2 | 54|10%=5.4 | 31|10%=3.1 | **26** |\n")
        self.assertEqual(audit.dimension_table_scores(md), {})

    def test_section_without_table_yields_nothing(self):
        self.assertEqual(audit.dimension_table_scores("## 三、综合评分\n\n数据有限\n"), {})

    def test_no_catalog_report_drifts_from_its_score_table(self):
        result = audit.audit_repository(ROOT)
        drift = [x for x in result["issues"] if x["code"] == "report_score_drift"]
        self.assertEqual(drift, [], f"Report tables disagree with catalog: {drift[:5]}")
