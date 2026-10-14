#!/usr/bin/env python3
"""复现 claude-code 2026-10-14 审计（T-111）：事件正文末句复述检测。

对每条事件的 summary / impact：切句后取最后一句，与同字段前面各句比较
二元字组（bigram）重叠，取最大值。两种度量并列输出：
  jaccard = |A∩B| / |A∪B|
  contain = |A∩B| / |A|     （A=末句字组集，衡量"末句有多少被前文覆盖"）
阈值：contain ≥ 0.5 即疑似（Jaccard 供人工复核参考）。

用法：python content/audit/detect-repetition.py [阈值]，默认 0.5。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ATLAS = Path(__file__).resolve().parents[1] / "atlas.json"
BENCHMARK = {  # claude-code 给的标杆，用于校准
    "evt-chanyuan", "evt-hangu-debate", "evt-changping",
    "evt-qin-unify", "evt-qin-collapse", "evt-luoyi", "evt-shangyang",
}


def bigrams(s: str) -> set[str]:
    return {s[i:i + 2] for i in range(len(s) - 1)}


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？；])", text)
    return [p.strip() for p in parts if p.strip()]


def main() -> None:
    thr = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    hits = []
    bench_missed = set()
    for ev in atlas["events"]:
        for field in ("summary", "impact"):
            text = ev.get(field)
            if not text:
                continue
            ss = sentences(text)
            if len(ss) < 2:
                continue
            last = ss[-1]
            g_last = bigrams(last)
            if len(g_last) < 4:  # 末句太短（如四字短语）不做几何判断
                continue
            best = None
            for prev in ss[:-1]:
                g = bigrams(prev)
                inter = g_last & g
                union = g_last | g
                jac = len(inter) / len(union)
                con = len(inter) / len(g_last)
                if best is None or con > best[1]:
                    best = (prev, con, jac)
            if best and best[1] >= thr:
                hits.append((ev["id"], field, last, best))
                if ev["id"] in BENCHMARK:
                    bench_missed.discard(ev["id"])
        if ev["id"] in BENCHMARK and ev["id"] not in {h[0] for h in hits}:
            bench_missed.add(ev["id"])

    print(f"阈值 contain>={thr}：疑似 {len(hits)} 处（涉及 {len({h[0] for h in hits})} 个事件）")
    missed = BENCHMARK - {h[0] for h in hits}
    print(f"标杆 7 条中未检出：{sorted(missed) if missed else '无'}\n")
    for eid, field, last, (prev, con, jac) in hits:
        print(f"[{con:.2f}|j{jac:.2f}] {eid} · {field}")
        print(f"  前句：{prev}")
        print(f"  末句：{last}\n")


if __name__ == "__main__":
    main()
