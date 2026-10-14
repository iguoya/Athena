#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下载并整理学术层历史政区 GeoJSON → packages/maps/geo/academic/

依据 ADR 0159：网上能取到的数据直接入库。本脚本可重跑。

官方 CHGIS V6 / Hartwell 在 Harvard Dataverse；本环境访问其 API/页面会被
AWS WAF 拦成 robots.txt。因此默认从公开仓库
https://github.com/pessimistcamellia/china-history-map 的 v2/data/geo/ 拉取
已转成 WGS84、按朝代切好的切片（DEVLOG 写明：秦汉等来自 CHGIS V6
v6_time_pref_pgn_utf_wgs84；唐宋元明等来自 Hartwell GIS v5）。

若本机已把官方 zip 放到 .cache/maps/chgis/，可用 --from-cache 路径扩展
（当前版本先落地公开切片；官方 shapefile 管线待 Dataverse 可达时补）。
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CACHE = REPO / ".cache" / "maps" / "chgis"
OUT = REPO / "packages" / "maps" / "geo" / "academic"

# 公开镜像（china-history-map / ChanceChen12）
MIRROR_BASE = (
    "https://raw.githubusercontent.com/pessimistcamellia/"
    "china-history-map/main/v2/data/geo/"
)

# 官方入口（出处登记；自动化下载当前会被 WAF 拦截）
OFFICIAL = {
    "chgis_site": "https://chgis.fas.harvard.edu/data/chgis/v6/",
    "chgis_dataverse": "https://dataverse.harvard.edu/dataverse/chgis_v6",
    "pref_polygons_doi": "doi:10.7910/DVN/I0Q7SM",
    "pref_polygons_file": "v6_time_pref_pgn_utf_wgs84.zip",
    "hartwell_doi": "doi:10.7910/DVN/29302",
    "mirror_repo": "https://github.com/pessimistcamellia/china-history-map",
    "mirror_devlog": (
        "https://raw.githubusercontent.com/pessimistcamellia/"
        "china-history-map/main/DEVLOG.md"
    ),
}

# 只收中国历史政区切片，不收 world_*（aourednik）与现代示意无关层
SLICES: list[dict] = [
    {
        "id": "qin",
        "remote": "qin.json",
        "fromYear": -221,
        "toYear": -206,
        "lineage": "chgis-v6",
        "title": "秦",
    },
    {
        "id": "han-west",
        "remote": "han_w.json",
        "fromYear": -206,
        "toYear": 9,
        "lineage": "chgis-v6",
        "title": "西汉",
    },
    {
        "id": "han-east",
        "remote": "han_e.json",
        "fromYear": 25,
        "toYear": 220,
        "lineage": "chgis-v6",
        "title": "东汉",
    },
    {
        "id": "three-kingdoms",
        "remote": "three_k.json",
        "fromYear": 220,
        "toYear": 280,
        "lineage": "chgis-v6",
        "title": "三国",
    },
    {
        "id": "jin-west",
        "remote": "jin_w.json",
        "fromYear": 265,
        "toYear": 316,
        "lineage": "chgis-v6",
        "title": "西晋",
    },
    {
        "id": "southern-northern",
        "remote": "south_n.json",
        "fromYear": 420,
        "toYear": 589,
        "lineage": "chgis-v6",
        "title": "南北朝",
    },
    {
        "id": "sui",
        "remote": "sui.json",
        "fromYear": 581,
        "toYear": 618,
        "lineage": "chgis-v6",
        "title": "隋",
    },
    {
        "id": "five-dynasties",
        "remote": "five_d.json",
        "fromYear": 907,
        "toYear": 960,
        "lineage": "chgis-v6",
        "title": "五代",
    },
    {
        "id": "tang",
        "remote": "tang.json",
        "fromYear": 618,
        "toYear": 907,
        "lineage": "hartwell-v5",
        "title": "唐",
    },
    {
        "id": "song-liao",
        "remote": "song_liao.json",
        "fromYear": 960,
        "toYear": 1127,
        "lineage": "hartwell-v5",
        "title": "北宋/辽",
    },
    {
        "id": "liao",
        "remote": "liao.json",
        "fromYear": 907,
        "toYear": 1125,
        "lineage": "hartwell-v5",
        "title": "辽",
    },
    {
        "id": "song-jin",
        "remote": "song_jin.json",
        "fromYear": 1127,
        "toYear": 1279,
        "lineage": "hartwell-v5",
        "title": "南宋/金",
    },
    {
        "id": "jin",
        "remote": "jin_dy.json",
        "fromYear": 1115,
        "toYear": 1234,
        "lineage": "hartwell-v5",
        "title": "金",
    },
    {
        "id": "xixia",
        "remote": "xixia.json",
        "fromYear": 1038,
        "toYear": 1227,
        "lineage": "hartwell-v5",
        "title": "西夏",
    },
    {
        "id": "xixia-1200",
        "remote": "xixia_1200.json",
        "fromYear": 1200,
        "toYear": 1200,
        "lineage": "hartwell-v5",
        "title": "西夏（1200 切片）",
    },
    {
        "id": "yuan",
        "remote": "yuan.json",
        "fromYear": 1271,
        "toYear": 1368,
        "lineage": "hartwell-v5",
        "title": "元",
    },
    {
        "id": "ming",
        "remote": "ming.json",
        "fromYear": 1368,
        "toYear": 1644,
        "lineage": "hartwell-v5",
        "title": "明",
    },
    {
        "id": "qing",
        "remote": "qing.json",
        "fromYear": 1644,
        "toYear": 1911,
        "lineage": "chgis-v6",
        "title": "清",
    },
    {
        "id": "republic",
        "remote": "republic.json",
        "fromYear": 1912,
        "toYear": 1949,
        "lineage": "chgis-v6",
        "title": "民国",
    },
]


