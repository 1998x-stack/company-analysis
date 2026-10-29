import hashlib,importlib.util,tempfile,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("workflow",ROOT/"tools/run_research_pipeline.py")
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
from test_create_evaluation import fixture
class WorkflowTests(unittest.TestCase):
    def make_job(self,root):
        data=fixture();document=root/"source.txt"
        document.write_text("Synthetic test financial information for parsing only.",encoding="utf-8")
        data["sources"][0]["document_sha256"]=hashlib.sha256(document.read_bytes()).hexdigest()
        company={"id":data["company_id"],"name":"Synthetic Test","nameEn":"Synthetic",
                 "ind1":"Testing","ind2":"Synthetic"}
        return {"evaluation_input":data,"source_files":{"fixture-source":str(document)},"company_record":company}
    def test_idempotent_run_to_review_and_publication_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);db=w.connect(root/"tasks.sqlite");store=root/"store"
            job=self.make_job(root);key=w.enqueue(db,job)
            self.assertEqual(w.enqueue(db,job),key)
            self.assertEqual(w.run_to_review(db,key,store),"review_required")
            self.assertEqual(w.row(db,key)["state"],"review_required")
            with self.assertRaisesRegex(ValueError,"Human approval"):
                w.stage(db,key,root/"site")
            meta=json.loads(w.row(db,key)["artifacts_json"])
            snap=json.loads(Path(meta["snapshot_path"]).read_text())
            approval={"evaluation_id":snap["evaluation_id"],"input_sha256":snap["input_sha256"],
                      "engine_sha256":snap["engine_sha256"],"decision":"approve",
                      "reviewer":"Unit Tester","approved_at":"2026-10-29"}
            self.assertEqual(w.approve(db,key,approval),"approved")
            manifest=w.stage(db,key,root/"site")
            self.assertEqual(manifest["status"],"staged_not_deployed")
            self.assertEqual(w.row(db,key)["state"],"staged")
            self.assertTrue((root/"site/index.html").is_file())
            db.close()
    def test_failure_and_retry_budget(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);db=w.connect(root/"tasks.sqlite")
            job=self.make_job(root);key=w.enqueue(db,job)
            (root/"source.txt").unlink()
            with self.assertRaises(FileNotFoundError):
                w.advance(db,key,root/"store")
            self.assertEqual(w.row(db,key)["state"],"failed")
            w.retry(db,key)
            self.assertEqual(w.row(db,key)["state"],"queued")
            db.close()
if __name__=="__main__":unittest.main()
