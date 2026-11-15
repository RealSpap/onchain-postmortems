import csv
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import by_type  # noqa: E402
import find_incidents  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
ROWS = json.loads((REPO / "data" / "incidents.json").read_text(encoding="utf-8"))["incidents"]


class ByType(unittest.TestCase):
    def test_counts_add_up_to_the_data(self):
        self.assertEqual(sum(len(rs) for _, rs in by_type.groups(ROWS)), len(ROWS))
        self.assertEqual(sum(r["loss_usd"] for _, rs in by_type.groups(ROWS) for r in rs), sum(r["loss_usd"] for r in ROWS))

    def test_the_page_lists_every_incident_once(self):
        page = by_type.render_page(ROWS)
        for r in ROWS:
            self.assertEqual(page.count(f"(../incidents/{r['slug']}/)"), 1, r["slug"])

    def test_the_dates_come_from_the_data(self):
        first, last = by_type.span(ROWS)
        self.assertEqual(last, max(r["date"][:10] for r in ROWS))
        self.assertIn(last, by_type.render_block(ROWS))

    def test_an_added_incident_changes_the_counts_and_the_date(self):
        extra = dict(ROWS[0], slug="x-new", date="2099-01-01", category="Oracle", loss_usd=5)
        block = by_type.render_block(ROWS + [extra])
        self.assertIn(f"{len(ROWS) + 1} incidents", block)
        self.assertIn("2099-01-01", block)

    def test_an_unknown_tag_is_still_listed(self):
        extra = dict(ROWS[0], slug="x-new", category="Brand-New-Tag")
        self.assertIn("## Brand-New-Tag", by_type.render_page(ROWS + [extra]))

    def test_splice_refuses_a_readme_without_markers(self):
        with self.assertRaises(SystemExit):
            by_type.splice("no markers here", "x")

    def test_the_committed_files_are_current(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertEqual(by_type.splice(readme, by_type.render_block(ROWS)), readme)
        self.assertEqual((REPO / "docs" / "by-type.md").read_text(encoding="utf-8"), by_type.render_page(ROWS))


class Finder(unittest.TestCase):
    def setUp(self):
        with open(REPO / "data" / "incidents.csv", encoding="utf-8", newline="") as fh:
            self.rows = list(csv.DictReader(fh))

    def test_filters_combine_with_and(self):
        a = find_incidents.find(self.rows, category="Bridge")
        b = find_incidents.find(self.rows, category="Bridge", chain="Ethereum")
        self.assertTrue(0 < len(b) <= len(a))
        self.assertTrue(all(r["category"] == "Bridge" and "ethereum" in r["chain"].lower() for r in b))

    def test_no_filter_returns_everything_newest_first(self):
        allr = find_incidents.find(self.rows)
        self.assertEqual(len(allr), len(self.rows))
        self.assertEqual(allr[0]["date"], max(r["date"] for r in self.rows))

    def test_an_impossible_filter_returns_nothing(self):
        self.assertEqual(find_incidents.find(self.rows, category="Bridge", text="zzzz-no-such-word"), [])


if __name__ == "__main__":
    unittest.main()
