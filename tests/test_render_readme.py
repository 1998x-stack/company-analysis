"""The README tables are generated from the catalog and must never drift.

Hand-maintained copies had already gone stale: the ranking table pointed
崇达技术 at another company's radar chart and two tickers were outdated.
"""
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("render_readme", ROOT / "tools/render_readme.py")
readme_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(readme_tool)

CATALOG = [
    {"id": "b", "name": "Beta", "ticker": "—（非上市）", "ind1": "I", "ind2": "S",
     "scores": {"cashFlow": 90, "profitability": 50, "debt": 62,
                "operations": 81, "sustainability": 76},
     "total": 76, "grade": "Moderate-High", "gradeLabel": "中等偏上",
     "report": "Beta-财务健康评估-2026-08-13.md", "radar": "Beta_health_radar.png"},
    {"id": "a", "name": "Alpha", "ticker": "NASDAQ: ABC", "ind1": "I", "ind2": "S",
     "scores": {"cashFlow": 90, "profitability": 90, "debt": 90,
                "operations": 90, "sustainability": 90},
     "total": 90, "grade": "Excellent", "gradeLabel": "优秀",
     "report": "Alpha-财务健康评估-2026-06-12.md", "radar": "Alpha_health_radar.png"},
]


class ReadmeRenderTests(unittest.TestCase):
    def test_ranking_is_sorted_by_total_then_name(self):
        rows = readme_tool.render_ranking(CATALOG).splitlines()
        self.assertIn("| 1 | Alpha (NASDAQ: ABC)", rows[2])
        self.assertIn("| 2 | Beta", rows[3])

    def test_placeholder_tickers_are_hidden(self):
        rendered = readme_tool.render_ranking(CATALOG)
        self.assertIn("Alpha (NASDAQ: ABC)", rendered)
        self.assertNotIn("—（非上市）", rendered)
        self.assertIn("| 2 | Beta |", rendered)

    def test_dimension_table_matches_scores(self):
        rendered = readme_tool.render_dimensions(CATALOG)
        self.assertIn("| Alpha | 90 | 90 | 90 | 90 | 90 | **90** |", rendered)
        self.assertIn("| Beta | 90 | 50 | 62 | 81 | 76 | **76** |", rendered)

    def test_link_targets_are_escaped_for_markdown(self):
        # Parentheses end a Markdown link destination early: without escaping,
        # "Sea Limited(Shopee)-…md" produced a dead link on GitHub.
        rendered = readme_tool.render_ranking([dict(CATALOG[0], report="A (B)-x.md",
                                                    radar="A_B.png")])
        self.assertIn("[报告](docs/examples/A%20%28B%29-x.md)", rendered)
        self.assertNotIn("](docs/examples/A (B)", rendered)

    def test_every_generated_link_resolves_in_the_repository(self):
        catalog = json.loads((ROOT / "docs/companies.json").read_text(encoding="utf-8"))
        rendered = readme_tool.render_ranking(catalog)
        targets = re.findall(r"\]\((docs/examples/[^)]+)\)", rendered)
        self.assertEqual(len(targets), len(catalog) * 2)
        missing = [t for t in targets if not (ROOT / unquote(t)).exists()]
        self.assertEqual(missing, [], f"dead README links: {missing[:3]}")

    def test_repository_readme_is_generated_not_hand_edited(self):
        current = (ROOT / "README.md").read_text(encoding="utf-8")
        catalog = json.loads((ROOT / "docs/companies.json").read_text(encoding="utf-8"))
        self.assertEqual(readme_tool.render_readme(current, catalog), current)
        self.assertIn(readme_tool.RANKING_BEGIN, current)
        self.assertIn(readme_tool.DIMENSIONS_BEGIN, current)


class ReadmeCliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "docs").mkdir()
        (self.root / "docs/companies.json").write_text(json.dumps(CATALOG), encoding="utf-8")
        self.readme = self.root / "README.md"
        self.readme.write_text(
            "# T\n\n" + readme_tool.RANKING_BEGIN + "\nstale\n" + readme_tool.RANKING_END +
            "\n\n" + readme_tool.DIMENSIONS_BEGIN + "\nstale\n" + readme_tool.DIMENSIONS_END + "\n",
            encoding="utf-8")

    def run_tool(self, *args):
        return subprocess.run([sys.executable, "tools/render_readme.py", "--root", str(self.root), *args],
                              cwd=ROOT, capture_output=True, text=True)

    def test_check_mode_reports_staleness(self):
        result = self.run_tool("--check")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("stale", result.stdout)

    def test_write_then_check_is_clean(self):
        self.assertEqual(self.run_tool("--write").returncode, 0)
        result = self.run_tool("--check")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_missing_markers_fail_loudly(self):
        self.readme.write_text("# T\n\nno markers here\n", encoding="utf-8")
        result = self.run_tool("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("marker", result.stdout)

    def test_write_does_not_touch_other_content(self):
        before = self.readme.read_text(encoding="utf-8")
        self.run_tool("--write")
        after = self.readme.read_text(encoding="utf-8")
        self.assertTrue(after.startswith("# T\n"))
        self.assertIn("stale", before)
        self.assertNotIn("stale", after)


if __name__ == "__main__":
    unittest.main()
