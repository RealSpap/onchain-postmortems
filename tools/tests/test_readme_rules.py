"""The README ceiling and the dash rule of check_structure.py : each rule must refuse its own planted fault."""
import importlib.util, json, shutil, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_structure", HERE.parent / "check_structure.py")
cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)
CFG = {"root_files": ["README.md"], "root_dirs": [], "max_root_entries": 1, "incident_parent": None, "forbidden_names": [],
       "allowed_paths": [], "readme_max_lines": 10}


class ReadmeRules(unittest.TestCase):
    def check(self, text):
        d = Path(tempfile.mkdtemp())
        try:
            (d / "README.md").write_text(text, encoding="utf-8")
            return cs.check(d, CFG)
        finally:
            shutil.rmtree(d)

    def test_short_clean_readme_passes(self):
        self.assertEqual(self.check("# Title\n\nOne line.\n"), [])

    def test_long_readme_is_refused(self):
        self.assertTrue(any("ceiling" in e for e in self.check("x\n" * 11)))

    def test_em_dash_is_refused(self):
        self.assertTrue(any("dash" in e for e in self.check("a " + chr(0x2014) + " b\n")))

    def test_en_dash_is_refused(self):
        self.assertTrue(any("dash" in e for e in self.check("a " + chr(0x2013) + " b\n")))


if __name__ == "__main__":
    unittest.main()
