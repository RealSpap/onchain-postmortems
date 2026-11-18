"""The incident-count badge file is generated from the same rows as the JSON export and must match the committed file."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import export_dataset as ed  # noqa: E402


class BadgeTest(unittest.TestCase):
    def test_badge_counts_rows(self):
        rows = [{"slug": "a"}, {"slug": "b"}]
        data = json.loads(ed.render_badge(rows))
        self.assertEqual((data["schemaVersion"], data["label"], data["message"]), (1, "incidents", "2"))

    def test_committed_badge_is_current(self):
        rows = ed.parse(ed.INDEX.read_text())
        self.assertEqual(ed.OUT_BADGE.read_text(), ed.render_badge(rows))


if __name__ == "__main__":
    unittest.main()
