"""T-029 sanity: Chang'an–Luoyang + route/leadsTo counts."""
from __future__ import annotations

import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

R = 6371.0
ROOT = Path(__file__).resolve().parents[4]  # mentor/jiuzhou


def hav(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    p1, p2 = radians(lat1), radians(lat2)
    dp = radians(lat2 - lat1)
    dl = radians(lon2 - lon1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * R * asin(min(1.0, sqrt(a)))


def main() -> None:
    km = hav(108.94, 34.27, 112.45, 34.62)
    print(
        f"Chang'an->Luoyang: {round(km)} km; "
        f"infantry ~{round(km / 25, 1)}d; cavalry ~{round(km / 60, 1)}d"
    )

    routes_raw = json.loads((ROOT / "content" / "routes.json").read_text(encoding="utf-8"))
    routes = routes_raw["routes"] if isinstance(routes_raw, dict) else routes_raw
    atlas = json.loads((ROOT / "content" / "atlas.json").read_text(encoding="utf-8"))
    places = {p["id"]: p for p in atlas["places"]}
    events = atlas["events"]

    n_route = 0
    for r in routes:
        w = r.get("waypoints", [])
        if len(w) < 2:
            continue
        s = 0.0
        for i in range(1, len(w)):
            s += hav(w[i - 1]["lon"], w[i - 1]["lat"], w[i]["lon"], w[i]["lat"])
        n_route += 1
        print(f"route {r['id']}: {round(s)} km infantry~{round(s / 25, 1)}d")
    print(f"routes_with_estimate={n_route}")

    n_lead = 0
    for e in events:
        leads = e.get("leadsTo") or []
        if not leads:
            continue
        fr = places.get(e["placeId"])
        if not fr:
            continue
        for lid in leads:
            nxt = next((x for x in events if x["id"] == lid), None)
            if not nxt:
                continue
            to = places.get(nxt["placeId"])
            if not to or to["id"] == fr["id"]:
                continue
            d = hav(fr["lon"], fr["lat"], to["lon"], to["lat"])
            n_lead += 1
            if n_lead <= 10:
                print(f"leadsTo {e['id']}->{lid}: {round(d)} km")
    print(f"leadsTo_diff_place={n_lead}")


if __name__ == "__main__":
    main()
