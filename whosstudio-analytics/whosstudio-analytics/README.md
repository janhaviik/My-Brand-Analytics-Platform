# Whos Studio analytics

A small data pipeline and dashboard for [whosstudio.co](https://whosstudio.co), the handmade brand I run on Instagram. I make the products, answer the DMs and track sales myself, so I built the tooling to answer one question: what turns Instagram attention into orders?

**Costs nothing to run or host.** Python standard library only (no installs), SQLite for storage, GitHub Actions for tests and GitHub Pages for the live dashboard.

> The CSVs in `data/` are **synthetic sample data** so the repo runs out of the box. Swap in real exports (see below) and set `is_sample` to `false` in `data/settings.json`.

## How it works

```
data/orders.csv ─┐
                 ├─► studio/db.py (validate + load into SQLite)
data/instagram.csv ┘            │
                                ▼
                  studio/analytics.py (SQL: monthly revenue, repeat buyers, funnel, top products)
                                │
                                ▼
                  docs/data.js ─► docs/index.html (dashboard)
```

- **Validation:** bad rows (zero quantity, wrong date format, missing columns) stop the load and report the file and line number.
- **Repeat buyers:** a SQL window function (`ROW_NUMBER() OVER (PARTITION BY customer ...)`) marks an order as repeat when that customer ordered before.
- **Funnel:** reach, profile visits, DMs and orders, with the conversion between steps.
- **Tests:** `unittest` covers aggregation, repeat logic, the Instagram join and validation. GitHub Actions runs them on every push.

## Run it

```
python -m unittest discover -s tests -v   # run the tests
python -m studio summary                  # totals and funnel in the terminal
python -m studio build                    # regenerate docs/data.js
```

Then open `docs/index.html` in a browser. Needs Python 3.9+.

## Use your own data

1. `data/orders.csv`: one row per order with `order_id, order_date (YYYY-MM-DD), customer, product, qty, unit_price`.
2. `data/instagram.csv`: one row per month with `month (YYYY-MM), reach, visits, dms`, taken from Instagram Insights.
3. `data/settings.json`: shop name, currency, emojis per product, and your own notes about what the numbers taught you.
4. Product photos: save as `docs/images/<product-name>.jpg` (lowercase, dashes for spaces, e.g. `product-one.jpg`).
5. Run `python -m studio build`.

## Publish the dashboard for free

Push to a public repo, then Settings, Pages, deploy from the `main` branch and the `/docs` folder.

## Next steps

- Rebuild the pipeline on AWS (Lambda and DynamoDB) as a second version. I kept this one local so it stays free.
- Add per-post tracking to see which content type brings the most DMs.
