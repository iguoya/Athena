#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Natural Earth 河流加密本机河网（输出到 .cache，不入库）。

1. 下载（CC0）到 .cache/maps/natural-earth/：
   https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.zip
2. 需要 pyshp 或 geopandas 之一；有则裁切中国范围并按名称匹配主干河。
3. 写出 .cache/maps/hydro-dense.json；九州若读到则叠在示意层上（见 README）。

无依赖 / 未下载时只打印指引并退出 0（不挡 check）。
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CACHE = REPO / ".cache" / "maps"
NE_DIR = CACHE / "natural-earth"
OUT = CACHE / "hydro-dense.json"

# 名称子串 → 输出 id（Natural Earth name_zh / name 字段不一，多试几个）
TARGETS = {
    "huanghe": ("Yellow", "Huang He", "黄河"),
    "changjiang": ("Yangtze", "Chang Jiang", "长江"),
    "huaihe": ("Huai", "淮河"),
    "zhujiang": ("Pearl", "Xi Jiang", "珠江", "西江"),
    "haihe": ("Hai", "海河"),
    "liaohe": ("Liao", "辽河"),
    "songhuajiang": ("Songhua", "松花江"),
    "lancangjiang": ("Mekong", "Lancang", "澜沧江"),
    "yarlung": ("Brahmaputra", "Yarlung", "雅鲁藏布"),
}

BBOX = (73.0, 18.0, 135.5, 54.0)  # 中国粗框


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    zips = list(NE_DIR.glob("ne_10m_rivers*.zip"))
    shps = list(NE_DIR.rglob("ne_10m_rivers_lake_centerlines.shp"))
    if not zips and not shps:
        print(
            "未找到 Natural Earth 河流包。\n"
            f"请下载到 {NE_DIR}/ ：\n"
            "  https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.zip\n"
            "然后重跑本脚本。仓库内 packages/maps/geo/hydro.json 已是加密后的示意版。"
        )
        return 0

    try:
        import shapefile  # type: ignore
    except ImportError:
        print("需要 pyshp：pip install pyshp")
        return 0

    if not shps and zips:
        with zipfile.ZipFile(zips[0]) as zf:
            zf.extractall(NE_DIR / "extracted")
        shps = list((NE_DIR / "extracted").rglob("ne_10m_rivers_lake_centerlines.shp"))
    if not shps:
        print("解压后仍无 .shp")
        return 0

    sf = shapefile.Reader(str(shps[0]))
    fields = [f[0] for f in sf.fields[1:]]
    features = []
    for sr in sf.iterShapeRecords():
        rec = {fields[i]: sr.record[i] for i in range(len(fields))}
        name = " ".join(
            str(rec.get(k) or "") for k in ("name", "name_en", "name_zh", "name_alt")
        )
        matched = None
        for rid, keys in TARGETS.items():
            if any(k.lower() in name.lower() for k in keys):
                matched = rid
                break
        if not matched:
            continue
        geom = sr.shape
        if geom.shapeType not in (3, 5, 13, 15):  # polyline variants
            continue
        for part_i, start in enumerate(geom.parts):
            end = geom.parts[part_i + 1] if part_i + 1 < len(geom.parts) else len(geom.points)
            coords = []
            for x, y in geom.points[start:end]:
                if BBOX[0] <= x <= BBOX[2] and BBOX[1] <= y <= BBOX[3]:
                    coords.append([round(x, 4), round(y, 4)])
            if len(coords) < 4:
                continue
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "id": matched,
                        "name": name.strip() or matched,
                        "kind": "river",
                        "source": "natural-earth-10m",
                    },
                    "geometry": {"type": "LineString", "coordinates": coords},
                }
            )

    doc = {
        "_note": "Natural Earth 裁切加密河网，本机 .cache，不入库。",
        "type": "FeatureCollection",
        "features": features,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} features={len(features)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
