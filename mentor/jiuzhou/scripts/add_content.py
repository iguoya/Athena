#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把一份 JSON 里的新事件 / 地点 / 人物校验后并入 content/atlas.json。

用法：
  python scripts/add_content.py batch.json            # 只校验，不写入（默认）
  python scripts/add_content.py batch.json --apply    # 校验通过后写入

batch.json 形如：
  {"events": [...], "places": [...], "people": [...]}      # 三个键都可省略

校验规则与 scripts/check.py 同源（质量优先、不灌水）；写入时：
  - 事件按「同一阶段内第一个年份更晚的事件之前」插入，不整体重排；
  - 根据人物 name / aliases 回填 personIds；
  - 格式保持 2 空格缩进、不转义中文、末尾换行，保证 git diff 干净。
一个 id 只装一个东西，已存在的 id 一律拒绝（不覆盖、不改嫁）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ATLAS = Path(__file__).resolve().parent.parent / "content" / "atlas.json"

KINDS = {"政治", "军事", "经济", "文化", "科技", "灾害", "民族"}
TIERS = {"capital", "metropolis", "pass", "prefecture", "other"}
MAX_LEDE = 40
MIN_PROSE = 60


def err(problems: list[str], msg: str) -> None:
    problems.append(msg)


def validate_places(new, data, problems):
    have = {p["id"] for p in data["places"]}
    seen = set()
    for p in new:
        pid = p.get("id", "?")
        if pid in have or pid in seen:
            err(problems, f"places[{pid}]: id 已存在")
        seen.add(pid)
        for k in ("id", "modern", "lon", "lat", "tier", "names"):
            if k not in p:
                err(problems, f"places[{pid}]: 缺 {k}")
        if p.get("tier") not in TIERS:
            err(problems, f"places[{pid}]: tier 须为 {sorted(TIERS)}")
        lon, lat = p.get("lon"), p.get("lat")
        if not (isinstance(lon, (int, float)) and isinstance(lat, (int, float))):
            err(problems, f"places[{pid}]: lon/lat 须为数字")
        elif not (70 <= lon <= 145 and 5 <= lat <= 56):
            err(problems, f"places[{pid}]: 坐标超出东亚范围 {lon},{lat}")
        names = p.get("names") or []
        if not names:
            err(problems, f"places[{pid}]: names 不能为空")
        for n in names:
            if "from" not in n or "name" not in n:
                err(problems, f"places[{pid}]: names 每项需 from/name")
            if "to" in n and n["to"] < n["from"]:
                err(problems, f"places[{pid}]: names.to < from")
        if p.get("tier") in {"capital", "metropolis", "pass"} and not p.get("role"):
            err(problems, f"places[{pid}]: capital/metropolis/pass 须写 role（为何在图上重要）")
    return seen


def validate_people(new, data, problems):
    have = {p["id"] for p in data["people"]}
    names = {p["name"] for p in data["people"]}
    seen = set()
    for p in new:
        pid = p.get("id", "?")
        if pid in have or pid in seen:
            err(problems, f"people[{pid}]: id 已存在")
        if p.get("name") in names:
            err(problems, f"people[{pid}]: 同名人物已存在 {p.get('name')}")
        seen.add(pid)
        for k in ("id", "name", "years", "blurb"):
            if not p.get(k):
                err(problems, f"people[{pid}]: 缺 {k}")
        if len(p.get("blurb", "")) > 60:
            err(problems, f"people[{pid}]: blurb 过长（>60 字），应一句话")
    return seen


