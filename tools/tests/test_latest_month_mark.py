"""The "(latest month)" mark of INDEX.md: each fault must be refused by check_readme_consistency.py."""
import importlib.util, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_readme_consistency", HERE.parent / "check_readme_consistency.py")
crc = importlib.util.module_from_spec(spec); spec.loader.exec_module(crc)


class Month:
    def __init__(self, y, m):
        self.key = (y, m)


YEARS = {2026: {"months": [Month(2026, 9), Month(2026, 10)]}}


class LatestMonthMark(unittest.TestCase):
    def refused(self, fn, *args):
        with self.assertRaises(crc.ConsistencyError):
            fn(*args)

    def test_right_mark_passes(self):
        crc.check_current_month(YEARS, [(2026, 10)])

    def test_absent_mark_is_refused(self):
        self.refused(crc.check_current_month, YEARS, [])

    def test_two_marks_are_refused(self):
        self.refused(crc.check_current_month, YEARS, [(2026, 9), (2026, 10)])

    def test_wrong_month_is_refused(self):
        self.refused(crc.check_current_month, YEARS, [(2026, 9)])

    def test_old_wording_in_prose_is_refused(self):
        self.refused(crc.check_no_old_mark, "Intro.\nThe current month is marked below.\n")

    def test_new_wording_in_prose_passes(self):
        crc.check_no_old_mark("The latest month with an incident is marked below.\n")


if __name__ == "__main__":
    unittest.main()
