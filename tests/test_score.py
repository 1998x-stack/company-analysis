"""Deterministic regression tests for the existing v1 scoring engine."""
import importlib.util
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / ".claude/skills/company-health-eval/scripts/score.py"
SPEC = importlib.util.spec_from_file_location("company_score_engine", ENGINE)
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)


class ScoreEngineTests(unittest.TestCase):
    def test_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(score.WEIGHTS.values()), 1.0)

    def test_three_level_rubric(self):
        self.assertEqual(score.score_cash_flow({
            "operating_cf": "healthy", "cash_runway": "healthy",
            "debt_level": "healthy", "cf_to_ni_ratio": "healthy",
        }), 90)

    def test_four_level_and_rnd_rubric(self):
        self.assertEqual(score.score_profitability({
            "gross_margin": "excellent", "net_margin": "excellent",
            "revenue_growth": "excellent", "rd_ratio": "excellent",
            "revenue_per_head": "excellent",
        }), 95)

    def test_missing_indicators_are_redistributed(self):
        self.assertEqual(score.score_cash_flow({"operating_cf": "healthy"}), 90)

    def test_empty_dimensions_have_floor(self):
        result = score.calculate({"company": "Unknown"})
        self.assertEqual(result["total_score"], 15)
        self.assertTrue(all(x == 15 for x in result["scores"].values()))
        self.assertEqual(result["grade"], "High-Risk")

    def test_bonus_capped(self):
        debt = {k: "healthy" for k in (
            "debt_to_assets", "interest_bearing_debt", "current_ratio",
            "cash_ratio", "pledge_ratio")}
        debt["bonus_zero_debt_tax_a"] = True
        self.assertEqual(score.score_debt(debt), 95)

    def test_grade_boundaries(self):
        for value, expected in ((0, "High-Risk"), (40, "Moderate-Low"),
                                (55, "Moderate"), (70, "Moderate-High"),
                                (85, "Excellent"), (100, "Excellent")):
            with self.subTest(value=value):
                self.assertEqual(score.get_grade(value)["grade"], expected)

    def test_input_template_matches_scoring_engine(self):
        import json
        template_path = ENGINE.parent / "score_input_template.json"
        template = json.loads(template_path.read_text(encoding="utf-8"))
        self.assertEqual(set(template["cash_flow"]), {
            "operating_cf", "cash_runway", "debt_level", "cf_to_ni_ratio"
        })
        self.assertEqual(set(template["operations"]), {
            "receivable_turnover", "customer_concentration",
            "employee_trend", "executive_stability"
        })

    def test_invalid_top_level_input(self):
        with self.assertRaises(TypeError):
            score.calculate(["invalid"])


if __name__ == "__main__":
    unittest.main()
