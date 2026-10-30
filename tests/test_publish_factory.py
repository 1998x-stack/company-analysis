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
            # The site's #/method route reads this document from the staged tree.
            self.assertTrue((dest/"docs/企业健康度评估体系"/"00-评估框架总览.md").is_file())
            catalog=json.loads((dest/"docs/companies.json").read_text())
            new=next(c for c in catalog if c["id"]==self.company["id"])
            self.assertEqual(new["as_of_date"],self.snapshot["as_of_date"])
            self.assertEqual(new["rubric_version"],"financial-health-v1")
            self.assertEqual(new["total"],self.snapshot["score_result"]["total_score"])
            self.assertIn("requires",self.snapshot["verification_status"])
            with self.assertRaises(FileExistsError):
                pub.publish(self.snapshot,self.approval,self.company,dest)
    def test_existing_company_keeps_legacy_catalog_record(self):
        existing=json.loads((ROOT/"docs/companies.json").read_text())[0]
        data=fixture();data["company_id"]=existing["id"]
        snapshot=sc.calculate_snapshot(data)
        approval=dict(self.approval,evaluation_id=snapshot["evaluation_id"],
                      input_sha256=snapshot["input_sha256"],engine_sha256=snapshot["engine_sha256"])
        company=dict(self.company,id=existing["id"],name=existing["name"],
                     ind1=existing["ind1"],ind2=existing["ind2"])
        with tempfile.TemporaryDirectory() as d:
            result=pub.publish(snapshot,approval,company,Path(d)/"site")
            self.assertEqual(result["companies"],230)
            self.assertEqual(result["publication_kind"],"new_version")
            catalog=json.loads((Path(d)/"site/docs/companies.json").read_text())
            current=next(c for c in catalog if c["id"]==existing["id"])
            self.assertEqual({key:current[key] for key in existing},existing)
            self.assertEqual(current["evaluations"][0]["evaluation_id"],snapshot["evaluation_id"])
            self.assertTrue((Path(d)/"site/docs/examples"/result["report"]).is_file())
            self.assertTrue((Path(d)/"site/docs/material_review_baseline.json").is_file())
    def test_existing_company_identity_mismatch_is_rejected(self):
        existing=json.loads((ROOT/"docs/companies.json").read_text())[0]
        data=fixture();data["company_id"]=existing["id"]
        snapshot=sc.calculate_snapshot(data)
        approval=dict(self.approval,evaluation_id=snapshot["evaluation_id"],
                      input_sha256=snapshot["input_sha256"],engine_sha256=snapshot["engine_sha256"])
        company=dict(self.company,id=existing["id"])
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"identity"):
                pub.publish(snapshot,approval,company,Path(d)/"site")
    def test_modified_score_cannot_be_published_with_old_approval(self):
        snapshot=json.loads(json.dumps(self.snapshot))
        snapshot["score_result"]["total_score"]-=1
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"exact scoring replay"):
                pub.publish(snapshot,self.approval,self.company,Path(d)/"site")
if __name__=="__main__":unittest.main()
