import importlib.util,tempfile,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"tools"/path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
pub=load("publish_factory.py","publication")
sc=load("create_evaluation.py","scoring_factory")
from test_create_evaluation import fixture
class PublishTests(unittest.TestCase):
    def setUp(self):
        self.snapshot=sc.calculate_snapshot(fixture())
        self.approval={"evaluation_id":self.snapshot["evaluation_id"],
                       "input_sha256":self.snapshot["input_sha256"],
                       "engine_sha256":self.snapshot["engine_sha256"],
                       "reviewer":"Unit test reviewer","decision":"approve",
                       "approved_at":"2026-10-29"}
        self.company={"id":"unit-test-company","name":"Synthetic Example","nameEn":"Example",
                      "ind1":"Enterprise Services","ind2":"Testing"}
    def test_requires_review(self):
        a=dict(self.approval);a["decision"]="reject"
        with self.assertRaisesRegex(ValueError,"approval"):
            pub.check_approval(self.snapshot,a)
    def test_hash_mismatch(self):
        a=dict(self.approval);a["input_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"hash mismatch"):
            pub.check_approval(self.snapshot,a)
    def test_build_full_static_site(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/"site"
            result=pub.publish(self.snapshot,self.approval,self.company,dest)
            self.assertEqual(result["companies"],231)
            self.assertTrue((dest/"index.html").exists())
            self.assertTrue((dest/"docs/examples"/result["report"]).exists())
            self.assertTrue((dest/"docs/examples"/result["radar"]).exists())
            self.assertTrue((dest/"company/index.md").exists())
            self.assertIn("requires",self.snapshot["verification_status"])
            with self.assertRaises(FileExistsError):
                pub.publish(self.snapshot,self.approval,self.company,dest)
if __name__=="__main__":unittest.main()
