import json
import tempfile
import unittest
from pathlib import Path

from studio import snapshot

DATA = {
    "period": {"label": "test period"},
    "instagram": {"views": 1000, "viewers": 400, "followers_share": 30.0, "interactions": 50,
                  "profile_visits": 100, "bio_link_taps": 5, "followers": 200, "net_followers": 10,
                  "reach_by_type": {"Reels": 300}, "interactions_by_type": {"Reels": 30}},
    "sales": {"orders": 4, "revenue": 2000},
}


def write(data):
    path = Path(tempfile.mkdtemp()) / "snapshot.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class SnapshotTests(unittest.TestCase):
    def test_derived_metrics(self):
        d = snapshot.derive(snapshot.load(write(DATA)))
        self.assertEqual(d["avg_order"], 500)
        self.assertAlmostEqual(d["visit_rate"], 0.25)
        self.assertAlmostEqual(d["order_rate"], 0.04)
        self.assertAlmostEqual(d["link_rate"], 0.05)
        self.assertEqual(d["nonfollower_share"], 70.0)

    def test_missing_field_is_named(self):
        bad = json.loads(json.dumps(DATA))
        del bad["sales"]["orders"]
        with self.assertRaisesRegex(ValueError, "sales.orders"):
            snapshot.load(write(bad))

    def test_zero_orders_rejected(self):
        bad = json.loads(json.dumps(DATA))
        bad["sales"]["orders"] = 0
        with self.assertRaises(ValueError):
            snapshot.load(write(bad))


if __name__ == "__main__":
    unittest.main()
