"""SQL analytics: monthly revenue, repeat buyers, Instagram funnel, top products."""
import calendar
import re

MONTHLY_SQL = """
WITH o AS (
    SELECT substr(order_date, 1, 7) AS month,
           qty * unit_price AS revenue,
           ROW_NUMBER() OVER (PARTITION BY customer ORDER BY order_date, order_id) AS nth
    FROM orders
)
SELECT o.month,
       COUNT(*)                  AS orders,
       SUM(o.revenue)            AS revenue,
       SUM(o.nth > 1)            AS repeat,
       COALESCE(MAX(i.reach), 0)  AS reach,
       COALESCE(MAX(i.visits), 0) AS visits,
       COALESCE(MAX(i.dms), 0)    AS dms
FROM o LEFT JOIN instagram i ON i.month = o.month
GROUP BY o.month
ORDER BY o.month
"""


def monthly(conn):
    """One dict per month. An order is 'repeat' if its customer ordered before."""
    keys = ["month", "orders", "revenue", "repeat", "reach", "visits", "dms"]
    return [dict(zip(keys, row)) for row in conn.execute(MONTHLY_SQL)]


def top_products(conn, limit=4):
    sql = ("SELECT product, SUM(qty), SUM(qty * unit_price) FROM orders "
           "GROUP BY product ORDER BY 3 DESC LIMIT ?")
    return [{"name": n, "units": u, "revenue": r} for n, u, r in conn.execute(sql, (limit,))]


def funnel(rows):
    """Total each stage and the share of the previous stage that moved on."""
    stages = [("Reached", sum(r["reach"] for r in rows)),
              ("Visited the profile", sum(r["visits"] for r in rows)),
              ("Sent a DM", sum(r["dms"] for r in rows)),
              ("Placed an order", sum(r["orders"] for r in rows))]
    return [(name, n, (n / stages[i - 1][1] if i and stages[i - 1][1] else None))
            for i, (name, n) in enumerate(stages)]


def dashboard_payload(conn, cfg, images_dir):
    """Shape the data the way docs/index.html expects it."""
    months = [{**r, "m": calendar.month_abbr[int(r["month"][5:])]} for r in monthly(conn)[-12:]]
    products = []
    for p in top_products(conn):
        slug = re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")
        img = next((f"images/{slug}.{e}" for e in ("jpg", "png", "webp")
                    if (images_dir / f"{slug}.{e}").exists()), "")
        products.append({**p, "img": img, "emoji": cfg.get("product_emoji", {}).get(p["name"], "✨")})
    return {"name": cfg["name"], "site": cfg["site"], "currency": cfg.get("currency", "₹"),
            "isSample": cfg.get("is_sample", True), "months": months,
            "products": products, "notes": cfg.get("notes", [])}
