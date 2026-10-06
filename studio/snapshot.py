"""Snapshot mode: one period of Instagram Insights plus order totals.

"""
import json
from pathlib import Path

REQUIRED = {
    "period": ["label"],
    "instagram": ["views", "viewers", "followers_share", "interactions", "profile_visits",
                  "bio_link_taps", "followers", "net_followers", "reach_by_type", "interactions_by_type"],
    "sales": ["orders", "revenue"],
}


def load(path):
    """Read data/snapshot.json and check it has everything the dashboard needs."""
    name = Path(path).name
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for section, keys in REQUIRED.items():
        for key in keys:
            if key not in data.get(section, {}):
                raise ValueError(f"{name}: missing {section}.{key}")
    if data["sales"]["orders"] <= 0 or data["sales"]["revenue"] < 0:
        raise ValueError(f"{name}: sales.orders must be positive and sales.revenue can't be negative")
    if data["instagram"]["viewers"] <= 0 or data["instagram"]["profile_visits"] <= 0:
        raise ValueError(f"{name}: instagram.viewers and instagram.profile_visits must be positive")
    return data


def derive(data):
    i, s = data["instagram"], data["sales"]
    return {
        "avg_order": s["revenue"] / s["orders"],
        "visit_rate": i["profile_visits"] / i["viewers"],           # profile visits per viewer
        "order_rate": s["orders"] / i["profile_visits"],            # orders per profile visit
        "link_rate": i["bio_link_taps"] / i["profile_visits"],
        "interaction_rate": i["interactions"] / i["views"],
        "nonfollower_share": 100 - i["followers_share"],
    }


def payload(data, cfg):
    """Shape the data the way docs/index.html expects it."""
    return {"name": cfg["name"], "site": cfg["site"], "currency": cfg.get("currency", "₹"),
            "isSample": cfg.get("is_sample", False), "months": [], "products": [],
            "notes": cfg.get("notes", []), "nextSteps": cfg.get("next_steps", []),
            "snapshot": {**data, "derived": derive(data)}}
