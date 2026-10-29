import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("sector_v2",ROOT/"tools/sector_scoring_v2.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class SectorTests(unittest.TestCase):
    def test_four_rubrics_normalized(self):
        cfg=m.rubric();m.validate_config(cfg)
        self.assertEqual(set(cfg["sectors"]),{"bank","insurance","manufacturing","ai_startup"})
    def test_good_bad_direction(self):
        self.assertGreater(m.score_metric(0.14,0.13,0.075),
                           m.score_metric(0.08,0.13,0.075))
        self.assertGreater(m.score_metric(0.01,0.01,0.05),
                           m.score_metric(0.04,0.01,0.05))
    def test_all_missing_results_unscored(self):
        result=m.evaluate({"sector":"bank","metrics":{}})
        self.assertIsNone(result["score_experimental"])
        self.assertEqual(result["metric_coverage"],0)
    def test_evidence_required_for_observed_data(self):
        with self.assertRaisesRegex(ValueError,"evidence"):
            m.evaluate({"sector":"bank","metrics":{"npl_ratio":{"value":.02,"period":"2025-FY","evidence_ids":[]}}})
    def test_full_coverage_and_ablation(self):
        cfg=m.rubric()["sectors"]["bank"]["metrics"]
        metrics={k:{"value":d["good"],"period":"2025-FY","evidence_ids":["test"]}
                 for k,d in cfg.items()}
        r=m.evaluate({"sector":"bank","metrics":metrics})
        self.assertEqual(r["metric_coverage"],1)
        self.assertEqual(r["score_experimental"],90)
        self.assertEqual(len(r["sensitivity_leave_one_out"]),4)
        self.assertFalse(r["mixed_reporting_periods"])
    def test_missing_not_scored_as_bad(self):
        cfg=m.rubric()["sectors"]["insurance"]["metrics"]
        observed=list(cfg)[:2]
        metrics={k:{"value":cfg[k]["good"],"period":"2025-FY","evidence_ids":["s"]}
                 for k in observed}
        out=m.evaluate({"sector":"insurance","metrics":metrics})
        self.assertEqual(out["status"],"insufficient_coverage")
        self.assertIsNone(out["score_experimental"])
if __name__=="__main__":unittest.main()
