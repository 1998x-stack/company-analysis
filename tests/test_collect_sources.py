import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("collect",ROOT/"tools/collect_sources.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class CollectorTests(unittest.TestCase):
    def test_html_strips_script(self):
        value=m.extract_text(b"<html><style>bad</style><body>Good<script>evil()</script>More</body></html>","text/html")
        self.assertIn("Good",value)
        self.assertNotIn("evil()",value)
    def test_disallow_private_ip_and_unlisted_hostname(self):
        with self.assertRaises(ValueError):
            m.validate_url("http://localhost",["localhost"])
        with self.assertRaises(ValueError):
            m.validate_url("https://example.com",["another-domain.invalid"])
if __name__=="__main__":unittest.main()
