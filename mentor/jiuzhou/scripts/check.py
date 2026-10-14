#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jiuzhou app check: atlas structure, frontend build, Rust (ADR 0156)."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ATLAS = PROJECT_ROOT / "content" / "atlas.json"
TERRITORIES = PROJECT_ROOT / "content" / "territories.json"
# ADR 0002：第八段 contemporary（1949 至 asOf）；modern 的 id 与范围不动
EXPECTED_ERAS = 8
# ADR 0001：质量优先，禁止灌水凑字；摘要可短，一句话 lede ≤40
MIN_PROSE = 60
MAX_LEDE = 40
# 条内近义复述：字符三元组 Jaccard；0.6+ 已由内容侧删句，0.42+ 仍判为复述（须改写）
INTRA_SENT_SIM = 0.42
BOILERPLATE = (
    "地理上，关键不只是地名变动，而是交通、粮运与边防能力的重新排布。",
    "后人读史若只记年份而看不见水系与山口，就会把政治选择误当成凭空发生。",
    "把地点放回流域与走廊里看，才能理解同一条决策为何在彼时可行、在此时失灵。",
)


def _split_sents(text: str) -> list[str]:
    return [
        s.strip()
        for s in re.split(r"(?<=[。！？])", text or "")
        if len(s.strip()) >= 10
    ]


def _norm_chars(text: str) -> str:
    return re.sub(r"[，、；：。！？\s「」『』《》\u3000]", "", text)


def _trigrams(text: str) -> set[str]:
    s = _norm_chars(text)
    return {s[i : i + 3] for i in range(max(0, len(s) - 2))}


def _jaccard(a: str, b: str) -> float:
    ga, gb = _trigrams(a), _trigrams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def _intra_field_repeats(text: str) -> list[tuple[float, str, str]]:
    """同一 summary/impact 内近义复述句对。"""
    ss = _split_sents(text)
    hits: list[tuple[float, str, str]] = []
    for i in range(len(ss)):
        for j in range(i + 1, len(ss)):
            na, nb = _norm_chars(ss[i]), _norm_chars(ss[j])
            sim = _jaccard(ss[i], ss[j])
            contain = False
            if na and nb and (na in nb or nb in na):
                shorter, longer = (na, nb) if len(na) <= len(nb) else (nb, na)
                contain = len(shorter) / max(1, len(longer)) >= 0.55
            if sim >= INTRA_SENT_SIM or contain:
                hits.append((sim if not contain else max(sim, 0.99), ss[i], ss[j]))
    return hits


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"missing tool: {name}")
    return found


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def check_atlas() -> None:
    print("== atlas structure ==", flush=True)
    data = json.loads(ATLAS.read_text(encoding="utf-8"))
    problems: list[str] = []

    eras = data.get("eras") or []
    if len(eras) != EXPECTED_ERAS:
        problems.append(f"eras expected {EXPECTED_ERAS}, got {len(eras)}")
    era_ids = {e.get("id") for e in eras}
    if len(era_ids) != len(eras):
        problems.append("duplicate eras.id")

    places = data.get("places") or []
    place_ids = {p.get("id") for p in places}
    if len(place_ids) != len(places):
        problems.append("duplicate places.id")
    for p in places:
        pid = p.get("id", "?")
        if not isinstance(p.get("lon"), (int, float)) or not isinstance(
            p.get("lat"), (int, float)
        ):
            problems.append(f"places[{pid}]: missing lon/lat")
        names = p.get("names") or []
        if not names:
            problems.append(f"places[{pid}]: empty names")
        for n in names:
            if "from" not in n or "name" not in n:
                problems.append(f"places[{pid}]: names need from/name")

    events = data.get("events") or []
    event_ids = {e.get("id") for e in events}
    if len(event_ids) != len(events):
        problems.append("duplicate events.id")
    for e in events:
        eid = e.get("id", "?")
        if e.get("eraId") not in era_ids:
            problems.append(f"events[{eid}]: bad eraId")
        if e.get("placeId") not in place_ids:
            problems.append(f"events[{eid}]: bad placeId")
        for key in ("year", "title", "summary", "impact"):
            if key not in e:
                problems.append(f"events[{eid}]: missing {key}")
        if len(e.get("summary") or "") < MIN_PROSE:
            problems.append(f"events[{eid}]: summary too short (<{MIN_PROSE})")
        if len(e.get("impact") or "") < MIN_PROSE:
            problems.append(f"events[{eid}]: impact too short (<{MIN_PROSE})")
        lede = e.get("lede") or ""
        if lede and len(lede) > MAX_LEDE:
            problems.append(f"events[{eid}]: lede too long (>{MAX_LEDE})")
        for boiler in BOILERPLATE:
            if boiler in (e.get("summary") or "") or boiler in (e.get("impact") or ""):
                problems.append(f"events[{eid}]: boilerplate pad prose (ADR 0001)")
                break
        for field in ("summary", "impact"):
            for sim, _a, _b in _intra_field_repeats(e.get(field) or ""):
                problems.append(
                    f"events[{eid}]: {field} has near-duplicate sentences "
                    f"(sim={sim:.2f}; rewrite, do not pad)"
                )
                break
        leads = e.get("leadsTo") or []
        if not isinstance(leads, list):
            problems.append(f"events[{eid}]: leadsTo must be list")
        else:
            for lid in leads:
                if lid not in event_ids:
                    problems.append(f"events[{eid}]: leadsTo {lid!r} missing")

    people = data.get("people") or []
    person_ids = {p.get("id") for p in people if p.get("id")}
    for e in events:
        for pid in e.get("personIds") or []:
            if pid and pid not in person_ids:
                problems.append(
                    f"events[{e.get('id')}]: personIds {pid!r} not in people"
                )

    feats: list = []
    if not TERRITORIES.is_file():
        problems.append("missing content/territories.json")
    else:
        terr = json.loads(TERRITORIES.read_text(encoding="utf-8"))
        if terr.get("type") != "FeatureCollection":
            problems.append("territories.json must be FeatureCollection")
        feats = terr.get("features") or []
        terr_ids = {(f.get("properties") or {}).get("id") for f in feats}
        for e in eras:
            tid = e.get("territoryId")
            if tid and tid not in terr_ids:
                problems.append(
                    f"eras[{e.get('id')}]: territoryId {tid!r} not in territories"
                )

    if problems:
        for p in problems:
            print(f"  {p}")
        raise SystemExit(f"atlas: {len(problems)} problems")

    print(
        f"{len(eras)} eras / {len(places)} places / {len(events)} events / "
        f"{len(people)} people / {len(feats)} territories",
        flush=True,
    )


