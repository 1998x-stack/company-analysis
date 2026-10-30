"""Full-population ledgers: do not invent historical evidence."""
import importlib.util,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    s=importlib.util.spec_from_file_location(name,ROOT/"tools"/name)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
backfill=load("backfill_evidence.py")
replay=load("reproduce_scores.py")
audit=load("audit_repository.py")
class LedgersTests(unittest.TestCase):
    def test_230_company_backfill(self):
        seeds=json.loads((ROOT/"data/source_candidates.json").read_text(encoding="utf-8"))
        result=backfill.build(ROOT,seeds)
        self.assertEqual(result["summary"]["companies"],230)
        self.assertEqual(result["summary"]["without_direct_urls"],227)
        self.assertEqual(result["summary"]["candidate_source_companies"],3)
        self.assertTrue(all(x["verification_status"]=="unverified_legacy_report"
                            and not x["original_score_input_available"]
                            and len(x["report_sha256"])==64 for x in result["records"]))
    def test_230_score_replay_requires_original_inputs(self):
        result=replay.build(ROOT)
        self.assertEqual(result["summary"]["companies"],230)
        self.assertEqual(result["summary"]["precision_drift"],9)
        self.assertEqual(result["summary"]["grade_boundary_ambiguous"],11)
        names={x["name"] for x in result["records"] if x["precision_drift"]}
        warnings={x["company"] for x in audit.audit_repository(ROOT)["issues"]
                  if x["code"]=="total_precision_drift"}
        self.assertEqual(names,warnings)
        self.assertTrue(all(x["reproduction_status"]=="needs_original_inputs"
                            for x in result["records"]))
    def test_no_candidate_is_fake_verified_filing(self):
        seeds=json.loads((ROOT/"data/source_candidates.json").read_text(encoding="utf-8"))
        for item in seeds:
            self.assertEqual(item["verification_status"],"candidate_only")
            self.assertTrue(item["url"].startswith("https://"))
if __name__=="__main__":unittest.main()
