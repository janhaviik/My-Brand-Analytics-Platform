"""Load the shop's CSV exports into SQLite, with validation."""
import csv
import sqlite3
from datetime import date, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id   TEXT PRIMARY KEY,
    order_date TEXT NOT NULL,
    customer   TEXT NOT NULL,
    product    TEXT NOT NULL,
    qty        INTEGER NOT NULL CHECK (qty > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0)
);
CREATE TABLE IF NOT EXISTS instagram (
    month  TEXT PRIMARY KEY,   -- YYYY-MM
    reach  INTEGER NOT NULL,
    visits INTEGER NOT NULL,
    dms    INTEGER NOT NULL
);
"""


def connect(path=":memory:"):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def _rows(path, columns):
    with Path(path).open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = set(columns) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{Path(path).name}: missing columns {sorted(missing)}")
        yield from reader


def load_orders(conn, path):
    """Insert orders.csv rows (order_id, order_date, customer, product, qty, unit_price)."""
    cols = ["order_id", "order_date", "customer", "product", "qty", "unit_price"]
    count = 0
    for line, r in enumerate(_rows(path, cols), start=2):
        try:
            date.fromisoformat(r["order_date"])
            record = (r["order_id"].strip(), r["order_date"], r["customer"].strip(),
                      r["product"].strip(), int(r["qty"]), float(r["unit_price"]))
            if not all(record[:4]) or record[4] <= 0 or record[5] < 0:
                raise ValueError("empty field, qty <= 0 or negative price")
        except ValueError as exc:
            raise ValueError(f"{Path(path).name} line {line}: {exc}") from exc
        conn.execute("INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?)", record)
        count += 1
    conn.commit()
    return count


def load_instagram(conn, path):
    """Insert instagram.csv rows (month as YYYY-MM, reach, visits, dms) from Instagram Insights."""
    count = 0
    for line, r in enumerate(_rows(path, ["month", "reach", "visits", "dms"]), start=2):
        try:
            datetime.strptime(r["month"], "%Y-%m")
            record = (r["month"], int(r["reach"]), int(r["visits"]), int(r["dms"]))
        except ValueError as exc:
            raise ValueError(f"{Path(path).name} line {line}: {exc}") from exc
        conn.execute("INSERT OR REPLACE INTO instagram VALUES (?,?,?,?)", record)
        count += 1
    conn.commit()
    return count