def http_get(url: str, dest: Path | None = None) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Athena-maps-fetch_academic/1.0 (+personal research)",
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    return data


def probe_dataverse() -> dict:
    """探测官方 Dataverse 是否可达；当前常见结果是 WAF 返回 robots.txt。"""
    url = (
        "https://dataverse.harvard.edu/api/datasets/:persistentId/"
        f"?persistentId={OFFICIAL['pref_polygons_doi']}"
    )
    try:
        raw = http_get(url)
        text = raw[:200].decode("utf-8", errors="replace")
        if text.lstrip().startswith("User-agent:"):
            return {
                "ok": False,
                "reason": "aws-waf-robots-txt",
                "url": url,
            }
        json.loads(raw)
        return {"ok": True, "url": url}
    except Exception as exc:  # noqa: BLE001 — 探测失败即记原因
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}", "url": url}


def normalize_feature(feat: dict, slice_meta: dict) -> dict:
    props = dict(feat.get("properties") or {})
    beg = props.get("beg_yr", props.get("BEG_YR", props.get("fromYear")))
    end = props.get("end_yr", props.get("END_YR", props.get("toYear")))
    if beg is None:
        beg = slice_meta["fromYear"]
    if end is None:
        end = slice_meta["toYear"]
    name = props.get("name") or props.get("NAME_CH") or props.get("NAME") or ""
    name_py = props.get("name_py") or props.get("NAME_PY") or props.get("PINYIN") or ""
    type_ch = props.get("type_ch") or props.get("TYPE_CH") or props.get("TYPE") or ""
    sys_id = props.get("sys_id") or props.get("SYS_ID") or props.get("BO_ID")
    out_props = {
        "name": name,
        "name_py": name_py,
        "type_ch": type_ch,
        "beg_yr": beg,
        "end_yr": end,
        "fromYear": beg,
        "toYear": end,
        "source": slice_meta["lineage"],
        "sliceId": slice_meta["id"],
        "sliceTitle": slice_meta["title"],
    }
    if sys_id is not None:
        out_props["sys_id"] = sys_id
    return {
        "type": "Feature",
        "properties": out_props,
        "geometry": feat.get("geometry"),
    }


