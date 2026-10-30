"""Cross-file consistency: the same scoring facts are duplicated across the
engine, the audits, the publisher and the front end. These tests keep them
in lock-step without changing any published score."""
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCORE = load(".claude/skills/company-health-eval/scripts/score.py", "health_score")
AUDIT = load("tools/audit_repository.py", "repository_audit")
REPRODUCE = load("tools/reproduce_scores.py", "score_reproduction")
PUBLISH = load("tools/publish_factory.py", "publication")
RADAR = load("tools/radar_geometry.py", "radar_geometry")


class GradeThresholdConsistencyTests(unittest.TestCase):
    def test_grade_thresholds_agree_everywhere(self):
        self.assertEqual(AUDIT.GRADE_THRESHOLDS, tuple(REPRODUCE.THRESHOLDS))
        for score in (0, 39, 40, 54, 55, 69, 70, 84, 85, 100):
            self.assertEqual(AUDIT.grade_for(score), REPRODUCE.grade(score))
            self.assertEqual(AUDIT.grade_for(score), SCORE.get_grade(score)["grade"], score)

    def test_grade_labels_agree_everywhere(self):
        engine = {SCORE.get_grade(score)["grade"]: SCORE.get_grade(score)["grade_label"]
                  for score in (100, 80, 60, 45, 10)}
        self.assertEqual(engine, AUDIT.GRADE_LABELS)
        self.assertEqual(PUBLISH.LABEL, AUDIT.GRADE_LABELS)

    def test_catalog_grade_labels_match_the_engine(self):
        for c in json.loads((ROOT / "docs/companies.json").read_text(encoding="utf-8")):
            self.assertEqual(c["gradeLabel"], AUDIT.GRADE_LABELS[c["grade"]], c["id"])


class DimensionConsistencyTests(unittest.TestCase):
    def test_weights_agree_everywhere(self):
        self.assertEqual(AUDIT.DIMENSION_WEIGHTS, REPRODUCE.WEIGHTS)
        engine = {PUBLISH.MAP[key]: weight for key, weight in SCORE.WEIGHTS.items()}
        self.assertEqual(engine, AUDIT.DIMENSION_WEIGHTS)

    def test_dimension_order_and_keys_agree_in_the_front_end(self):
        script = (ROOT / "index.html").read_text(encoding="utf-8")
        block = re.search(r"const DIMS = \[(.*?)\];", script, re.S).group(1)
        keys = re.findall(r'key:"([a-zA-Z]+)"', block)
        weights = re.findall(r'weight:"(\d+)%"', block)
        self.assertEqual(tuple(keys), RADAR.DIMENSIONS)
        self.assertEqual(tuple(PUBLISH.MAP.values()), RADAR.DIMENSIONS)
        self.assertEqual({k: int(w) / 100 for k, w in zip(keys, weights)},
                         AUDIT.DIMENSION_WEIGHTS)

    def test_front_end_grade_colour_maps_cover_every_grade(self):
        script = (ROOT / "index.html").read_text(encoding="utf-8")
        for name in ("GRADE_COLORS", "CARD_GRADE_CLS"):
            block = re.search(rf"const {name} = \{{(.*?)\n\}};", script, re.S).group(1)
            for grade in AUDIT.GRADE_LABELS:
                self.assertIn(f'"{grade}"', block, f"{name} misses {grade}")


if __name__ == "__main__":
    unittest.main()