def validate_events(new, data, new_places, problems):
    have = {e["id"] for e in data["events"]}
    place_ids = {p["id"] for p in data["places"]} | new_places
    eras = {e["id"]: e for e in data["eras"]}
    new_ids = {e.get("id") for e in new}
    seen = set()
    for e in new:
        eid = e.get("id", "?")
        if eid in have or eid in seen:
            err(problems, f"events[{eid}]: id 已存在")
        seen.add(eid)
        for k in ("id", "eraId", "year", "placeId", "title", "summary", "impact", "lede", "kind"):
            if k not in e:
                err(problems, f"events[{eid}]: 缺 {k}")
        if e.get("eraId") not in eras:
            err(problems, f"events[{eid}]: eraId 不存在")
        else:
            er = eras[e["eraId"]]
            if not (er["from"] <= e.get("year", 10**9) <= er["to"]):
                err(problems, f"events[{eid}]: 年份不在阶段 {er['id']} 范围内")
        if e.get("placeId") not in place_ids:
            err(problems, f"events[{eid}]: placeId 不存在 {e.get('placeId')}")
        if e.get("kind") not in KINDS:
            err(problems, f"events[{eid}]: kind 须为 {sorted(KINDS)}")
        if len(e.get("lede", "")) > MAX_LEDE:
            err(problems, f"events[{eid}]: lede 超过 {MAX_LEDE} 字")
        for f in ("summary", "impact"):
            if len(e.get(f, "")) < MIN_PROSE:
                err(problems, f"events[{eid}]: {f} 少于 {MIN_PROSE} 字")
        geo = e.get("geoWhy")
        if geo is not None and not (10 <= len(geo) <= 80):
            err(problems, f"events[{eid}]: geoWhy 须 10–80 字")
        for l in e.get("leadsTo", []):
            if l not in have and l not in new_ids:
                err(problems, f"events[{eid}]: leadsTo 不存在 {l}")
        pids = e.get("placeIds")
        if pids is not None:
            if not pids or pids[0] != e.get("placeId"):
                err(problems, f"events[{eid}]: placeIds 首项须为主 placeId")
            for p in pids:
                if p not in place_ids:
                    err(problems, f"events[{eid}]: placeIds 不存在 {p}")
        src = e.get("source")
        if src is not None and not (isinstance(src, list) and all(isinstance(s, dict) and s.get("work") for s in src)):
            err(problems, f"events[{eid}]: source 须为 [{{work, loc?, url?}}] 列表")


def insert_event(events, ev):
    idx = None
    last = None
    for i, e in enumerate(events):
        if e["eraId"] == ev["eraId"]:
            last = i
            if e["year"] > ev["year"] and idx is None:
                idx = i
    if idx is None:
        idx = (last + 1) if last is not None else len(events)
    events.insert(idx, ev)


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch", type=Path)
    ap.add_argument("--apply", action="store_true", help="校验通过后写入 atlas.json")
    args = ap.parse_args()

    batch = json.loads(args.batch.read_text(encoding="utf-8"))
    data = json.loads(ATLAS.read_text(encoding="utf-8"))
    problems: list[str] = []

    new_places = validate_places(batch.get("places", []), data, problems)
    validate_people(batch.get("people", []), data, problems)
    validate_events(batch.get("events", []), data, new_places, problems)

    if problems:
        print(f"校验失败，{len(problems)} 个问题（未写入任何内容）：")
        for p in problems:
            print("  -", p)
        return 1

    print(
        f"校验通过：events +{len(batch.get('events', []))}、"
        f"places +{len(batch.get('places', []))}、people +{len(batch.get('people', []))}"
    )
    if not args.apply:
        print("（演练模式，未写入；确认无误后加 --apply）")
        return 0

    data["places"].extend(batch.get("places", []))
    data["people"].extend(batch.get("people", []))
    lookup: dict[str, str] = {}
    for p in data["people"]:
        lookup.setdefault(p["name"], p["id"])
        for a in p.get("aliases", []):
            lookup.setdefault(a, p["id"])
    for ev in batch.get("events", []):
        ev.setdefault("people", [])
        ev.setdefault("leadsTo", [])
        ev.setdefault("dynastyTag", "")
        ids = list(ev.get("personIds") or [])
        for n in ev["people"]:
            pid = lookup.get(n)
            if pid and pid not in ids:
                ids.append(pid)
        ev["personIds"] = ids
        insert_event(data["events"], ev)
    ATLAS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {ATLAS.name}；现有 events={len(data['events'])} places={len(data['places'])} people={len(data['people'])}")
    print("请接着运行：python scripts/check.py --skip-rust")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