def process_slice(meta: dict) -> dict:
    remote = meta["remote"]
    cache_path = CACHE / "mirror" / remote
    url = MIRROR_BASE + remote
    print(f"GET {url}")
    try:
        raw = http_get(url, cache_path)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"下载失败 {remote}: HTTP {exc.code}") from exc
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"下载失败 {remote}: {exc}") from exc

    data = json.loads(raw.decode("utf-8"))
    feats = [normalize_feature(f, meta) for f in data.get("features") or []]
    feats = [f for f in feats if f.get("geometry")]
    out_name = f"{meta['id']}.json"
    out_path = OUT / out_name
    fc = {
        "type": "FeatureCollection",
        "name": meta["id"],
        "features": feats,
    }
    out_path.write_text(
        json.dumps(fc, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    size = out_path.stat().st_size
    return {
        "id": meta["id"],
        "file": out_name,
        "title": meta["title"],
        "fromYear": meta["fromYear"],
        "toYear": meta["toYear"],
        "lineage": meta["lineage"],
        "featureCount": len(feats),
        "bytes": size,
        "remote": remote,
    }


def write_sources(index: dict, probe: dict) -> None:
    lines = [
        "# 学术层来源（packages/maps/geo/academic）",
        "",
        f"核对日期：{index['fetchedAt']}",
        "",
        "## 官方入口（原文）",
        "",
        f"- CHGIS V6 说明：{OFFICIAL['chgis_site']}",
        f"- Dataverse 集合：{OFFICIAL['chgis_dataverse']}",
        f"- 时序府级面：`{OFFICIAL['pref_polygons_file']}`，"
        f"{OFFICIAL['pref_polygons_doi']}",
        f"- Hartwell GIS v5：{OFFICIAL['hartwell_doi']}",
        "",
        "## 本批实际下载路径",
        "",
        "Harvard Dataverse 在本机自动化访问时被 AWS WAF 拦截"
        "（API 返回 `robots.txt` 正文，浏览器页同样空白）。",
        f"探测结果：`ok={probe.get('ok')}` · `reason={probe.get('reason')}`。",
        "",
        "因此本批从公开镜像拉取已转好的朝代切片：",
        f"- 仓库：{OFFICIAL['mirror_repo']}",
        f"- 路径：`v2/data/geo/<slice>.json`",
        f"- 镜像方说明（DEVLOG）：{OFFICIAL['mirror_devlog']}",
        "",
        "镜像方声明的谱系（摘录）：",
        "- 秦汉等早期：CHGIS V6 `v6_time_pref_pgn_utf_wgs84`（WGS84）",
        "- 唐宋元明等：Hartwell GIS v5（已由镜像方转 WGS84）",
        "- 几何曾做过 Douglas-Peucker 简化（非官方原精度）",
        "",
        "## 字段映射（要素属性）",
        "",
        "| 入库字段 | 含义 | 来自镜像 |",
        "|---|---|---|",
        "| `name` | 政区中文名 | `name` |",
        "| `name_py` | 拼音 | `name_py` |",
        "| `type_ch` | 政区类型（郡/州/府…） | `type_ch` |",
        "| `beg_yr` / `fromYear` | 存续起年（CE，负数为前） | `beg_yr`；缺则用切片年 |",
        "| `end_yr` / `toYear` | 存续止年 | `end_yr`；缺则用切片年 |",
        "| `source` | `chgis-v6` 或 `hartwell-v5` | 本脚本写入 |",
        "| `sliceId` / `sliceTitle` | 所属切片 | 本脚本写入 |",
        "| `sys_id` | CHGIS 原始 ID（若有） | `sys_id`/`SYS_ID`；镜像多数未带 |",
        "",
        "切片级 `fromYear`/`toYear` 见同目录 `index.json`（给 T-010 / T-110 按年对表）。",
        "",
        "## 样例属性（秦·会稽郡）",
        "",
        "```json",
        json.dumps(
            {
                "name": "会稽郡",
                "name_py": "Kuaiji Jun",
                "type_ch": "郡",
                "beg_yr": -222,
                "end_yr": -211,
                "fromYear": -222,
                "toYear": -211,
                "source": "chgis-v6",
                "sliceId": "qin",
                "sliceTitle": "秦",
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## 抽样核对（质心，手工）",
        "",
        "| 切片 | 地名 | 存续 | 质心 (lon,lat) | 对照 |",
        "|---|---|---|---|---|",
        "| `qin` | 会稽郡 | -222–-211 | 119.86, 30.02 | 浙东合理 |",
        "| `tang` | 泽州 | 627–741 | 112.77, 35.60 | 晋东南合理 |",
        "| `ming` | 襄阳府 | 1476–1911 | 111.87, 32.07 | 鄂北合理 |",
        "| `qing` | 顺天府 | 1743–1911 | 116.83, 39.67 | 京津合理 |",
        "",
        "## 已知局限（出自镜像 DEVLOG，入库时照录）",
        "",
        "1. **Hartwell（唐宋元明等 `hartwell-v5` 切片）**是用现代县域边界「拼接」历史政区的近似值；"
        "前端图例（T-020）应对此类标「近似」。",
        "2. **秦**仅约 13 郡，且集中在东南；关中/西部无面。",
        "3. **唐**关中/长安一带常无多边形覆盖（CHGIS 早期面偏东）；勿把空白当成「无政权」。",
        "4. **几何**经 Douglas-Peucker 简化（ε 约 0.03°–0.5°），非官方原精度。",
        "5. 本批未直接从 Harvard Dataverse 拉官方 zip（本环境 AWS WAF）；谱系以镜像 DEVLOG + 字段形态核对。",
        "",
        "## 重跑",
        "",
        "```sh",
        "python packages/maps/scripts/fetch_academic.py",
        "```",
        "",
        "中间文件在 `.cache/maps/chgis/mirror/`（可删，可重下）。产出扩展名为 `.json`（便于 Vite 打包）。",
        "",
        "## 切片清单",
        "",
        "| id | 文件 | 标题 | from | to | 谱系 | 要素数 | 字节 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in index["slices"]:
        lines.append(
            f"| {s['id']} | `{s['file']}` | {s['title']} | {s['fromYear']} | "
            f"{s['toYear']} | {s['lineage']} | {s['featureCount']} | {s['bytes']} |"
        )
    lines.append("")
    (OUT / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    probe = probe_dataverse()
    print("Dataverse probe:", probe)

    from datetime import date

    slices_out: list[dict] = []
    for meta in SLICES:
        info = process_slice(meta)
        print(
            f"  → {info['file']}  features={info['featureCount']}  "
            f"{info['bytes']} bytes"
        )
        if info["bytes"] > 5_000_000:
            print(
                f"WARNING: {info['file']} > 5MB "
                f"({info['bytes']}); 总量过大时先问 claude-code",
                file=sys.stderr,
            )
        slices_out.append(info)

    index = {
        "fetchedAt": date.today().isoformat(),
        "official": OFFICIAL,
        "dataverseProbe": probe,
        "slices": slices_out,
    }
    (OUT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_sources(index, probe)

    total = sum(s["bytes"] for s in slices_out)
    print(f"done: {len(slices_out)} slices, {total} bytes → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
