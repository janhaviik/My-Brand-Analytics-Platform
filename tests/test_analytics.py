import tempfile
import unittest
from pathlib import Path

from studio import analytics, db

ORDERS = """order_id,order_date,customer,product,qty,unit_price
A1,2026-01-05,c1,Mug,1,400
A2,2026-01-20,c2,Mug,2,400
A3,2026-02-03,c1,Bag,1,600
A4,2026-02-10,c1,Mug,1,400
"""
INSTA = "month,reach,visits,dms\n2026-01,1000,100,10\n2026-02,2000,150,12\n"


def write(text):
    path = Path(tempfile.mkdtemp()) / "f.csv"
    path.write_text(text, encoding="utf-8")
    return path


def make_conn(orders=ORDERS):
    conn = db.connect()
    db.load_orders(conn, write(orders))
    db.load_instagram(conn, write(INSTA))
    return conn


class AnalyticsTests(unittest.TestCase):
    def test_monthly_revenue_and_orders(self):
        jan, feb = analytics.monthly(make_conn())
        self.assertEqual((jan["orders"], jan["revenue"]), (2, 1200))
        self.assertEqual((feb["orders"], feb["revenue"]), (2, 1000))

    def test_repeat_means_customer_ordered_before(self):
        jan, feb = analytics.monthly(make_conn())
        self.assertEqual(jan["repeat"], 0)   # first orders only
        self.assertEqual(feb["repeat"], 2)   # c1 ordered again twice

    def test_instagram_joined_and_funnel(self):
        rows = analytics.monthly(make_conn())
        self.assertEqual(rows[0]["reach"], 1000)
        stages = analytics.funnel(rows)
        self.assertEqual(stages[-1][:2], ("Placed an order", 4))
        self.assertAlmostEqual(stages[1][2], 250 / 3000)

    def test_bad_rows_report_the_line(self):
        bad = ORDERS + "A5,2026-02-11,c3,Mug,0,400\n"
        with self.assertRaisesRegex(ValueError, "line 6"):
            make_conn(bad)

    def test_top_products_sorted_by_revenue(self):
        top = analytics.top_products(make_conn())
        self.assertEqual([p["name"] for p in top], ["Mug", "Bag"])


if __name__ == "__main__":
    unittest.main()