def check_derived_geo() -> None:
    """T-030：派生 GeoJSON 不得比源文件旧。"""
    print("== derived geo freshness ==", flush=True)
    repo = PROJECT_ROOT.parents[1]
    problems: list[str] = []

    terr_src = PROJECT_ROOT / "content" / "territories.json"
    terr_out = repo / "packages" / "maps" / "geo" / "territories-clipped.json"
    if not terr_out.is_file():
        problems.append(
            "missing packages/maps/geo/territories-clipped.json — "
            "run: python packages/maps/scripts/clip_territories.py"
        )
    elif terr_src.is_file() and terr_src.stat().st_mtime > terr_out.stat().st_mtime + 1.0:
        problems.append(
            "content/territories.json is newer than territories-clipped.json — "
            "re-run: python packages/maps/scripts/clip_territories.py"
        )

    land_out = repo / "packages" / "maps" / "geo" / "land.json"
    build_script = repo / "packages" / "maps" / "scripts" / "build_base_layers.py"
    if not land_out.is_file():
        problems.append(
            "missing packages/maps/geo/land.json — "
            "run: python packages/maps/scripts/build_base_layers.py"
        )
    elif (
        build_script.is_file()
        and build_script.stat().st_mtime > land_out.stat().st_mtime + 1.0
    ):
        problems.append(
            "packages/maps/scripts/build_base_layers.py is newer than land.json — "
            "re-run: python packages/maps/scripts/build_base_layers.py"
        )

    if problems:
        for p in problems:
            print(f"  {p}")
        raise SystemExit(f"derived geo: {len(problems)} problems")
    print("territories-clipped / land.json OK", flush=True)


def ensure_dependencies() -> None:
    if (PROJECT_ROOT / "node_modules").is_dir():
        return
    pnpm = tool("pnpm")
    repo_lock = PROJECT_ROOT.parents[1] / "pnpm-lock.yaml"
    if (PROJECT_ROOT / "pnpm-lock.yaml").is_file() or repo_lock.is_file():
        run([pnpm, "install", "--frozen-lockfile"], "install deps (lock)")
    else:
        run([pnpm, "install"], "install deps")


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="check jiuzhou app")
    parser.add_argument("--skip-rust", action="store_true", help="skip Rust check")
    arguments = parser.parse_args()

    check_atlas()
    check_derived_geo()
    run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "check_layers.py")],
        "layer overlays",
    )
    ensure_dependencies()
    run([tool("pnpm"), "run", "build"], "frontend build")
    run([tool("node"), str(PROJECT_ROOT / "scripts" / "smoke_dist.mjs")], "smoke dist")
    if not arguments.skip_rust:
        run(
            [
                tool("cargo"),
                "check",
                "--manifest-path",
                "src-tauri/Cargo.toml",
                "--all-targets",
            ],
            "Rust check",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
