#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 Natural Earth 10m 河流中心线（公域）重建主干河，写进 geo/hydro.json。

为什么：手绘示意折线在中游偏出 100–350 km（黄河直接切过山西、长江下荆江截弯取直），
与晕渲底板、城市坐标对不上。NE 的河流中心线是沿真实河道测的，主干河改用它。

做法：NE 的一条河由若干零散线段加湖区汊道构成，不能直接首尾相连；这里把线段建成图，
取源头到入海口的最短路径作主干（自动舍掉鄱阳湖、洞庭湖那类汊道环），再用 Douglas-Peucker
简化到约 0.01°（≈1 km）。

用法：
  1. 下载 https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.zip
     放到 .cache/maps/natural-earth/（脚本自己解压）
  2. python packages/maps/scripts/densify_hydro.py
     → 覆盖 packages/maps/geo/hydro.json 里的 huanghe / changjiang 两条
  3. 九州另有一份 mentor/jiuzhou/content/hydro.json（黄河只画到郑州，下游由分期河道接续）；
     加 --jiuzhou 一并改写它与 features.json 里的现行河道与各分期起点。

需要 pyshp、shapely。
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
NE_DIR = REPO / ".cache" / "maps" / "natural-earth"
GEO_HYDRO = REPO / "packages" / "maps" / "geo" / "hydro.json"
JZ_HYDRO = REPO / "mentor" / "jiuzhou" / "content" / "hydro.json"
JZ_FEATURES = REPO / "mentor" / "jiuzhou" / "content" / "features.json"

SIMPLIFY_DEG = 0.01
BRIDGE_DEG = 0.1
# 黄河上下游的分界：荥阳广武山一带，之后历代河道各走各的（features.json 的 hr-*）
YELLOW_SPLIT_LON = 113.4

# id → (NE 名称谓词, 源头附近, 入海口附近, 末端手工延伸)
# 长江 NE 在镇江（119.6°E）就停了，崇明段用手工路标接到口外，下游宽江面里中心线本就是示意
STEMS = {
    "huanghe": dict(
        names={"Yellow", "Huang"},
        src=(96.16, 35.13),
        dst=(119.2, 37.8),
        tail=[],
    ),
    "changjiang": dict(
        names={"Yangtze", "Jinsha", "Tongtian", "Tuotuo He"},
        src=(90.79, 34.30),
        dst=(119.6, 32.2),
        tail=[[120.28, 31.92], [120.7, 31.95], [121.1, 31.8], [121.6, 31.55], [121.9, 31.4]],
    ),
}


def load_reader():
    import shapefile  # pyshp

    shps = list(NE_DIR.rglob("ne_10m_rivers_lake_centerlines.shp"))
    if not shps:
        zips = list(NE_DIR.glob("ne_10m_rivers_lake_centerlines.zip"))
        if not zips:
            sys.exit(f"未找到 NE 河流包，请按文件头说明下载到 {NE_DIR}/")
        out = NE_DIR / "rivers10"
        with zipfile.ZipFile(zips[0]) as zf:
            zf.extractall(out)
        shps = list(out.rglob("ne_10m_rivers_lake_centerlines.shp"))
    return shapefile.Reader(str(shps[0]), encoding="utf-8")


def key(p):
    return (round(p[0], 5), round(p[1], 5))


