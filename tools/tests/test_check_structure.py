"""The structure guard accepts the target layout and refuses each way of drifting from it (mutants)."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import check_structure as cs  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
CFG = cs.load_config(REPO / "tools" / "structure.json")


def skeleton(root, cfg):
    for f in cfg["root_files"]:
        (root / f).write_text("x\n")
    for d in cfg["root_dirs"]:
        (root / d).mkdir(exist_ok=True)
    for slug in ("alpha-incident", "beta-incident"):
        d = root / "incidents" / slug
        d.mkdir(parents=True)
        for f in ("README.md", "reconstruct_exploit.py", "registre_hypotheses.csv", "resultats_2026-01-01.txt"):
            (d / f).write_text("x\n")


class Structure(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.cfg = json.loads(json.dumps(CFG))
        skeleton(self.tmp, self.cfg)

    def errors(self):
        return cs.check(self.tmp, self.cfg)

    def refuses(self, needle):
        errs = self.errors()
        self.assertTrue(any(needle in e for e in errs), f"expected '{needle}' in {errs}")

    # accept
    def test_accepts_the_target_layout(self):
        self.assertEqual(self.errors(), [])

    def test_accepts_the_real_repository_checkout(self):
        # the committed tree only: untracked tool leftovers (caches) are not part of the repository
        import subprocess
        files = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True, check=True).stdout.split("\n")
        real = self.tmp / "real"
        real.mkdir()
        for f in filter(None, files):
            dest = real / f
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text("x\n")
        self.assertEqual(cs.check(real, self.cfg), [])

    # mutants
    def test_refuses_a_stray_file_at_the_root(self):
        (self.tmp / "notes.md").write_text("x")
        self.refuses("unexpected file at the root: notes.md")

    def test_refuses_an_unknown_folder_at_the_root(self):
        (self.tmp / "misc").mkdir()
        self.refuses("unexpected folder at the root: misc")

    def test_refuses_an_incident_folder_at_the_root(self):
        d = self.tmp / "gamma-incident"
        d.mkdir()
        (d / "README.md").write_text("x")
        (d / "reconstruct_exploit.py").write_text("x")
        self.refuses("unexpected folder at the root: gamma-incident")
        self.refuses("incident file gamma-incident/reconstruct_exploit.py is outside incidents/<slug>/")

    def test_refuses_an_incident_folder_one_level_too_deep(self):
        d = self.tmp / "incidents" / "alpha-incident" / "sub"
        d.mkdir()
        (d / "registre_hypotheses.csv").write_text("x")
        self.refuses("is outside incidents/<slug>/")

    def test_refuses_a_hand_over_file_at_the_root(self):
        (self.tmp / "CONTINUE.md").write_text("x")
        self.refuses("forbidden name 'CONTINUE.md'")
        self.refuses("unexpected file at the root: CONTINUE.md")

    def test_refuses_a_hand_over_file_inside_an_incident(self):
        (self.tmp / "incidents" / "alpha-incident" / "DRAFT.md").write_text("x")
        self.refuses("forbidden name 'DRAFT.md'")

    def test_refuses_a_work_folder_deep_in_the_tree(self):
        (self.tmp / "docs" / "work").mkdir()
        self.refuses("forbidden name 'work'")

    def test_refuses_a_backup_file(self):
        (self.tmp / "incidents" / "beta-incident" / "README.md.bak").write_text("x")
        self.refuses("forbidden name 'README.md.bak'")

    def test_refuses_any_file_that_fits_no_allowed_pattern(self):
        # whatever its name: a note, a spreadsheet, an unlisted resume file
        for rel in ("incidents/alpha-incident/notes.md", "docs/plan.xlsx", "digests/summary.txt", "data/extra.json"):
            (self.tmp / rel).write_text("x")
            self.refuses(f"file outside the layout: {rel}")

    def test_accepts_proof_files_of_any_kind_under_preuves(self):
        d = self.tmp / "incidents" / "alpha-incident" / "preuves"
        d.mkdir()
        (d / "anything.json").write_text("x")
        self.assertEqual(self.errors(), [])

    def test_refuses_too_many_visible_root_entries(self):
        for i in range(3):
            name = f"extra{i}.md"
            self.cfg["root_files"].append(name)
            (self.tmp / name).write_text("x")
        self.refuses("visible entries at the root, the ceiling is 14")

    def test_refuses_a_loose_file_in_incidents(self):
        (self.tmp / "incidents" / "oops.md").write_text("x")
        self.refuses("incidents/ holds a loose file: oops.md")

    def test_refuses_an_incident_without_readme(self):
        (self.tmp / "incidents" / "alpha-incident" / "README.md").unlink()
        self.refuses("incidents/alpha-incident/ has no README.md")

    def test_refuses_a_missing_incidents_folder(self):
        shutil.rmtree(self.tmp / "incidents")
        self.refuses("missing folder incidents/")

    # legacy redirects
    def legacy(self, text=None, extra=None):
        self.cfg["legacy_redirects"] = ["alpha-incident"]
        self.cfg["max_legacy_redirects"] = 5
        d = self.tmp / "alpha-incident"
        d.mkdir()
        (d / "README.md").write_text(text if text is not None else "Moved to [incidents/alpha-incident](incidents/alpha-incident/).\n")
        if extra:
            (d / extra).write_text("x")

    def test_accepts_a_proper_legacy_redirect(self):
        self.legacy()
        self.assertEqual(self.errors(), [])

    def test_refuses_a_legacy_redirect_that_holds_more_than_a_readme(self):
        self.legacy(extra="reconstruct_exploit.py")
        self.refuses("must hold only a README.md")

    def test_refuses_a_legacy_redirect_that_does_not_name_its_new_place(self):
        self.legacy(text="Moved somewhere.\n")
        self.refuses("must be short and name incidents/alpha-incident")

    def test_refuses_a_legacy_redirect_that_is_not_listed(self):
        self.legacy()
        self.cfg["legacy_redirects"] = []
        self.refuses("unexpected folder at the root: alpha-incident")

    def test_accepts_a_proper_legacy_script_stub(self):
        self.cfg["legacy_redirects"] = ["check.py"]
        self.cfg["max_legacy_redirects"] = 5
        (self.tmp / "check.py").write_text("# moved to tools/check.py\n")
        self.assertEqual(self.errors(), [])

    def test_refuses_a_legacy_script_stub_that_is_long(self):
        self.cfg["legacy_redirects"] = ["check.py"]
        self.cfg["max_legacy_redirects"] = 5
        (self.tmp / "check.py").write_text("# moved to tools/check.py\n" + "x = 1\n" * 20)
        self.refuses("legacy redirect check.py must be short and name tools/check.py")

    def test_refuses_a_legacy_script_stub_that_does_not_name_its_new_place(self):
        self.cfg["legacy_redirects"] = ["check.py"]
        self.cfg["max_legacy_redirects"] = 5
        (self.tmp / "check.py").write_text("print('hi')\n")
        self.refuses("must be short and name tools/check.py")

    def test_refuses_more_legacy_redirects_than_the_cap(self):
        self.legacy()
        self.cfg["max_legacy_redirects"] = 0
        self.refuses("legacy redirects listed, the cap is 0")


if __name__ == "__main__":
    unittest.main()
