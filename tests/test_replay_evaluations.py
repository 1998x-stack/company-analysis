import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("replayer",ROOT/"tools/replay_evaluations.py")
import sys
sys.path.insert(0,str(ROOT/"tools"))
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
from test_create_evaluation import fixture
from create_evaluation import calculate_snapshot
class ReplayTests(unittest.TestCase):
    def test_exact_replay(self):
        snap=calculate_snapshot(fixture())
        self.assertEqual(r.replay(snap)["status"],"exact_replay_verified")
    def test_modified_score_rejected(self):
        snap=calculate_snapshot(fixture())
        snap["score_result"]["total_score"]-=1
        with self.assertRaisesRegex(ValueError,"Score differs"):
            r.replay(snap)
    def test_modified_input_rejected(self):
        snap=calculate_snapshot(fixture())
        snap["payload"]["score_input"]["cash_flow"]["operating_cf"]="danger"
        with self.assertRaisesRegex(ValueError,"Input SHA256"):
            r.replay(snap)
    def test_changed_engine_rejected(self):
        snap=calculate_snapshot(fixture())
        snap["engine_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"Engine version"):
            r.replay(snap)
    def test_batch_with_valid_and_corrupted(self):
        snap=calculate_snapshot(fixture())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"valid.json").write_text(json.dumps(snap))
            (root/"invalid.json").write_text("{}")
            report=r.replay_dir(root)
            self.assertEqual((report["verified"],report["failed"]),(1,1))
if __name__=="__main__":unittest.main()
