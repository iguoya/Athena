#!/usr/bin/env python3
"""把 ADR 0009 切出的六张课程碎片图，按原 C++ 首页知识图谱收成两章。

只跑一次：读 content/polaris.json 与 content/absorbed/cpp-roadmap.json，写出新的
polaris.json。节点正文、练习、验收和必要程度全部沿用已吸收的字段，只调整归属、
强弱先修和原图上的 entry / verify / track。
"""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLARIS = ROOT / "content" / "polaris.json"
RAW = ROOT / "content" / "absorbed" / "cpp-roadmap.json"

FRAGMENT_MAPS = {
    "computer-programming",
    "computer-machine",
    "computer-network-intelligence",
    "electronic-circuit",
    "electronic-mcu",
    "electronic-embedded",
}

NODE_KEYS = [
    "id",
    "title",
    "track",
    "stable_definition",
    "engineering_role",
    "pitfall",
    "practice",
    "validation",
    "validation_note",
    "volatility",
    "priority",
    "priority_reason",
    "targets",
    "app",
    "entry",
    "verify",
    "requires",
    "source_refs",
]

THEORY_BY_SIDE = {
    "computer": [
        "离散数学",
        "计算理论与自动机",
        "算法复杂度分析",
        "线性代数与概率统计",
        "体系结构进阶",
    ],
    "electronics": [
        "信号与系统",
        "控制理论与 PID",
        "通信原理",
        "模拟电路进阶",
        "电磁兼容与信号完整性",
    ],
}


def absorbed_id(raw_node: dict) -> str:
    prefix = "polaris.cs." if raw_node["side"] == "computer" else "polaris.ei."
    return prefix + raw_node["id"]


def ordered_node(source: dict) -> OrderedDict:
    node = OrderedDict()
    for key in NODE_KEYS:
        if key in source:
            node[key] = source[key]
    for key, value in source.items():
        if key not in node:
            node[key] = value
    return node


def main() -> None:
    polaris = json.loads(POLARIS.read_text(encoding="utf-8"))
    if any(entry["id"] == "computer-science" for entry in polaris["maps"]):
        print("两章课程图已经在 polaris.json 里，无需再合并。")
        return
    raw = json.loads(RAW.read_text(encoding="utf-8"))

    raw_by_id = {node["id"]: node for node in raw["nodes"]}
    theory_by_name = {topic["name"]: topic for topic in raw["theory"]}

    existing_nodes: dict[str, dict] = {}
    existing_edges: dict[tuple[str, str], dict] = {}
    kept_maps: list[dict] = []
    for entry in polaris["maps"]:
        for node in entry["nodes"]:
            existing_nodes[node["id"]] = node
        for edge in entry.get("edges", []):
            existing_edges[(edge["from"], edge["to"])] = edge
        if entry["id"] not in FRAGMENT_MAPS:
            kept_maps.append(entry)
    for edge in polaris.get("cross_edges", []):
        existing_edges[(edge["from"], edge["to"])] = edge

    def evidence_for(from_id: str, to_id: str, fallback_node: dict) -> list:
        old = existing_edges.get((from_id, to_id))
        if old and old.get("evidence_refs"):
            return old["evidence_refs"]
        refs = fallback_node.get("source_refs") or []
        if refs:
            first = refs[0]
            return [
                {
                    "relation": "informed",
                    "source_id": first["source_id"],
                    "locator": first["locator"],
                }
            ]
        raise SystemExit(f"边 {from_id} → {to_id} 找不到出处")

    chapters = {
        "computer": {
            "id": "computer-science",
            "title": "计算机科学与技术",
            "view_kind": "academic",
            "graph_kind": "course",
            "summary": (
                "计算机方向的完整课程依赖图，对应原 C++ 学习首页知识图谱的一侧："
                "从语言、工具链和系统基础出发，经数据结构、并发与网络，收到一个能独立交付的项目。"
                "Python 语言、C 语言编程、C++ 程序设计和工程实践与工具链都是推荐入门起点，"
                "从这些里任选一个开始都合理。实线是真正的前置门槛，虚线是「知道渊源会更透彻」的来路。"
            ),
            "nodes": [],
            "edges": [],
            "theory": [theory_by_name[name] for name in THEORY_BY_SIDE["computer"]],
        },
        "electronics": {
            "id": "electronic-information",
            "title": "电子信息技术",
            "view_kind": "academic",
            "graph_kind": "course",
            "summary": (
                "电子信息方向的完整课程依赖图，对应原 C++ 学习首页知识图谱的另一侧："
                "从电路基础出发，经单片机、总线、信号处理，走到嵌入式 Linux 与端侧部署。"
                "电路基础是推荐入门起点，不依赖任何编程知识，但没有它后面的单片机和 PCB "
                "只能照着接线图抄。跨侧依赖（例如先修 C 语言）在详情里作为跨图关联列出。"
            ),
            "nodes": [],
            "edges": [],
            "theory": [theory_by_name[name] for name in THEORY_BY_SIDE["electronics"]],
        },
    }

    cross_edges = []
    for raw_node in raw["nodes"]:
        node_id = absorbed_id(raw_node)
        existing = existing_nodes.get(node_id)
        if existing is None:
            raise SystemExit(f"缺少已吸收节点 {node_id}")
        merged = dict(existing)
        merged["track"] = raw_node["track"]
        merged["entry"] = bool(raw_node["entry"])
        merged["verify"] = raw_node["verify"]
        strong_same_side = []
        for prereq in raw_node["prerequisites"]:
            other = raw_by_id[prereq["id"]]
            from_id = absorbed_id(other)
            to_id = node_id
            same_side = other["side"] == raw_node["side"]
            relation = "requires" if prereq["strong"] else "enables"
            edge = {
                "from": from_id,
                "to": to_id,
                "relation": relation,
                "rationale": prereq["reason"],
                "evidence_refs": evidence_for(from_id, to_id, existing),
            }
            if prereq["strong"]:
                edge["strong"] = True
            else:
                edge["strong"] = False
            if same_side:
                chapters[raw_node["side"]]["edges"].append(edge)
                if prereq["strong"]:
                    strong_same_side.append(from_id)
            else:
                cross_edges.append(edge)
        merged["requires"] = strong_same_side
        chapters[raw_node["side"]]["nodes"].append(ordered_node(merged))

    new_maps = [chapters["computer"], chapters["electronics"]] + kept_maps
    polaris["maps"] = new_maps
    polaris["cross_edges"] = cross_edges
    POLARIS.write_text(
        json.dumps(polaris, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"写成两章：计算机 {len(chapters['computer']['nodes'])} 节点 / "
        f"{len(chapters['computer']['edges'])} 边，电子信息 "
        f"{len(chapters['electronics']['nodes'])} 节点 / "
        f"{len(chapters['electronics']['edges'])} 边，跨图 {len(cross_edges)} 条。"
    )


if __name__ == "__main__":
    main()
