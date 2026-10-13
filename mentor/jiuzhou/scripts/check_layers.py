#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验九州的叠加图层数据：features / routes / highlights / stories（ADR 0158）。

只读内容文件，不改动它们；引用的 id 必须能在 atlas / hydro / corridors 里找到。
用法：python3 scripts/check_layers.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CONTENT = Path(__file__).resolve().parent.parent / "content"

# 坐标合法范围：覆盖中国全境并留出郑和航线（南至爪哇、西至古里）与玄奘西行的余量。
LON_RANGE = (50.0, 145.0)
LAT_RANGE = (-12.0, 56.0)


def load(name: str) -> dict:
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def in_range(lon: float, lat: float) -> bool:
    return LON_RANGE[0] <= lon <= LON_RANGE[1] and LAT_RANGE[0] <= lat <= LAT_RANGE[1]


def check_coords(label: str, coords: list, problems: list[str]) -> None:
    if len(coords) < 2:
        problems.append(f"{label}: 折线至少 2 个点")
    for c in coords:
        if len(c) != 2 or not in_range(c[0], c[1]):
            problems.append(f"{label}: 坐标越界或格式不对 {c}")


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    atlas = load("atlas.json")
    hydro = load("hydro.json")
    corridors = load("corridors.json")
    features_doc = load("features.json")
    routes_doc = load("routes.json")
    highlights_doc = load("highlights.json")
    stories_doc = load("stories.json")

    event_ids = {e["id"] for e in atlas["events"]}
    place_ids = {p["id"] for p in atlas["places"]}
    hydro_ids = {f["properties"]["id"] for f in hydro["features"]}
    corridor_ids = {f["properties"]["id"] for f in corridors["features"]}

    problems: list[str] = []

    # ---- features ----
    features = features_doc["features"]
    feature_ids = [f["id"] for f in features]
    if len(set(feature_ids)) != len(feature_ids):
        problems.append("features: id 重复")
    feature_set = set(feature_ids)
    for f in features:
        fid = f["id"]
        if "to" in f and f["to"] < f["from"]:
            problems.append(f"features[{fid}]: to < from")
        if f["geometry"]["type"] != "LineString":
            problems.append(f"features[{fid}]: 只支持 LineString")
        else:
            check_coords(f"features[{fid}]", f["geometry"]["coordinates"], problems)
        if not f.get("note"):
            problems.append(f"features[{fid}]: 缺 note")

    # ---- routes ----
    routes = routes_doc["routes"]
    route_ids = [r["id"] for r in routes]
    if len(set(route_ids)) != len(route_ids):
        problems.append("routes: id 重复")
    route_set = set(route_ids)
    for r in routes:
        rid = r["id"]
        if r.get("eventId") and r["eventId"] not in event_ids:
            problems.append(f"routes[{rid}]: eventId 不存在 {r['eventId']}")
        wps = r["waypoints"]
        if len(wps) < 2:
            problems.append(f"routes[{rid}]: 路线至少 2 个点")
        last_year = None
        for w in wps:
            if not in_range(w["lon"], w["lat"]):
                problems.append(f"routes[{rid}]: 坐标越界 {w['label']}")
            if w.get("placeId") and w["placeId"] not in place_ids:
                problems.append(f"routes[{rid}]: placeId 不存在 {w['placeId']}")
            y = w.get("year")
            if y is not None:
                if last_year is not None and y < last_year:
                    problems.append(f"routes[{rid}]: 年份倒退于 {w['label']}")
                last_year = y
        if wps and "year" in wps[0] and wps[0]["year"] < r["from"]:
            problems.append(f"routes[{rid}]: 起点年份早于 from")

    # ---- highlights ----
    for eid, h in highlights_doc["highlights"].items():
        if eid not in event_ids:
            problems.append(f"highlights: 事件不存在 {eid}")
        for key, universe in (
            ("hydro", hydro_ids),
            ("corridors", corridor_ids),
            ("features", feature_set),
            ("routes", route_set),
            ("places", place_ids),
        ):
            for ref in h.get(key, []):
                if ref not in universe:
                    problems.append(f"highlights[{eid}].{key}: 引用不存在 {ref}")
        if not h.get("why"):
            problems.append(f"highlights[{eid}]: 缺 why")

    # ---- stories ----
    story_ids = [s["id"] for s in stories_doc["stories"]]
    if len(set(story_ids)) != len(story_ids):
        problems.append("stories: id 重复")
    for s in stories_doc["stories"]:
        sid = s["id"]
        for i, step in enumerate(s["steps"]):
            label = f"stories[{sid}].steps[{i}]"
            if step.get("eventId") and step["eventId"] not in event_ids:
                problems.append(f"{label}: eventId 不存在 {step['eventId']}")
            v = step["view"]
            if not in_range(v["lon"], v["lat"]):
                problems.append(f"{label}: view 越界")
            show = step.get("show", {})
            for key, universe in (
                ("hydro", hydro_ids),
                ("corridors", corridor_ids),
                ("features", feature_set),
                ("routes", route_set),
                ("places", place_ids),
            ):
                for ref in show.get(key, []):
                    if ref not in universe:
                        problems.append(f"{label}.show.{key}: 引用不存在 {ref}")
            if not step.get("caption"):
                problems.append(f"{label}: 缺 caption")

    # ---- atlas 新字段（ADR 0001：kind / geoWhy / placeIds）----
    kinds = {"政治", "军事", "经济", "文化", "科技", "灾害", "民族"}
    for e in atlas["events"]:
        eid = e["id"]
        if "kind" in e and e["kind"] not in kinds:
            problems.append(f"events[{eid}]: kind 不在枚举内 {e['kind']!r}")
        if "geoWhy" in e and not (10 <= len(e["geoWhy"]) <= 80):
            problems.append(f"events[{eid}]: geoWhy 应为 10–80 字，实际 {len(e['geoWhy'])}")
        if "placeIds" in e:
            ids = e["placeIds"]
            if not ids or ids[0] != e["placeId"]:
                problems.append(f"events[{eid}]: placeIds 首项须为主 placeId")
            for pid in ids:
                if pid not in place_ids:
                    problems.append(f"events[{eid}]: placeIds 不存在 {pid}")
            if len(set(ids)) != len(ids):
                problems.append(f"events[{eid}]: placeIds 有重复")

    # ---- territories：快照 ----
    terr = load("territories.json")
    snapshots: dict[str, list[dict]] = {}
    for f in terr["features"]:
        props = f.get("properties", {})
        fid = props.get("id", "?")
        if "fromYear" in props and "toYear" in props and props["toYear"] < props["fromYear"]:
            problems.append(f"territories[{fid}]: toYear < fromYear")
        ring = f["geometry"]["coordinates"][0]
        if ring[0] != ring[-1]:
            problems.append(f"territories[{fid}]: 外环未闭合")
        for lon, lat in ring:
            if not in_range(lon, lat):
                problems.append(f"territories[{fid}]: 坐标越界 {lon},{lat}")
        if props.get("kind") == "snapshot":
            snapshots.setdefault(props.get("snapshot", "?"), []).append(props)
    for snap, members in snapshots.items():
        powers = [m["power"] for m in members]
        if len(set(powers)) != len(powers):
            problems.append(f"snapshot[{snap}]: power 重复")
        if len({(m["fromYear"], m["toYear"]) for m in members}) != 1:
            problems.append(f"snapshot[{snap}]: 成员年份窗口不一致")
        for m in members:
            cap = m.get("capitalPlaceId")
            if cap and cap not in place_ids:
                problems.append(f"snapshot[{snap}]: capitalPlaceId 不存在 {cap}")

    # ---- capitals：都城迁移 ----
    caps = load("capitals.json")["capitals"]
    cap_ids = [c["id"] for c in caps]
    if len(set(cap_ids)) != len(cap_ids):
        problems.append("capitals: id 重复")
    for c in caps:
        cid = c["id"]
        if c["placeId"] not in place_ids:
            problems.append(f"capitals[{cid}]: placeId 不存在 {c['placeId']}")
        if "to" in c and c["to"] < c["from"]:
            problems.append(f"capitals[{cid}]: to < from")
        if c.get("role") not in {"main", "east", "west", "alt"}:
            problems.append(f"capitals[{cid}]: role 不合法 {c.get('role')!r}")
    # 主都覆盖：1949 年之前每个年份至少有一个主都（分裂期可多个）
    mains = [c for c in caps if c["role"] == "main"]
    for y in range(-1300, 1949, 10):
        if not any(c["from"] <= y < c.get("to", 9999) for c in mains):
            problems.append(f"capitals: {y} 年前后没有主都（允许的空档须在 note 注明）")
            break

    print(
        f"features={len(features)} routes={len(routes)} "
        f"highlights={len(highlights_doc['highlights'])} stories={len(stories_doc['stories'])} "
        f"snapshots={len(snapshots)} capitals={len(caps)}"
    )
    if problems:
        print(f"发现 {len(problems)} 个问题：")
        for p in problems:
            print("  -", p)
        return 1
    print("图层数据结构校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
