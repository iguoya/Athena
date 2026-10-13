#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Natural Earth 生成东亚海陆底图（入库小文件，原始 zip 在 .cache）。

前置：
  .cache/maps/natural-earth/ne_50m_land.zip
  .cache/maps/natural-earth/ne_50m_admin_0_countries.zip
  pip install pyshp

写出：
  packages/maps/geo/land.json
  packages/maps/geo/countries.json
  packages/maps/geo/lakes.json
  （总大小目标 ≤ 250KB）
"""

from __future__ import annotations

import json
import math
import zipfile
from pathlib import Path

import shapefile

REPO = Path(__file__).resolve().parents[3]
NE = REPO / ".cache" / "maps" / "natural-earth"
OUT = REPO / "packages" / "maps" / "geo"

BBOX = (70.0, 5.0, 145.0, 55.0)  # W S E N
# 东亚邻国（非中国），用更淡陆色
NEIGHBOR_ISO = {
    "PRK",
    "KOR",
    "JPN",
    "MNG",
    "RUS",
    "KAZ",
    "KGZ",
    "TJK",
    "UZB",
    "TKM",
    "AFG",
    "PAK",
    "IND",
    "NPL",
    "BTN",
    "BGD",
    "MMR",
    "LAO",
    "THA",
    "VNM",
    "KHM",
    "MYS",
    "IDN",
    "PHL",
    "TWN",  # NE 有时单独
}


def extract_shp(zip_name: str, member_stem: str) -> Path:
    zpath = NE / zip_name
    dest = NE / "extracted" / member_stem
    dest.mkdir(parents=True, exist_ok=True)
    shp = dest / f"{member_stem}.shp"
    if shp.exists():
        return shp
    with zipfile.ZipFile(zpath) as zf:
        for n in zf.namelist():
            base = Path(n).name
            if base.startswith(member_stem) and base.endswith(
                (".shp", ".shx", ".dbf", ".prj", ".cpg")
            ):
                target = dest / base
                if not target.exists():
                    target.write_bytes(zf.read(n))
    if not shp.exists():
        raise SystemExit(f"missing {shp} after extract {zip_name}")
    return shp


def point_in_bbox(x: float, y: float) -> bool:
    return BBOX[0] <= x <= BBOX[2] and BBOX[1] <= y <= BBOX[3]


def ring_hits_bbox(ring: list[tuple[float, float]]) -> bool:
    return any(point_in_bbox(x, y) for x, y in ring)


def clip_ring_soft(ring: list[tuple[float, float]]) -> list[list[float]]:
    """软裁：只保留落在框内或框边附近的点；过稀则跳过。"""
    out: list[list[float]] = []
    for x, y in ring:
        if (
            BBOX[0] - 2 <= x <= BBOX[2] + 2
            and BBOX[1] - 2 <= y <= BBOX[3] + 2
        ):
            out.append([round(x, 3), round(y, 3)])
    return out


def douglas_peucker(
    pts: list[list[float]], tol: float
) -> list[list[float]]:
    if len(pts) < 3:
        return pts

    def perp(a, b, p):
        (x1, y1), (x2, y2), (x, y) = a, b, p
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(x - x1, y - y1)
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))

    stack = [(0, len(pts) - 1)]
    keep = {0, len(pts) - 1}
    while stack:
        i, j = stack.pop()
        max_d, max_i = 0.0, None
        for k in range(i + 1, j):
            d = perp(pts[i], pts[j], pts[k])
            if d > max_d:
                max_d, max_i = d, k
        if max_i is not None and max_d > tol:
            keep.add(max_i)
            stack.append((i, max_i))
            stack.append((max_i, j))
    return [pts[i] for i in sorted(keep)]


def simplify_ring(ring: list[list[float]], tol: float) -> list[list[float]]:
    if len(ring) < 4:
        return ring
    closed = ring[0] == ring[-1]
    body = ring[:-1] if closed else ring
    simp = douglas_peucker(body, tol)
    if closed:
        if simp[0] != simp[-1]:
            simp.append(simp[0][:])
    return simp if len(simp) >= 4 else ring


def shapes_to_features(
    shp_path: Path,
    *,
    prop_fn,
    tol: float,
) -> list[dict]:
    sf = shapefile.Reader(str(shp_path))
    fields = [f[0] for f in sf.fields[1:]]
    features: list[dict] = []
    for sr in sf.iterShapeRecords():
        rec = {fields[i]: sr.record[i] for i in range(len(fields))}
        props = prop_fn(rec)
        if props is None:
            continue
        shape = sr.shape
        parts = list(shape.parts) + [len(shape.points)]
        polys: list[list[list[list[float]]]] = []
        # shapefile polygon: one or more rings; treat each part as ring,
        # group into MultiPolygon of single-ring polygons for simplicity
        rings_out: list[list[list[float]]] = []
        for i in range(len(parts) - 1):
            raw = [(p[0], p[1]) for p in shape.points[parts[i] : parts[i + 1]]]
            if not ring_hits_bbox(raw):
                continue
            clipped = clip_ring_soft(raw)
            if len(clipped) < 4:
                continue
            simp = simplify_ring(clipped, tol)
            if len(simp) < 4:
                continue
            rings_out.append(simp)
        if not rings_out:
            continue
        # exterior = first ring; rest as separate polygons (good enough for land)
        for ring in rings_out:
            polys.append([ring])
        geom = (
            {"type": "Polygon", "coordinates": polys[0]}
            if len(polys) == 1
            else {"type": "MultiPolygon", "coordinates": polys}
        )
        features.append(
            {"type": "Feature", "properties": props, "geometry": geom}
        )
    return features


def write_fc(path: Path, note: str, features: list[dict]) -> None:
    doc = {"_note": note, "type": "FeatureCollection", "features": features}
    raw = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    path.write_text(raw, encoding="utf-8")
    print(f"wrote {path.relative_to(REPO)} features={len(features)} bytes={len(raw.encode())}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    land_shp = extract_shp("ne_50m_land.zip", "ne_50m_land")
    admin_shp = extract_shp(
        "ne_50m_admin_0_countries.zip", "ne_50m_admin_0_countries"
    )

    # 逐步放宽容差直到总包体够小
    for tol in (0.08, 0.12, 0.18, 0.25, 0.35):
        land = shapes_to_features(
            land_shp,
            prop_fn=lambda _r: {"id": "land", "kind": "land"},
            tol=tol,
        )
        # 合并过多碎片：只保留较大环
        land = [
            f
            for f in land
            if (
                len(f["geometry"]["coordinates"][0])
                if f["geometry"]["type"] == "Polygon"
                else sum(len(p[0]) for p in f["geometry"]["coordinates"])
            )
            >= 8
        ]

        def country_props(rec: dict):
            iso = str(rec.get("ISO_A3") or rec.get("ADM0_A3") or "")
            name = str(rec.get("NAME") or rec.get("ADMIN") or iso)
            # 只要与 bbox 相交的国家，由几何过滤
            role = "china" if iso in {"CHN", "HKG", "MAC"} else (
                "neighbor" if iso in NEIGHBOR_ISO else "other"
            )
            if role == "other":
                # 仍保留与框相交的（如部分东南亚）
                role = "neighbor"
            return {"id": iso or name, "name": name, "role": role}

        countries = shapes_to_features(
            admin_shp, prop_fn=country_props, tol=tol
        )
        # 只要中国 + 邻国标签
        countries = [
            f
            for f in countries
            if f["properties"].get("role") in {"china", "neighbor"}
        ]

        write_fc(
            OUT / "land.json",
            "Natural Earth 50m land，裁东亚并简化。原始 zip 在 .cache/maps/natural-earth/。",
            land,
        )
        write_fc(
            OUT / "countries.json",
            "Natural Earth 50m admin0，裁东亚；role=china|neighbor。",
            countries,
        )

        lakes_zip = NE / "ne_10m_lakes.zip"
        lakes_feats: list[dict] = []
        if lakes_zip.exists():
            lakes_shp = extract_shp("ne_10m_lakes.zip", "ne_10m_lakes")
            lakes_feats = shapes_to_features(
                lakes_shp,
                prop_fn=lambda r: {
                    "id": str(r.get("name") or r.get("Name") or "lake"),
                    "kind": "lake",
                },
                tol=max(tol, 0.15),
            )
            lakes_feats = lakes_feats[:80]
            write_fc(
                OUT / "lakes.json",
                "Natural Earth 10m lakes，裁东亚并简化。",
                lakes_feats,
            )
        else:
            write_fc(
                OUT / "lakes.json",
                "占位：下载 ne_10m_lakes.zip 后重跑本脚本。",
                [],
            )

        total = sum(
            (OUT / n).stat().st_size
            for n in ("land.json", "countries.json", "lakes.json")
        )
        print(f"tol={tol} total_bytes={total}")
        if total <= 250_000:
            break
    else:
        print("warning: still >250KB after max tol")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
