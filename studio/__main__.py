"""Usage: python -m studio build | python -m studio summary"""
import argparse
import json
from pathlib import Path

from . import analytics, db, snapshot


def load(data_dir):
    conn = db.connect()
    db.load_orders(conn, data_dir / "orders.csv")
    db.load_instagram(conn, data_dir / "instagram.csv")
    return conn


def main():
    ap = argparse.ArgumentParser(prog="studio", description="Whos Studio analytics")
    ap.add_argument("command", choices=["build", "summary"])
    ap.add_argument("--data", default="data", type=Path)
    ap.add_argument("--out", default="docs/data.js", type=Path)
    args = ap.parse_args()
    cfg = json.loads((args.data / "settings.json").read_text(encoding="utf-8"))

    snap_path = args.data / "snapshot.json"
    if snap_path.exists():  # snapshot mode: Instagram Insights period plus order totals
        data = snapshot.load(snap_path)
        if args.command == "build":
            payload = snapshot.payload(data, cfg)
            args.out.write_text("window.STUDIO = " + json.dumps(payload, ensure_ascii=False, indent=1) + ";\n",
                                encoding="utf-8")
            print(f"Wrote {args.out} (snapshot: {data['period']['label']})")
        else:
            d = snapshot.derive(data)
            print(f"{data['period']['label']}: {data['sales']['orders']} orders, "
                  f"about {data['sales']['revenue']:,.0f} revenue ({d['avg_order']:,.0f} per order)")
            print(f"  {d['visit_rate']:.1%} of viewers visited the profile; {d['order_rate']:.1%} of visits became orders")
        return

    conn = load(args.data)
    if args.command == "build":
        payload = analytics.dashboard_payload(conn, cfg, args.out.parent / "images")
        args.out.write_text("window.STUDIO = " + json.dumps(payload, ensure_ascii=False, indent=1) + ";\n",
                            encoding="utf-8")
        print(f"Wrote {args.out} ({len(payload['months'])} months, {len(payload['products'])} products)")
    else:
        rows = analytics.monthly(conn)
        best = max(rows, key=lambda r: r["revenue"])
        print(f"Revenue {sum(r['revenue'] for r in rows):,.0f} from {sum(r['orders'] for r in rows)} orders; "
              f"best month {best['month']} ({best['revenue']:,.0f})")
        for name, n, share in analytics.funnel(rows):
            print(f"  {name:<20}{n:>8,}  {'' if share is None else f'{share:.1%} of previous step'}")


main()
