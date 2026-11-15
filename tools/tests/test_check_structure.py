"""The structure guard accepts the target layout and refuses each way of drifting from it (mutants)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import check_structure as cs  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
CFG = cs.load_config(REPO / "tools" / "structure.json")


def put(root, rel, text="x\n"):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def skeleton(root, cfg):
    for f in cfg["root_files"]:
        put(root, f)
    for slug in ("alpha-incident", "beta-incident"):
        for f in ("README.md", "reconstruct_exploit.py", "registre_hypotheses.csv", "resultats_2026-01-01.txt"):
            put(root, f"incidents/{slug}/{f}")
    for f in ("tools/check_structure.py", "data/incidents.json", "digests/2026-01.md", "docs/method.md", ".github/workflows/check_drift.yml"):
        put(root, f)


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
        files = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True, check=True).stdout.split("\n")
        real = self.tmp / "real"
        real.mkdir()
        for f in filter(None, files):
            dest = real / f
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / f, dest)
        self.assertEqual(cs.check(real, self.cfg), [])

    def test_accepts_proof_files_of_any_kind_under_preuves_at_any_depth(self):
        put(self.tmp, "incidents/alpha-incident/preuves/anything.json")
        put(self.tmp, "incidents/alpha-incident/preuves/deeper/more.txt")
        self.assertEqual(self.errors(), [])

    # mutants: the root
    def test_refuses_a_stray_file_at_the_root(self):
        put(self.tmp, "notes.md")
        self.refuses("unexpected file at the root: notes.md")

    def test_refuses_an_unknown_folder_at_the_root(self):
        put(self.tmp, "misc/a.md")
        self.refuses("unexpected folder at the root: misc")

    def test_refuses_an_incident_folder_at_the_root(self):
        put(self.tmp, "gamma-incident/README.md")
        put(self.tmp, "gamma-incident/reconstruct_exploit.py")
        self.refuses("unexpected folder at the root: gamma-incident")
        self.refuses("incident file gamma-incident/reconstruct_exploit.py is outside incidents/<slug>/")

    def test_refuses_too_many_visible_root_entries(self):
        for i in range(3):
            name = f"extra{i}.md"
            self.cfg["root_files"].append(name)
            put(self.tmp, name)
        self.refuses("visible entries at the root, the ceiling is 14")

    # mutants: inside the tree
    def test_refuses_an_incident_folder_one_level_too_deep(self):
        put(self.tmp, "incidents/alpha-incident/sub/registre_hypotheses.csv")
        self.refuses("is outside incidents/<slug>/")
        self.refuses("file outside the layout: incidents/alpha-incident/sub/registre_hypotheses.csv")

    def test_refuses_a_deep_readme_and_a_deep_script(self):
        put(self.tmp, "incidents/alpha-incident/sub/README.md")
        put(self.tmp, "incidents/alpha-incident/sub/deep/x.py")
        put(self.tmp, "tools/scratch2/x.py")
        for rel in ("incidents/alpha-incident/sub/README.md", "incidents/alpha-incident/sub/deep/x.py", "tools/scratch2/x.py"):
            self.refuses(f"file outside the layout: {rel}")

    def test_refuses_a_hand_over_file_wherever_it_hides(self):
        for rel in ("CONTINUE.md", "docs/DRAFT.md", "incidents/alpha-incident/preuves/TODO.md", "incidents/beta-incident/NOTES.txt"):
            put(self.tmp, rel)
        self.refuses("forbidden name 'CONTINUE.md'")
        self.refuses("forbidden name 'DRAFT.md'")
        self.refuses("forbidden name 'TODO.md'")
        self.refuses("forbidden name 'NOTES.txt'")

    def test_refuses_a_work_folder_deep_in_the_tree(self):
        put(self.tmp, "docs/work/a.md")
        self.refuses("forbidden name 'work'")

    def test_refuses_a_backup_or_log_file(self):
        put(self.tmp, "incidents/beta-incident/README.md.bak")
        put(self.tmp, "incidents/beta-incident/preuves/run.log")
        self.refuses("forbidden name 'README.md.bak'")
        self.refuses("forbidden name 'run.log'")

    def test_refuses_any_file_that_fits_no_allowed_pattern(self):
        # whatever its name: a note, a spreadsheet, a summary, a file in docs that is not listed
        for rel in ("incidents/alpha-incident/notes.md", "docs/plan.xlsx", "docs/SUMMARY.md", "digests/summary.txt", "data/extra.json", ".github/workflows/evil.yml"):
            put(self.tmp, rel)
            self.refuses(f"file outside the layout: {rel}")

    def test_refuses_hidden_files_and_folders_nobody_listed(self):
        for rel in ("incidents/alpha-incident/preuves/.hidden/x", "docs/.secret.md", "incidents/alpha-incident/preuves/.env"):
            put(self.tmp, rel)
            self.refuses(f"file outside the layout: {rel}")

    def test_refuses_a_symbolic_link(self):
        os.symlink("/etc/hostname", self.tmp / "docs" / "method2.md")
        self.refuses("symbolic link: docs/method2.md")

    def test_refuses_a_loose_file_in_incidents(self):
        put(self.tmp, "incidents/oops.md")
        self.refuses("incidents/ holds a loose file: oops.md")

    def test_refuses_an_incident_without_readme(self):
        (self.tmp / "incidents" / "alpha-incident" / "README.md").unlink()
        self.refuses("incidents/alpha-incident/ has no README.md")

    def test_refuses_a_missing_incidents_folder(self):
        shutil.rmtree(self.tmp / "incidents")
        self.refuses("missing folder incidents/")

    def test_a_tracked_cache_folder_is_still_checked(self):
        # in a git checkout, what git tracks is checked even under names that .gitignore normally hides
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        put(self.tmp, "docs/__pycache__/DRAFT.md")
        subprocess.run(["git", "add", "-f", "-A"], cwd=self.tmp, check=True)
        self.refuses("file outside the layout: docs/__pycache__/DRAFT.md")

    # legacy redirects
    def legacy(self, text=None, extra=None):
        self.cfg["legacy_redirects"] = ["alpha-incident"]
        self.cfg["max_legacy_redirects"] = 5
        put(self.tmp, "alpha-incident/README.md", text if text is not None else "Moved to [incidents/alpha-incident](../incidents/alpha-incident/).\n")
        if extra:
            put(self.tmp, f"alpha-incident/{extra}")

    def test_accepts_a_proper_legacy_redirect(self):
        self.legacy()
        self.assertEqual(self.errors(), [])

    def test_refuses_a_legacy_redirect_that_holds_more_than_a_readme(self):
        self.legacy(extra="reconstruct_exploit.py")
        self.refuses("must hold only a README.md")

    def test_refuses_a_legacy_redirect_that_links_to_the_wrong_place(self):
        # the relative link from the old folder must climb out of it: ../incidents/<slug>/
        self.legacy(text="Moved to [incidents/alpha-incident](incidents/alpha-incident/).\n")
        self.refuses("must be short and name ../incidents/alpha-incident/")

    def test_refuses_a_legacy_redirect_with_a_fake_target(self):
        self.legacy(text="See [elsewhere](../incidents/alpha-incident-fake/).\n")
        self.refuses("must be short and name ../incidents/alpha-incident/")

    def test_refuses_a_long_legacy_redirect(self):
        self.legacy(text="Moved to (../incidents/alpha-incident/).\n" + "more text\n" * 10)
        self.refuses("must be short")

    def test_refuses_a_legacy_redirect_that_is_not_listed(self):
        self.legacy()
        self.cfg["legacy_redirects"] = []
        self.refuses("unexpected folder at the root: alpha-incident")

    def test_accepts_a_proper_legacy_script_stub(self):
        self.cfg["legacy_redirects"] = ["check.py"]
        self.cfg["max_legacy_redirects"] = 5
        put(self.tmp, "check.py", "# moved to tools/check.py\n")
        self.assertEqual(self.errors(), [])

    def test_refuses_a_legacy_script_stub_that_is_long(self):
        self.cfg["legacy_redirects"] = ["check.py"]
        self.cfg["max_legacy_redirects"] = 5
        put(self.tmp, "check.py", "# moved to tools/check.py\n" + "x = 1\n" * 20)
        self.refuses("legacy redirect check.py must be short and name tools/check.py")

    def test_refuses_a_legacy_script_stub_that_does_not_name_its_new_place(self):
        self.cfg["legacy_redirects"] = ["check.py"]
        self.cfg["max_legacy_redirects"] = 5
        put(self.tmp, "check.py", "print('hi')\n")
        self.refuses("must be short and name tools/check.py")

    def test_refuses_more_legacy_redirects_than_the_cap(self):
        self.legacy()
        self.cfg["max_legacy_redirects"] = 0
        self.refuses("legacy redirects listed, the cap is 0")


if __name__ == "__main__":
    unittest.main()
