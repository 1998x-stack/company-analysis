"""Negative coverage for every audit issue code.

The repository itself is clean, so running the audit against it never exercises
the failure branches. These tests build a minimal valid tree and then break one
thing at a time, so an inverted comparison or a wrong ``level`` cannot pass CI.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repository_audit", ROOT / "tools/audit_repository.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)
REPRO_SPEC = importlib.util.spec_from_file_location(
    "score_reproduction", ROOT / "tools/reproduce_scores.py")
audit_reproduction = importlib.util.module_from_spec(REPRO_SPEC)
REPRO_SPEC.loader.exec_module(audit_reproduction)

REPORT = "# Acme 财务健康评估（2026-01-01）\n\n## 一句话结论\n\n结论正文。\n"


def record(**overrides):
    base = {
        "id": "acme", "name": "Acme", "ind1": "I", "ind2": "S",
        "scores": {"cashFlow": 90, "profitability": 90, "debt": 90,
                   "operations": 90, "sustainability": 90},
        "total": 90, "grade": "Excellent",
        "report": "acme.md", "radar": "acme.png",
    }
    base.update(overrides)
    return base


class AuditNegativeTests(unittest.TestCase):
    def build(self, records, report=REPORT, link=True, extra=None):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        (root / "docs/examples").mkdir(parents=True)
        (root / "docs/companies.json").write_text(
            json.dumps(records, ensure_ascii=False), encoding="utf-8")
        (root / "docs/examples/acme.md").write_text(report, encoding="utf-8")
        (root / "docs/examples/acme.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        if link:
            for name in ("acme.md", "acme.png"):
                target = root / "company/I/S/Acme" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(f"../../../../docs/examples/{name}")
        if extra:
            extra(root)
        return root

    def codes(self, root):
        result = audit.audit_repository(root)
        return {issue["code"]: issue for issue in result["issues"]}

    def assert_code(self, records, code, level=None, **kwargs):
        root = self.build(records, **kwargs)
        codes = self.codes(root)
        self.assertIn(code, codes, f"expected {code}, got {sorted(codes)}")
        if level:
            self.assertEqual(codes[code]["level"], level)
        return codes

    # -- structural errors -------------------------------------------------
    def test_clean_tree_has_no_issues(self):
        self.assertEqual(self.codes(self.build([record()])), {})

    def test_malformed_record(self):
        self.assert_code(["not an object"], "malformed_record", "error")

    def test_missing_fields(self):
        broken = record()
        del broken["radar"]
        self.assert_code([broken], "missing_fields", "error")

    def test_duplicate_id(self):
        self.assert_code([record(), record(name="Acme 2")], "duplicate_id", "error")

    def test_invalid_dimensions(self):
        self.assert_code([record(scores={"cashFlow": 90})], "invalid_dimensions", "error")

    def test_score_out_of_range(self):
        scores = record()["scores"]
        scores["debt"] = 140
        self.assert_code([record(scores=scores)], "score_out_of_range", "error")

    def test_invalid_total(self):
        self.assert_code([record(total="ninety")], "invalid_total", "error")

    def test_unsafe_filename(self):
        self.assert_code([record(report="../escape.md")], "unsafe_filename", "error")

    def test_missing_report_and_radar(self):
        codes = self.codes(self.build([record(report="ghost.md", radar="ghost.png")]))
        self.assertIn("missing_report", codes)
        self.assertIn("missing_radar", codes)

    def test_broken_archive_symlink(self):
        def break_link(root):
            link = root / "company/I/S/Acme/acme.png"
            link.unlink()
            link.symlink_to("../../../../docs/examples/nowhere.png")
        self.assert_code([record()], "broken_archive_symlink", "error", extra=break_link)

    # -- legacy warnings ---------------------------------------------------
    def test_total_precision_drift(self):
        self.assert_code([record(total=100)], "total_precision_drift", "warning")

    def test_grade_boundary_ambiguity(self):
        self.assert_code([record(total=70, grade="Moderate")],
                         "grade_boundary_ambiguity", "warning")

    def test_archive_classification_drift(self):
        root = self.build([record(ind2="Other")])
        self.assertIn("archive_classification_drift", self.codes(root))

    def test_shared_artifact(self):
        self.assert_code([record(), record(id="beta", name="Beta")],
                         "shared_artifact", "warning")

    def test_report_score_drift_from_heading(self):
        report = REPORT + "\n### 1. 现金流质量（40/100）\n"
        self.assert_code([record()], "report_score_drift", "warning", report=report)

    def test_report_score_drift_from_table_without_headings(self):
        report = (REPORT + "\n## 三、综合评分\n\n| 维度 | 得分 |\n|---|---|\n"
                  "| 现金流质量 | 55.0 |\n| 盈利能力 | 90 |\n| 偿债能力 | 90 |\n"
                  "| 运营效率 | 90 |\n| 可持续发展 | 90 |\n")
        codes = self.assert_code([record()], "report_score_drift", "warning", report=report)
        self.assertIn("report table=55.0", codes["report_score_drift"]["detail"])

    def test_report_grade_word_differs_from_catalog(self):
        report = "# Acme 财务健康评估（2026-01-01）\n\n## 一句话结论\n\n⚫ **高风险（90/100）**\n"
        self.assert_code([record()], "report_grade_word_differs_from_catalog", "warning",
                         report=report)


if __name__ == "__main__":
    unittest.main()


class PrecisionThresholdDeterminismTests(unittest.TestCase):
    """0.55 is a boundary, and float summation differs between CPython versions.

    78 vs 77.45 is 0.5499999999999972 with the compensated sum() of CPython 3.12
    and 0.55000000000001 with the plain sum() of 3.11, so an unrounded comparison
    makes the audit result depend on the interpreter that runs it.
    """

    SCORES = {"cashFlow": 81, "profitability": 65, "debt": 76,
              "operations": 90, "sustainability": 76}

    def run_audit(self, total):
        neg = AuditNegativeTests()
        neg.build([record(total=total, scores=dict(self.SCORES),
                          grade="Moderate-High")])
        return neg.codes(Path(neg._tmp.name))

    def test_exact_boundary_is_not_flagged(self):
        codes = self.run_audit(78)  # weighted sum is 77.45 -> exactly 0.55 away
        self.assertNotIn("total_precision_drift", codes)

    def test_drift_beyond_the_boundary_is_flagged(self):
        codes = self.run_audit(79)  # 1.55 away
        self.assertIn("total_precision_drift", codes)

    def test_both_interpreter_float_representations_resolve_the_same_way(self):
        # CPython 3.12 compensated sum() vs 3.11 plain sum().
        for drift in (0.5499999999999972, 0.55000000000001):
            self.assertFalse(round(drift, 6) > 0.55, drift)

    def test_reproduce_scores_uses_the_same_boundary(self):
        for total, expected in ((78, False), (79, True)):
            analysis = audit_reproduction.analyze({
                "id": "acme", "name": "Acme", "total": total, "grade": "Moderate-High",
                "scores": dict(self.SCORES)})
            self.assertEqual(analysis["precision_drift"], expected, total)
