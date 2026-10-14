#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 Natural Earth 陆地面裁剪九州疆域（不改 content/territories.json）。

读：
  mentor/jiuzhou/content/territories.json
  packages/maps/geo/land.json
写：
  packages/maps/geo/territories-clipped.json

需要：pip install shapely
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

REPO = Path(__file__).resolve().parents[3]
TERR = REPO / "mentor" / "jiuzhou" / "content" / "territories.json"
LAND = REPO / "packages" / "maps" / "geo" / "land.json"
OUT = REPO / "packages" / "maps" / "geo" / "territories-clipped.json"


def main() -> int:
    land_fc = json.loads(LAND.read_text(encoding="utf-8"))
    land_geoms = []
    for f in land_fc.get("features") or []:
        try:
            g = make_valid(shape(f["geometry"]))
            if not g.is_empty:
                land_geoms.append(g)
        except Exception as exc:  # noqa: BLE001
            print(f"skip land feature: {exc}", file=sys.stderr)
    if not land_geoms:
        raise SystemExit("land.json 无有效几何")
    land = unary_union(land_geoms)
    print(f"land union: {land.geom_type} area≈{land.area:.4f}")

    terr = json.loads(TERR.read_text(encoding="utf-8"))
    out_feats = []
    gaps: list[tuple[str, float]] = []
    for f in terr.get("features") or []:
        props = dict(f.get("properties") or {})
        kind = props.get("kind")
        if kind not in ("snapshot", "schematic"):
            out_feats.append(f)
            continue
        try:
            g = make_valid(shape(f["geometry"]))
        except Exception as exc:  # noqa: BLE001
            print(f"skip bad geom {props.get('id')}: {exc}", file=sys.stderr)
            continue
        if g.is_empty:
            continue
        before = g.area
        clipped = g.intersection(land)
        if clipped.is_empty:
            label = str(props.get("power") or props.get("id") or "?")
            gaps.append((label, 1.0))
            print(f"WARN empty after clip: {label}", file=sys.stderr)
            continue
        after = clipped.area
        lost = 0.0 if before <= 0 else max(0.0, 1.0 - after / before)
        if lost > 0.08:
            label = (
                f"{props.get('snapshot') or props.get('id') or '?'}:"
                f"{props.get('power') or props.get('name') or '?'}"
            )
            gaps.append((label, lost))
        out_feats.append(
            {
                "type": "Feature",
                "properties": props,
                "geometry": mapping(clipped),
            },
        )

    OUT.write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": out_feats},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    gaps.sort(key=lambda x: -x[1])
    print(f"wrote {OUT} features={len(out_feats)} size={OUT.stat().st_size}")
    print("largest coastal loss (fraction of area):")
    for label, lost in gaps[:12]:
        print(f"  {label}: {lost:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
