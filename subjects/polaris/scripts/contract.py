#!/usr/bin/env python3
"""Polaris 内容契约校验：`content/polaris.json` 与 `content/sources/catalog.json` 的唯一守门员。

从 `src/polaris_catalog.cpp` 的 `validateDocument` 移植而来（ADR 0015 决策 2）。规则与那份
C++ 一一对应，区别只有两点：

- 一次收集全部违例，而不是遇到第一个就停——改内容时一轮就能看全；
- 每条违例带规则编号，测试按编号断言「这类规则真的会失败」。

新增或修改规则只改这一个文件。应用运行时不再校验（ADR 0015 决策 2）。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

KNOWN_VALIDATION = {"measurement", "benchmark", "integration", "review", "simulation", "analysis"}
KNOWN_VOLATILITY = {"stable", "evolving", "volatile"}
KNOWN_PRIORITY = {"essential", "important", "optional"}
STAGE_RANK = {"junior": 0, "intermediate": 1, "senior": 2}
KNOWN_VERIFY = {"code", "board", "bench"}
KNOWN_MASTERY = {"familiarity", "usage", "assessment"}
KNOWN_RELATION = {"requires", "enables"}
# 节点出处的关系词汇，与仓库级 scripts/check-app-sources.mjs 的 CONTENT_RELATIONS / META_RELATIONS 一致：
# 至少一条内容来源，补充说明不算数（ADR 0043）。边与路线的出处不受这条限制。
CONTENT_RELATIONS = {"verbatim", "quoted", "adapted", "authored"}
META_RELATIONS = {"selection_basis", "exam_alignment", "see_also"}
KNOWN_CONTRACT = {"timing", "memory", "bus", "power", "boot", "verify"}  # 软硬接口的六份跨层契约（ADR 0016 决策 4）
KNOWN_LENS = {"direction", "stack", "artifact"}
KNOWN_BALANCE = {"software", "balanced", "hardware"}
# 开放地图：界面可打开、路线可引用的底盘（ADR 0012、ADR 0016 决策 3、ADR 0018 决策 4）。src/content/catalog.ts 里有同一份定义。
OPEN_VIEW_KINDS = {"academic", "codesign", "frontier"}
# 十二个能力域（ADR 0018 决策 1）：开放地图的每个节点必须归入一个，路线的均衡度据此统计。
KNOWN_DOMAIN = {"foundations", "programming", "algorithms", "architecture", "systems", "digital",
                "circuits", "signals", "control", "power", "embedded", "assurance", "security", "acceleration"}
# 四个工科专业类 + 跨专业类（ADR 0021）。开放地图与全部路线必须写 discipline。
KNOWN_DISCIPLINE = {"cs", "ei", "ee", "auto", "cross"}
# 弱电、强电、兼有（ADR 0021 决策 2）：电气类（ee）图的每个节点必须写。
KNOWN_CURRENT = {"weak", "strong", "both"}

# 评级（ADR 0022、0023）：七个维度、五个等级。实践性、可验证性、学科核心骨干由内容推导、契约重算；其余四项是带依据的编辑评估。
RATING_DIMENSIONS = ["utility", "hands_on", "theory", "verifiable", "core", "demand", "outlook"]
RATING_DERIVED_NODE = {"hands_on", "verifiable", "core"}
RATING_LEVELS = 5
# 路线的推荐等级（ADR 0022 决策 7）：优先推荐、推荐、可选、进阶（有明确前置，不宜作起点）。
KNOWN_VERDICT = {"priority", "recommended", "optional", "advanced"}

NODE_FIELDS = ["id", "title", "track", "stable_definition", "engineering_role",
               "practice", "validation", "volatility"]
ACADEMIC_NODE_FIELDS = ["pitfall", "priority", "priority_reason"]


@dataclass(frozen=True)
class Violation:
    code: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.where}: {self.message}"


def load_document(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """读内容并把来源目录并入 `sources`，与 C++ 的 loadDocument 同一个形状。"""
    document = json.loads((root / "content" / "polaris.json").read_text(encoding="utf-8"))
    catalog = json.loads((root / "content" / "sources" / "catalog.json").read_text(encoding="utf-8"))
    document["sources"] = catalog.get("sources", [])
    return document


def _text(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _strings(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


class _Report:
    def __init__(self) -> None:
        self.violations: list[Violation] = []

    def add(self, code: str, where: str, message: str) -> None:
        self.violations.append(Violation(code, where, message))

    def require_text(self, code: str, where: str, obj: dict, keys: list[str]) -> bool:
        ok = True
        for key in keys:
            if not _text(obj.get(key)):
                self.add(code, where, f"缺少必填文本字段：{key}")
                ok = False
        return ok

    def require_source_refs(self, code: str, where: str, refs: Any, source_ids: set[str]) -> None:
        if not isinstance(refs, list) or not refs:
            self.add(code, where, "缺少出处引用")
            return
        for ref in refs:
            ref = ref if isinstance(ref, dict) else {}
            if not self.require_text(code, where, ref, ["relation", "source_id", "locator"]):
                continue
            if ref["source_id"] not in source_ids:
                self.add(code, where, f"引用了不存在的 source_id：{ref['source_id']}")


def validate(document: dict[str, Any], root: Path = PROJECT_ROOT) -> list[Violation]:
    report = _Report()
    report.require_text("doc.fields", "文档", document, ["title", "subtitle"])
    maps = document.get("maps") if isinstance(document.get("maps"), list) else []
    if len(maps) < 2:
        report.add("doc.min_maps", "文档", "至少需要两张地图，才能构成图谱合集。")

    source_ids = _validate_sources(report, document)

    # 先过一遍地图清单：节点的 targets 要指向职业目标层的地图，校验它是否存在需要先知道
    # 每张图的 view_kind；跨图关联的两端校验同理。
    view_kind_by_map = {m.get("id"): m.get("view_kind") for m in maps if isinstance(m, dict)}

    map_ids: set[str] = set()
    global_node_ids: set[str] = set()
    map_of_node: dict[str, str] = {}
    for entry in maps:
        entry = entry if isinstance(entry, dict) else {}
        _validate_map(report, entry, root, source_ids, view_kind_by_map,
                      map_ids, global_node_ids, map_of_node)

    _validate_cross_edges(report, document, source_ids, global_node_ids, map_of_node)
    _validate_routes(report, document, source_ids, view_kind_by_map, map_of_node)
    _validate_principles(report, document, source_ids)
    _validate_ratings(report, document, view_kind_by_map)
    return report.violations


def _validate_sources(report: _Report, document: dict[str, Any]) -> set[str]:
    source_ids: set[str] = set()
    for source in document.get("sources") or []:
        source = source if isinstance(source, dict) else {}
        where = f"来源 {source.get('id', '(无 id)')}"
        report.require_text("source.fields", where, source, ["id", "title", "url", "kind"])
        source_id = source.get("id")
        if source_id in source_ids:
            report.add("source.duplicate_id", where, f"来源 ID 重复：{source_id}")
        if isinstance(source_id, str):
            source_ids.add(source_id)
    if not source_ids:
        report.add("source.empty", "来源目录", "来源目录不能为空。")
    return source_ids


def _validate_map(report: _Report, entry: dict, root: Path, source_ids: set[str],
                  view_kind_by_map: dict, map_ids: set[str], global_node_ids: set[str],
                  map_of_node: dict[str, str]) -> None:
    map_id = entry.get("id")
    where = f"地图 {map_id}"
    report.require_text("map.fields", where, entry, ["id", "title", "summary", "view_kind"])
    if map_id in map_ids:
        report.add("map.duplicate_id", where, f"地图 ID 重复：{map_id}")
    map_ids.add(map_id)

    nodes = entry.get("nodes") if isinstance(entry.get("nodes"), list) else []
    if len(nodes) < 3:
        report.add("map.min_nodes", where, "少于三个节点，不能形成有意义的路径。")

    # 不建节点的理论科目（ADR 0009 第 7 条）：可以没有，写了就要三段齐全。
    for topic in entry.get("theory") or []:
        topic = topic if isinstance(topic, dict) else {}
        report.require_text("map.theory", f"{where} 的理论科目 {topic.get('name', '(无名)')}",
                            topic, ["name", "content", "role"])

    academic = entry.get("view_kind") == "academic"
    codesign = entry.get("view_kind") == "codesign"
    frontier = entry.get("view_kind") == "frontier"
    open_map = entry.get("view_kind") in OPEN_VIEW_KINDS
    if open_map and entry.get("discipline") not in KNOWN_DISCIPLINE:
        report.add("map.discipline", where, "开放地图必须写 discipline：cs、ei、ee、auto 或 cross。")
    course = entry.get("graph_kind") == "course"
    node_ids: set[str] = set()
    requirements: dict[str, set[str]] = {}
    node_stage: dict[str, str] = {}

    for node in nodes:
        node = node if isinstance(node, dict) else {}
        node_id = node.get("id")
        nwhere = f"节点 {node_id}"
        fields = NODE_FIELDS + (ACADEMIC_NODE_FIELDS if open_map else [])
        report.require_text("node.fields", nwhere, node, fields)
        if node_id in node_ids or node_id in global_node_ids:
            report.add("node.duplicate_id", nwhere, f"节点 ID 必须全局唯一：{node_id}")
        if isinstance(node_id, str):
            node_ids.add(node_id)
            global_node_ids.add(node_id)
            map_of_node[node_id] = map_id

        if node.get("validation") not in KNOWN_VALIDATION:
            report.add("node.validation", nwhere, f"validation 取值无效：{node.get('validation')}")
        if node.get("volatility") not in KNOWN_VOLATILITY:
            report.add("node.volatility", nwhere, "volatility 只能是 stable、evolving 或 volatile。")

        if open_map:
            _validate_graded_node(report, node, nwhere, node_stage, require_stage=codesign or frontier)
            if "current" in node and node["current"] not in KNOWN_CURRENT:
                report.add("node.current", nwhere, "current 只能是 weak、strong 或 both。")
            if entry.get("discipline") == "ee" and "current" not in node:
                report.add("node.current_required", nwhere, "电气类（ee）图的节点必须写 current（弱电、强电或兼有）。")
            if node.get("domain") not in KNOWN_DOMAIN:
                report.add("node.domain", nwhere, f"domain 只能是十二个能力域之一，现在是 {node.get('domain')!r}。")
        if academic:
            _validate_academic_node(report, node, nwhere, root, view_kind_by_map)
        if codesign:
            _validate_codesign_node(report, node, nwhere)
        if course:
            _validate_course_node(report, node, nwhere)
        elif "chapters" in node:
            _validate_chapters(report, node, nwhere)

        report.require_source_refs("node.source_refs", nwhere, node.get("source_refs"), source_ids)
        _validate_node_relations(report, nwhere, node.get("source_refs"))
        required: set[str] = set()
        for rid in _strings(node.get("requires")):
            if rid == node_id:
                report.add("node.self_requires", nwhere, "不能依赖自身。")
            required.add(rid)
        if isinstance(node_id, str):
            requirements[node_id] = required

    _validate_requirements(report, where, map_id, node_ids, requirements, node_stage)
    _validate_edges(report, entry, where, node_ids, requirements, source_ids)
    _validate_acyclic(report, where, node_ids, requirements)


def _validate_graded_node(report: _Report, node: dict, nwhere: str, node_stage: dict[str, str],
                          require_stage: bool) -> None:
    # 必要程度按职业目标层的专业方向判定（ADR 0009 第 5 条）：等级、理由和它支撑的
    # 目标能力三者必须同时在场。只留等级会退化成口味排序，只留理由则无法排先后。
    if node.get("priority") not in KNOWN_PRIORITY:
        report.add("node.priority", nwhere, "priority 只能是 essential、important 或 optional。")
    stage = node.get("stage")
    if stage in (None, ""):
        # 软硬接口图按阶段分列，没有阶段的节点没处放（ADR 0016 决策 4）；学术图历史上允许缺省。
        if require_stage:
            report.add("node.stage_required", nwhere, "软硬接口图与高端纵深图的节点必须写 stage。")
    elif stage not in STAGE_RANK:
        report.add("node.stage", nwhere, "stage 只能是 junior、intermediate 或 senior。")
    else:
        if not _text(node.get("stage_reason")):
            report.add("node.stage_reason", nwhere, "缺 stage_reason：要说明这一阶段为什么学它。")
        node_stage[node["id"]] = stage


def _validate_academic_node(report: _Report, node: dict, nwhere: str, root: Path,
                            view_kind_by_map: dict) -> None:
    # targets 不再必填（ADR 0021 决策 6）：军工目标图只是参考层；写了就必须有效。
    for target in _strings(node.get("targets")):
        if target not in view_kind_by_map:
            report.add("node.targets_unknown", nwhere, f"targets 引用了不存在的地图 {target}。")
        elif view_kind_by_map[target] != "target":
            report.add("node.targets_kind", nwhere, f"targets 只能指向职业目标层的地图，{target} 不是。")
    # 承载这个领域的独立应用（ADR 0009 第 8 条）：可以为空（规划中），写了就必须真有。
    app = node.get("app")
    if _text(app) and not (root.parent / app / "app.json").exists():
        report.add("node.app", nwhere, f"app 指向了不存在的应用：{app}")


def _validate_codesign_node(report: _Report, node: dict, nwhere: str) -> None:
    # 软硬接口节点必须同时写清两侧（ADR 0016 决策 4）：只写一侧的不属于这张图。
    if node.get("contract") not in KNOWN_CONTRACT:
        report.add("codesign.contract", nwhere, "contract 只能是 timing、memory、bus、power、boot 或 verify。")
    report.require_text("codesign.sides", nwhere, node, ["hw_side", "sw_side"])


def _validate_node_relations(report: _Report, nwhere: str, refs: Any) -> None:
    relations = [r.get("relation") for r in refs if isinstance(r, dict)] if isinstance(refs, list) else []
    for relation in relations:
        if relation not in CONTENT_RELATIONS | META_RELATIONS:
            report.add("node.source_relation", nwhere,
                       f"出处关系「{relation}」不是内容来源（{'/'.join(sorted(CONTENT_RELATIONS))}）"
                       f"也不是已知的补充说明（{'/'.join(sorted(META_RELATIONS))}）。")
    if relations and not any(r in CONTENT_RELATIONS for r in relations):
        report.add("node.source_content", nwhere, "只有补充说明，没有一条说明内容出自哪里。")


def _validate_course_node(report: _Report, node: dict, nwhere: str) -> None:
    # 课程知识图谱要能看见原图上的判断：从哪进、拿什么验（ADR 0010）。
    if "entry" not in node:
        report.add("course.entry", nwhere, "缺少 entry（是否为入门起点）。")
    if node.get("verify") not in KNOWN_VERIFY:
        report.add("course.verify", nwhere, "verify 只能是 code、board 或 bench。")
    _validate_chapters(report, node, nwhere)


def _validate_chapters(report: _Report, node: dict, nwhere: str) -> None:
    """细分章节学习流程。课程图的节点必须有；其他开放地图的节点写了就必须合格（ADR 0019）。

    章节按学习顺序排列：课内先修只能指向排在它前面的章节。可选的 ref 必须指向本节点自己
    引用过的来源，这样每一章都能追到出处。
    """
    chapters = node.get("chapters") if isinstance(node.get("chapters"), list) else []
    if len(chapters) < 3:
        report.add("course.chapters_min", nwhere, "缺少细分章节学习流程（至少三章）。")
    node_sources = {r.get("source_id") for r in node.get("source_refs") or [] if isinstance(r, dict)}
    seen: list[str] = []
    for chapter in chapters:
        chapter = chapter if isinstance(chapter, dict) else {}
        chapter_id = chapter.get("id")
        cwhere = f"{nwhere} 的章节 {chapter_id}"
        report.require_text("course.chapter_fields", cwhere, chapter, ["id", "title", "summary"])
        if chapter_id in seen:
            report.add("course.chapter_duplicate", cwhere, "章节 ID 重复。")
        mastery = chapter.get("mastery")
        if mastery not in KNOWN_MASTERY:
            report.add("course.mastery", cwhere, "mastery 只能是 familiarity、usage 或 assessment（CS2013）。")
        practice = chapter.get("hands_on") is True or chapter.get("kind") == "practice"
        if mastery in KNOWN_MASTERY and mastery != "familiarity" and not practice:
            report.add("course.practice", cwhere, "是运用或评估，必须标为实践，以便和理论区隔。")
        for rid in _strings(chapter.get("requires")):
            if rid not in seen:
                report.add("course.chapter_requires", cwhere, f"先修 {rid} 不在本课学习流程里，或排在它的后面。")
        if "ref" in chapter:
            ref = chapter["ref"] if isinstance(chapter["ref"], dict) else {}
            if not report.require_text("course.chapter_ref", cwhere, ref, ["source_id", "locator"]):
                pass
            elif ref["source_id"] not in node_sources:
                report.add("course.chapter_ref", cwhere, f"出处 {ref['source_id']} 不是本节点引用过的来源。")
        if isinstance(chapter_id, str):
            seen.append(chapter_id)


def _validate_requirements(report: _Report, where: str, map_id: str, node_ids: set[str],
                           requirements: dict[str, set[str]], node_stage: dict[str, str]) -> None:
    for node_id, required in requirements.items():
        for rid in required:
            if rid not in node_ids:
                report.add("requires.outside_map", where, f"强先修 {rid} 不在本地图内。")
                continue
            from_stage, to_stage = node_stage.get(rid), node_stage.get(node_id)
            if from_stage and to_stage and STAGE_RANK[from_stage] > STAGE_RANK[to_stage]:
                report.add("requires.higher_stage", f"节点 {node_id}", f"不能把更高阶段的 {rid} 当成先修。")


def _validate_edges(report: _Report, entry: dict, where: str, node_ids: set[str],
                    requirements: dict[str, set[str]], source_ids: set[str]) -> None:
    required_edges: set[tuple[str, str]] = set()
    for edge in entry.get("edges") or []:
        edge = edge if isinstance(edge, dict) else {}
        src, dst = edge.get("from"), edge.get("to")
        ewhere = f"边 {src} → {dst}"
        report.require_text("edge.fields", ewhere, edge, ["from", "to", "relation", "rationale"])
        if src not in node_ids or dst not in node_ids:
            report.add("edge.endpoint", f"{where} 的 {ewhere}", "引用了不存在的节点。")
            continue
        report.require_source_refs("edge.evidence", ewhere, edge.get("evidence_refs"), source_ids)
        relation = edge.get("relation")
        if relation not in KNOWN_RELATION:
            report.add("edge.relation", ewhere, "relation 只能是 requires 或 enables。")
        elif relation == "requires":
            required_edges.add((src, dst))
            if src not in requirements.get(dst, set()):
                report.add("edge.requires_not_declared", ewhere, "标为 requires，却未写入目标节点 requires。")
        elif src in requirements.get(dst, set()):
            report.add("edge.enables_in_requires", ewhere, "是虚线来路，不应写入目标节点 requires。")
    for dst, required in requirements.items():
        for src in required:
            if src in node_ids and (src, dst) not in required_edges:
                report.add("edge.requires_missing_edge", f"{where}", f"强先修 {src} → {dst} 缺少带依据的 requires 边。")


def _validate_acyclic(report: _Report, where: str, node_ids: set[str],
                      requirements: dict[str, set[str]]) -> None:
    indegree = {n: len([r for r in requirements.get(n, set()) if r in node_ids]) for n in node_ids}
    outgoing: dict[str, list[str]] = {}
    for node_id in node_ids:
        for rid in requirements.get(node_id, set()):
            if rid in node_ids:
                outgoing.setdefault(rid, []).append(node_id)
    ready = [n for n, degree in indegree.items() if degree == 0]
    visited = 0
    while ready:
        current = ready.pop()
        visited += 1
        for nxt in outgoing.get(current, []):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
    if visited != len(node_ids):
        report.add("requires.cycle", where, "requires 形成了环。")


def _validate_cross_edges(report: _Report, document: dict, source_ids: set[str],
                          global_node_ids: set[str], map_of_node: dict[str, str]) -> None:
    # 跨图关联（ADR 0009 第 6 条）：图内 requires 不跨图，两端落在不同图里的先修放顶层。
    seen: set[tuple[str, str]] = set()
    for edge in document.get("cross_edges") or []:
        edge = edge if isinstance(edge, dict) else {}
        src, dst = edge.get("from"), edge.get("to")
        where = f"跨图关联 {src} → {dst}"
        if not report.require_text("cross.fields", where, edge, ["from", "to", "rationale"]):
            continue
        if src not in global_node_ids or dst not in global_node_ids:
            report.add("cross.endpoint", where, "引用了不存在的节点。")
            continue
        if map_of_node.get(src) == map_of_node.get(dst):
            report.add("cross.same_map", where, "两端在同一张图里，应当写成图内 requires。")
        if (src, dst) in seen:
            report.add("cross.duplicate", where, "跨图关联重复。")
        seen.add((src, dst))
        report.require_source_refs("cross.evidence", where, edge.get("evidence_refs"), source_ids)


def _validate_routes(report: _Report, document: dict, source_ids: set[str], view_kind_by_map: dict,
                     map_of_node: dict[str, str]) -> None:
    """路线只引用节点 id、不复制节点（ADR 0016 决策 1–3）。"""
    nodes_by_id = {n["id"]: n for m in document.get("maps") or [] if isinstance(m, dict)
                   for n in m.get("nodes") or [] if isinstance(n, dict) and "id" in n}
    seen: set[str] = set()
    for route in document.get("routes") or []:
        route = route if isinstance(route, dict) else {}
        route_id = route.get("id")
        where = f"路线 {route_id}"
        report.require_text("route.fields", where, route, ["id", "title", "summary", "audience", "artifact"])
        if route_id in seen:
            report.add("route.duplicate_id", where, "路线 ID 重复。")
        seen.add(route_id)
        if route.get("discipline") not in KNOWN_DISCIPLINE:
            report.add("route.discipline", where, "路线必须写 discipline：cs、ei、ee、auto 或 cross。")
        if route.get("lens") not in KNOWN_LENS:
            report.add("route.lens", where, "lens 只能是 direction、stack 或 artifact。")
        if route.get("balance") not in KNOWN_BALANCE:
            report.add("route.balance", where, "balance 只能是 software、balanced 或 hardware。")
        report.require_source_refs("route.source_refs", where, route.get("source_refs"), source_ids)
        # 可选字段：写了就不能是空壳（ADR 0018 决策 3、5）。
        if "pitfalls" in route and not (isinstance(route["pitfalls"], list) and route["pitfalls"]
                                        and all(_text(item) for item in route["pitfalls"])):
            report.add("route.pitfalls", where, "pitfalls 写了就必须是非空的文字列表。")
        if "profile" in route and not _text(route["profile"]):
            report.add("route.profile", where, "profile 写了就不能是空的。")

        stages = route.get("stages") if isinstance(route.get("stages"), list) else []
        if len(stages) < 2:
            report.add("route.stages_min", where, "至少要有两个阶段，才算有先后。")
        stage_of: dict[str, int] = {}
        for index, stage in enumerate(stages):
            stage = stage if isinstance(stage, dict) else {}
            swhere = f"{where} 第 {index + 1} 阶段"
            report.require_text("route.stage_fields", swhere, stage, ["title", "goal", "checkpoint"])
            members = _strings(stage.get("nodes"))
            if not members:
                report.add("route.stage_nodes", swhere, "每个阶段至少要有一个节点。")
            for node_id in members:
                if node_id not in nodes_by_id:
                    report.add("route.node_unknown", swhere, f"引用了不存在的节点 {node_id}。")
                    continue
                if view_kind_by_map.get(map_of_node.get(node_id)) not in OPEN_VIEW_KINDS:
                    report.add("route.node_closed", swhere, f"{node_id} 在参考层地图里，路线只能引用开放地图的节点。")
                if node_id in stage_of:
                    report.add("route.node_repeated", swhere, f"{node_id} 在这条路线里出现了不止一次。")
                    continue
                stage_of[node_id] = index
        # 同一路线里，强先修不得排在被依赖者之后。
        for node_id, index in stage_of.items():
            for required in _strings(nodes_by_id[node_id].get("requires")):
                if required in stage_of and stage_of[required] > index:
                    report.add("route.order", where,
                               f"{node_id} 强先修 {required}，但 {required} 排在更晚的阶段。")


def _validate_principles(report: _Report, document: dict, source_ids: set[str]) -> None:
    """学习原则是数据，必须带出处：原则里的话要能在引用的来源里找到依据（ADR 0018 决策 6）。"""
    seen: set[str] = set()
    for principle in document.get("principles") or []:
        principle = principle if isinstance(principle, dict) else {}
        pid = principle.get("id")
        where = f"原则 {pid}"
        report.require_text("principle.fields", where, principle, ["id", "title", "body"])
        if pid in seen:
            report.add("principle.duplicate_id", where, "原则 ID 重复。")
        seen.add(pid)
        report.require_source_refs("principle.source_refs", where, principle.get("source_refs"), source_ids)


# —— 评级（ADR 0022）——

_VALIDATION_BASE = {"measurement": 3, "benchmark": 3, "integration": 2, "simulation": 2, "analysis": 1, "review": 1}
_VALIDATION_ZH = {"measurement": "实测", "benchmark": "基准对比", "integration": "联调", "simulation": "仿真",
                  "analysis": "分析", "review": "评审"}
_PRIORITY_BASE = {"essential": 3, "important": 2, "optional": 1}
_PRIORITY_ZH = {"essential": "必要", "important": "重要", "optional": "可选"}


def _round_half_up(x: float) -> int:
    return int(x + 0.5)


def _dependents(document: dict[str, Any]) -> dict[str, int]:
    """被依赖数：图内 requires 与跨图 requires 边合计。"""
    count: dict[str, int] = {}
    for entry in document.get("maps") or []:
        for node in (entry.get("nodes") or []) if isinstance(entry, dict) else []:
            for required in _strings(node.get("requires")) if isinstance(node, dict) else []:
                count[required] = count.get(required, 0) + 1
    for edge in document.get("cross_edges") or []:
        if isinstance(edge, dict) and edge.get("relation", "requires") == "requires" and isinstance(edge.get("from"), str):
            count[edge["from"]] = count.get(edge["from"], 0) + 1
    return count


def derive_node_ratings(node: dict[str, Any], dependents: int) -> dict[str, tuple[int, str]]:
    """推导型三个维度：实践性、可验证性、学科核心骨干。返回 {维度: (等级, 依据)}。"""
    chapters = [c for c in (node.get("chapters") or []) if isinstance(c, dict)]
    practice = sum(1 for c in chapters if c.get("kind") == "practice")
    ratio = practice / len(chapters) if chapters else 0.0
    hands_on = 1 if ratio <= 0.4 else 2 if ratio <= 0.55 else 3 if ratio <= 0.7 else 4 if ratio <= 0.8 else 5
    hands_on_reason = f"{len(chapters)} 章里 {practice} 章是动手实践（{round(ratio * 100)}%）"

    base = _VALIDATION_BASE.get(node.get("validation"), 1)
    last = chapters[-1] if chapters else {}
    accept = 1 if last.get("mastery") == "assessment" and last.get("hands_on") else 0
    physical = 1 if node.get("verify") in ("board", "bench") else 0
    verifiable = base + accept + physical
    parts = [f"验证方式为{_VALIDATION_ZH.get(node.get('validation'), '未知')}（基础 {base}）"]
    if accept:
        parts.append("末章是动手的验收（+1）")
    if physical:
        parts.append("用仪器或板上测量取证（+1）")
    verifiable_reason = "；".join(parts)

    core_base = _PRIORITY_BASE.get(node.get("priority"), 1)
    hub = 2 if dependents >= 6 else 1 if dependents >= 3 else 0
    core = core_base + hub
    core_reason = f"优先级{_PRIORITY_ZH.get(node.get('priority'), '可选')}（基础 {core_base}）；被 {dependents} 个节点列为强先修" + (f"（+{hub}）" if hub else "")
    return {"hands_on": (hands_on, hands_on_reason), "verifiable": (verifiable, verifiable_reason), "core": (core, core_reason)}


def aggregate_route_rating(levels: list[int]) -> tuple[int, str]:
    mean = sum(levels) / len(levels) if levels else 0.0
    return _round_half_up(mean), f"汇总 {len(levels)} 个知识点的评级，均值 {mean:.2f}"


def _valid_level(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= RATING_LEVELS


def _validate_ratings(report: _Report, document: dict[str, Any], view_kind_by_map: dict) -> None:
    scheme = document.get("rating_scheme") if isinstance(document.get("rating_scheme"), dict) else {}
    report.require_text("rating.scheme", "评级口径 rating_scheme", scheme, ["as_of"])
    dims = scheme.get("dimensions") if isinstance(scheme.get("dimensions"), list) else []
    if [d.get("id") if isinstance(d, dict) else None for d in dims] != RATING_DIMENSIONS:
        report.add("rating.scheme", "评级口径 rating_scheme", f"dimensions 必须按顺序恰好是 {RATING_DIMENSIONS}。")
    for dim in dims:
        dim = dim if isinstance(dim, dict) else {}
        where = f"评级维度 {dim.get('id')}"
        report.require_text("rating.scheme", where, dim, ["id", "title", "question"])
        derived = dim.get("id") in RATING_DERIVED_NODE
        if dim.get("basis") != ("derived" if derived else "editorial"):
            report.add("rating.scheme", where, "basis 必须与推导型 / 编辑型的划分一致（derived 或 editorial）。")
        levels = dim.get("levels") if isinstance(dim.get("levels"), list) else []
        if [lv.get("level") if isinstance(lv, dict) else None for lv in levels] != list(range(1, RATING_LEVELS + 1)):
            report.add("rating.scheme", where, f"levels 必须是 1 到 {RATING_LEVELS} 级，按顺序各一条。")
        for lv in levels:
            report.require_text("rating.scheme", where, lv if isinstance(lv, dict) else {}, ["name", "criterion"])

    dependents = _dependents(document)
    node_levels: dict[str, dict[str, int]] = {}
    for entry in document.get("maps") or []:
        entry = entry if isinstance(entry, dict) else {}
        if view_kind_by_map.get(entry.get("id")) not in OPEN_VIEW_KINDS:
            continue
        for node in entry.get("nodes") or []:
            node = node if isinstance(node, dict) else {}
            where = f"节点 {node.get('id')} 的 ratings"
            ratings = node.get("ratings") if isinstance(node.get("ratings"), dict) else None
            if ratings is None or set(ratings) != set(RATING_DIMENSIONS):
                report.add("rating.fields", where, f"开放地图的节点必须写齐全部评级维度：{RATING_DIMENSIONS}。")
                continue
            derived = derive_node_ratings(node, dependents.get(node.get("id"), 0))
            levels: dict[str, int] = {}
            for dim in RATING_DIMENSIONS:
                item = ratings[dim] if isinstance(ratings[dim], dict) else {}
                if not _valid_level(item.get("level")) or not _text(item.get("reason")):
                    report.add("rating.fields", where, f"{dim} 需要 1–{RATING_LEVELS} 的整数 level 与非空 reason。")
                    continue
                levels[dim] = item["level"]
                if dim in derived and (item["level"], item["reason"]) != derived[dim]:
                    report.add("rating.derived", where, f"{dim} 是推导型，应为 {derived[dim][0]} 级（{derived[dim][1]}），与内容不一致。")
            node_levels[node.get("id")] = levels

    for route in document.get("routes") or []:
        route = route if isinstance(route, dict) else {}
        where = f"路线 {route.get('id')}"
        members = []
        for stage in route.get("stages") or []:
            for nid in _strings(stage.get("nodes")) if isinstance(stage, dict) else []:
                if nid not in members:
                    members.append(nid)
        ratings = route.get("ratings") if isinstance(route.get("ratings"), dict) else None
        if ratings is None or set(ratings) != set(RATING_DIMENSIONS):
            report.add("rating.fields", where, f"路线必须写齐全部评级维度的 ratings：{RATING_DIMENSIONS}。")
        else:
            for dim in RATING_DIMENSIONS:
                item = ratings[dim] if isinstance(ratings[dim], dict) else {}
                values = [node_levels[n][dim] for n in members if n in node_levels and dim in node_levels[n]]
                expected = aggregate_route_rating(values)
                if (item.get("level"), item.get("reason")) != expected:
                    report.add("rating.derived", where, f"{dim} 应由节点汇总为 {expected[0]} 级（{expected[1]}）。")
        _validate_assessment(report, route, where, {r.get("id") for r in document.get("routes") or [] if isinstance(r, dict)})


def _validate_assessment(report: _Report, route: dict, where: str, route_ids: set) -> None:
    assessment = route.get("assessment") if isinstance(route.get("assessment"), dict) else {}
    if assessment.get("verdict") not in KNOWN_VERDICT or not _text(assessment.get("verdict_reason")):
        report.add("assessment.fields", where, f"assessment 需要 verdict（{sorted(KNOWN_VERDICT)}）与非空 verdict_reason。")
    for key in ("strengths", "weaknesses"):
        items = assessment.get(key)
        if not (isinstance(items, list) and 1 <= len(items) <= 3 and all(_text(i) for i in items)):
            report.add("assessment.fields", where, f"{key} 需要 1–3 条非空文字。")
    nxt = assessment.get("next")
    if not (isinstance(nxt, list) and 1 <= len(nxt) <= 3):
        report.add("assessment.fields", where, "next 需要 1–3 条推荐的后续方向。")
        return
    for item in nxt:
        item = item if isinstance(item, dict) else {}
        if item.get("route_id") not in route_ids or item.get("route_id") == route.get("id") or not _text(item.get("reason")):
            report.add("assessment.fields", where, "next 的每一项要指向另一条存在的路线，并写出理由。")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="校验 Polaris 内容契约（ADR 0015 决策 2）")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    arguments = parser.parse_args(argv)

    document = load_document(arguments.root)
    violations = validate(document, arguments.root)
    for violation in violations:
        print(f"  · {violation}")
    if violations:
        print(f"内容契约未通过，共 {len(violations)} 处。")
        return 1
    nodes = sum(len(m["nodes"]) for m in document["maps"])
    print(f"内容契约通过：{len(document['maps'])} 张图、{nodes} 个节点、"
          f"{len(document['sources'])} 条来源。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