def shortest_path(reader, names, src, dst):
    adj: dict[tuple, list] = {}
    ends = []
    for sr in reader.iterShapeRecords():
        d = sr.record.as_dict()
        if d["name_en"] not in names and d["name"] not in names:
            continue
        pts = sr.shape.points
        bounds = list(sr.shape.parts) + [len(pts)]
        for a, b in zip(bounds, bounds[1:]):
            seg = [key(p) for p in pts[a:b]]
            ends += [seg[0], seg[-1]]
            for p, q in zip(seg, seg[1:]):
                w = math.hypot(p[0] - q[0], p[1] - q[1])
                adj.setdefault(p, []).append((q, w))
                adj.setdefault(q, []).append((p, w))
    # 相邻两条线段的端点在 NE 里常差几百米而不重合，按 BRIDGE_DEG 内就近接上
    for i, p in enumerate(ends):
        for q in ends[i + 1 :]:
            w = math.hypot(p[0] - q[0], p[1] - q[1])
            if 0 < w <= BRIDGE_DEG:
                adj.setdefault(p, []).append((q, w))
                adj.setdefault(q, []).append((p, w))
    nodes = list(adj)

    def near(t):
        return min(nodes, key=lambda n: (n[0] - t[0]) ** 2 + (n[1] - t[1]) ** 2)

    s, e = near(src), near(dst)
    dist = {s: 0.0}
    prev: dict = {}
    heap = [(0.0, s)]
    while heap:
        d0, u = heapq.heappop(heap)
        if u == e:
            break
        if d0 > dist.get(u, 1e18):
            continue
        for v, w in adj[u]:
            nd = d0 + w
            if nd < dist.get(v, 1e18):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    if e not in dist:
        sys.exit(f"{names}: 源头与入海口在 NE 数据里不连通，检查 src/dst")
    path = [e]
    while path[-1] != s:
        path.append(prev[path[-1]])
    return [list(p) for p in reversed(path)]


def simplify(coords):
    from shapely.geometry import LineString

    line = LineString(coords).simplify(SIMPLIFY_DEG, preserve_topology=False)
    return [[round(x, 3), round(y, 3)] for x, y in line.coords]


def replace_coords(text: str, rid: str, coords) -> str:
    """只替换某个 id 后第一个 "coordinates" 数组，不动文件其余格式。"""
    i = text.index(f'"id": "{rid}"')
    j = text.index('"coordinates": [', i) + len('"coordinates": ')
    depth, k = 0, j
    while True:
        c = text[k]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                break
        k += 1
    out = text[:j] + json.dumps(coords) + text[k + 1 :]
    json.loads(out)
    return out


def split_yellow(coords):
    """按经度切成上游（到 YELLOW_SPLIT_LON）与下游（含分界点到入海）。

    黄河过了潼关向东，经度单调增到 114.8°（东坝头）才折向东北，所以首次越过分界经度
    的位置唯一。
    """
    for i in range(1, len(coords)):
        if coords[i][0] >= YELLOW_SPLIT_LON > coords[i - 1][0]:
            (x0, y0), (x1, y1) = coords[i - 1], coords[i]
            t = (YELLOW_SPLIT_LON - x0) / (x1 - x0)
            cut = [round(YELLOW_SPLIT_LON, 3), round(y0 + t * (y1 - y0), 3)]
            return coords[:i] + [cut], [cut] + coords[i:]
    sys.exit("黄河线没有越过分界经度")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jiuzhou", action="store_true", help="同时改写九州的 hydro.json 与 features.json")
    args = ap.parse_args()

    reader = load_reader()
    stems = {}
    for rid, cfg in STEMS.items():
        path = shortest_path(reader, cfg["names"], cfg["src"], cfg["dst"])
        stems[rid] = simplify(path + cfg["tail"])
        print(f"{rid}: {len(path)} → {len(stems[rid])} 点")

    text = GEO_HYDRO.read_text(encoding="utf-8", newline="")
    for rid, coords in stems.items():
        text = replace_coords(text, rid, coords)
    GEO_HYDRO.write_text(text, encoding="utf-8", newline="")
    print(f"已写 {GEO_HYDRO.relative_to(REPO)}")

    if args.jiuzhou:
        up, down = split_yellow(stems["huanghe"])
        cut = down[0]
        text = JZ_HYDRO.read_text(encoding="utf-8", newline="")
        text = replace_coords(text, "huanghe", up)
        text = replace_coords(text, "changjiang", stems["changjiang"])
        JZ_HYDRO.write_text(text, encoding="utf-8", newline="")

        text = JZ_FEATURES.read_text(encoding="utf-8", newline="")
        fe = json.loads(text)
        starts = {"hr-ancient", "hr-han-tang", "hr-song-north", "hr-yuan-ming"}
        for x in fe["features"]:
            if x["id"] in starts:
                c = [list(p) for p in x["geometry"]["coordinates"]]
                c[0] = cut
                text = replace_coords(text, x["id"], c)
            elif x["id"] == "hr-modern":
                text = replace_coords(text, "hr-modern", down)
        JZ_FEATURES.write_text(text, encoding="utf-8", newline="")
        print(f"已写九州 hydro.json / features.json，分界点 {cut}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
