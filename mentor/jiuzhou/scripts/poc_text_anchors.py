#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""概念验证：史书原文 → 地名锚点 → 地图坐标（不用机器学习，纯词典匹配，可审计）。

做法（MARKUS 式的最小版）：
1. 取事件 `source` 里的原文页（维基文库 MediaWiki API 取纯文本），按 `loc` 里的引语定位所在段落。
2. 用「地名词典」在段落里做最长匹配：我们自己的 places（带古名区间）+ 学术层 19 个切片里的政区名（带起止年、质心）。
3. 只保留在事件年份有效的名字，输出每个锚点：地名、命中的句子、坐标、来源（places / chgis / hartwell）。
这是验证链路是否走得通的概念验证，不入应用；结论见 docs/poc/text-geo-anchors.md。

用法：python scripts/poc_text_anchors.py
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from opencc import OpenCC  # pip install opencc-python-reimplemented
    _S2T = OpenCC('s2t').convert
except ImportError:  # 没装就退回原样（定位会失败，见 poc 说明）
    _S2T = lambda t: t  # noqa: E731

ROOT = Path(__file__).resolve().parent.parent
ATLAS = ROOT / "content" / "atlas.json"
ACAD = ROOT.parent.parent / "packages" / "maps" / "geo" / "academic"
OUT = ROOT / "docs" / "poc" / "text-geo-anchors.json"
UA = "Athena-jiuzhou-poc/0.1 (personal research)"


def wikisource_text(title: str) -> str:
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1, "format": "json",
                                "formatversion": 2, "titles": title})
    req = urllib.request.Request("https://zh.wikisource.org/w/api.php?" + q, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    return data["query"]["pages"][0].get("extract", "")


def centroid(geom: dict):
    pts = []

    def walk(c):
        if isinstance(c[0], (int, float)):
            pts.append(c)
        else:
            for k in c:
                walk(k)

    walk(geom["coordinates"])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return round(sum(xs) / len(xs), 3), round(sum(ys) / len(ys), 3)


def build_gazetteer():
    """名字 → [{lon,lat,from,to,src,id}]"""
    gaz: dict[str, list[dict]] = {}
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    for p in atlas["places"]:
        for n in p.get("names", []):
            for nm in [n["name"]] + n.get("also", []):
                gaz.setdefault(nm, []).append({"lon": p["lon"], "lat": p["lat"], "from": n.get("from", -9999),
                                               "to": n.get("to", 9999), "src": "places", "id": p["id"]})
    for f in sorted(ACAD.glob("*.json")):
        if f.name == "index.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for ft in d.get("features", []):
            pr = ft["properties"]
            nm = pr.get("name")
            if not nm or len(nm) < 2:
                continue
            lon, lat = centroid(ft["geometry"])
            gaz.setdefault(nm, []).append({"lon": lon, "lat": lat, "from": pr.get("fromYear", -9999),
                                           "to": pr.get("toYear", 9999), "src": pr.get("source", "academic"),
                                           "id": pr.get("sliceId")})
    # 维基文库是繁体：每个名字再登记一份繁体写法（指向同一批候选）
    for nm in list(gaz):
        t = _S2T(nm)
        if t != nm:
            gaz.setdefault(t, []).extend(gaz[nm])
    return gaz


def match(text: str, gaz: dict, year: int):
    names = sorted(gaz, key=len, reverse=True)
    pat = re.compile("|".join(re.escape(n) for n in names if len(n) >= 2))
    found: dict[str, dict] = {}
    for m in pat.finditer(text):
        nm = m.group(0)
        cands = [c for c in gaz[nm] if c["from"] - 50 <= year <= c["to"] + 50]  # 古地名起止年有出入，放宽 50 年
        if not cands or nm in found:
            continue
        s0 = max(0, m.start() - 12)
        found[nm] = {"name": nm, "context": text[s0:m.end() + 12].replace("\n", " "), "candidates": cands[:3]}
    return list(found.values())


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    gaz = build_gazetteer()
    print(f"地名词典：{len(gaz)} 个名字", flush=True)
    report = []
    for e in atlas["events"]:
        for src in e.get("source") or []:
            url = src.get("url", "")
            m = re.search(r"wikisource\.org/wiki/(.+)$", url)
            if not m:
                continue
            title = urllib.parse.unquote(m.group(1))
            try:
                full = wikisource_text(title)
            except Exception as ex:  # noqa: BLE001
                print("取文失败", title, ex)
                continue
            loc = _S2T(src.get("loc", ""))
            # 引语在「卷…：」之后；按标点切成片段，从长到短找第一个能在原文里定位的
            body = loc.split("：", 1)[-1]
            frags = sorted((f for f in re.split(r"[，。；、「」『』]", body) if len(f) >= 4), key=len, reverse=True)
            pos = -1
            for f in frags:
                pos = full.find(f[:12])
                if pos >= 0:
                    break
            if pos >= 0:  # 只取引语所在的那一整句（句号到句号），不取前后文，减少无关地名
                a = full.rfind("。", 0, pos) + 1
                b = full.find("。", pos)
                seg = full[a:(b + 1) if b >= 0 else pos + 80]
            else:
                seg = ""
            anchors = match(seg, gaz, e["year"])
            report.append({"event": e["id"], "year": e["year"], "work": src.get("work"), "located": pos >= 0,
                           "passage": seg.replace("\n", " "), "anchors": anchors})
            print(f"{e['id']} ({e['year']}) 定位={'是' if pos>=0 else '否'} 锚点 {len(anchors)}: "
                  + "、".join(a['name'] for a in anchors), flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写出", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
