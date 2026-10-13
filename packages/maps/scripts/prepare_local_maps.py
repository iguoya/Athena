#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""准备本机学术地理层（ADR 0158）。输出到 .cache/maps/，不入库。

用法：
  python packages/maps/scripts/prepare_local_maps.py
  set ATHENA_MAPS_DATA=D:\\maps\\my-tan-pack && python ...

期望目录（任一存在即可）：
  .cache/maps/chgis/          — CHGIS/Hartwell 解压或转换后的 GeoJSON
  .cache/maps/academic/       — 自备谭图系 / GeoJSONcn 年层 *.geojson
  ATHENA_MAPS_DATA            — 同上结构的外部根

写出：
  .cache/maps/manifest.json   — 九州读取的清单
"""

from __future__ import annotations

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CACHE = REPO / ".cache" / "maps"


def collect(root: Path) -> list[dict]:
    layers: list[dict] = []
    if not root.is_dir():
        return layers
    for sub in ("academic", "chgis", "hartwell"):
        d = root / sub
        if not d.is_dir():
            continue
        for path in sorted(d.rglob("*.geojson")):
            rel = path.relative_to(root).as_posix()
            layers.append(
                {
                    "id": path.stem,
                    "path": str(path),
                    "rel": rel,
                    "source": sub,
                }
            )
        for path in sorted(d.rglob("*.json")):
            if path.name.endswith(".geojson") or path.name == "manifest.json":
                continue
            # 仅收录带 type=FeatureCollection 的
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("type") != "FeatureCollection":
                continue
            layers.append(
                {
                    "id": path.stem,
                    "path": str(path),
                    "rel": path.relative_to(root).as_posix(),
                    "source": sub,
                }
            )
    return layers


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "academic").mkdir(exist_ok=True)
    (CACHE / "chgis").mkdir(exist_ok=True)
    readme = CACHE / "README.txt"
    if not readme.is_file():
        readme.write_text(
            "本机自用学术地图缓存（ADR 0158）。勿提交 git。\n"
            "将 CHGIS / 谭图数字化 GeoJSON 放入 academic/ 或 chgis/ 后重跑 prepare_local_maps.py。\n"
            "也可设置环境变量 ATHENA_MAPS_DATA 指向外部目录。\n",
            encoding="utf-8",
        )

    layers: list[dict] = []
    layers.extend(collect(CACHE))
    external = os.environ.get("ATHENA_MAPS_DATA")
    if external:
        layers.extend(collect(Path(external)))

    # 去重 path
    seen: set[str] = set()
    uniq: list[dict] = []
    for layer in layers:
        if layer["path"] in seen:
            continue
        seen.add(layer["path"])
        uniq.append(layer)

    manifest = {
        "note": "本机学术层清单；九州有则叠、无则示意降级",
        "count": len(uniq),
        "layers": uniq,
    }
    out = CACHE / "manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} layers={len(uniq)}")
    if not uniq:
        print("HINT: drop GeoJSON under .cache/maps/academic/ or set ATHENA_MAPS_DATA")


if __name__ == "__main__":
    main()
