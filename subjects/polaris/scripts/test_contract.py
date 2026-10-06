#!/usr/bin/env python3
"""contract.py 的测试：真实内容必须通过，每一类规则都必须有一个会真失败的反例。

反例做法：深拷贝真实内容，做一处最小改动，断言对应规则编号出现。只在真实内容上通过
是不够的——一条永远不触发的规则和没有这条规则没有区别（ADR 0015 决策 2 第 3 步）。
另外把 tests/polaris_catalog_test.cpp 里与内容有关的断言搬了过来（图数、入口、关键边）。
"""

from __future__ import annotations

import copy
import unittest

import contract

DOC = contract.load_document()


def codes_after(mutate) -> set[str]:
    document = copy.deepcopy(DOC)
    mutate(document)
    return {v.code for v in contract.validate(document)}


def find_map(document: dict, map_id: str) -> dict:
    return next(m for m in document["maps"] if m["id"] == map_id)


def find_node(document: dict, node_id: str) -> dict:
    for m in document["maps"]:
        for node in m["nodes"]:
            if node["id"] == node_id:
                return node
    raise KeyError(node_id)


def first_academic_node(document: dict) -> dict:
    return next(n for m in document["maps"] if m["view_kind"] == "academic" for n in m["nodes"])


def a_requires_edge(document: dict, map_id: str = "computer-science") -> dict:
    return next(e for e in find_map(document, map_id)["edges"] if e["relation"] == "requires")


class RealContent(unittest.TestCase):
    def test_passes_the_contract(self) -> None:
        self.assertEqual([str(v) for v in contract.validate(copy.deepcopy(DOC))], [])

    # —— 以下搬自 tests/polaris_catalog_test.cpp 的内容类断言 ——

    # ADR 0016 决策 6：只增不删。原有 17 张图的 id 一个不少，节点与边的数量不变。
    ORIGINAL_MAP_IDS = [
        "computer-science", "electronic-information", "computer-practice", "electronic-practice",
        "aerospace-engineering", "large-model-engineering", "robot-systems", "embedded-realtime", "hardware-compute",
        "target-realtime-software", "target-avionics-bus", "target-vehicle-engineering", "target-gnc",
        "target-onboard-computer", "target-sensing-compute", "target-digital-intelligence", "target-robot-systems",
    ]

    def test_original_content_only_grows(self) -> None:
        maps = {m["id"]: m for m in DOC["maps"]}
        for map_id in self.ORIGINAL_MAP_IDS:
            self.assertIn(map_id, maps)
        # 只增不删：基线是 125 个节点、138 条边；ADR 0021 又给计算机与电子信息两张图补了节点，所以只断言不少于基线。
        self.assertGreaterEqual(sum(len(maps[i]["nodes"]) for i in self.ORIGINAL_MAP_IDS), 125)
        self.assertGreaterEqual(sum(len(maps[i]["edges"]) for i in self.ORIGINAL_MAP_IDS), 138)

    def test_map_inventory(self) -> None:
        self.assertEqual(len(DOC["maps"]), 21)
        by_kind: dict[str, int] = {}
        for m in DOC["maps"]:
            by_kind[m["view_kind"]] = by_kind.get(m["view_kind"], 0) + 1
        # 课程知识图谱恢复为两章，实践主干两张仍在（ADR 0010）；开放 4 张学术图（ADR 0012）加 1 张软硬接口图（ADR 0016），
        # 再加自动化类与电气类两张课程图（ADR 0021），共 6 张学术图。
        self.assertEqual(by_kind["academic"], 6)
        self.assertEqual(by_kind["codesign"], 1)
        self.assertEqual(by_kind["frontier"], 1)
        self.assertEqual(by_kind["target"], 8)
        self.assertEqual(by_kind.get("career", 0) + by_kind.get("engineering", 0), 5)
        self.assertEqual(DOC["maps"][0]["id"], "computer-science")

    def test_four_disciplines_are_all_present(self) -> None:
        # ADR 0021：四个工科专业类各有一张课程图，路线按专业类归属，每类至少有一条阶梯与一条方向路线。
        disciplines = {m["discipline"] for m in DOC["maps"] if m["view_kind"] in contract.OPEN_VIEW_KINDS}
        self.assertEqual(disciplines, contract.KNOWN_DISCIPLINE)
        for discipline in ("cs", "ei", "ee", "auto"):
            routes = [r for r in DOC["routes"] if r["discipline"] == discipline]
            self.assertTrue(any(r["lens"] == "stack" for r in routes), f"{discipline} 缺主干阶梯")
            self.assertTrue(any(r["lens"] == "direction" for r in routes), f"{discipline} 缺方向路线")

    def test_electrical_map_is_weak_current_first(self) -> None:
        # ADR 0021 决策 2：弱电优先。弱电与兼有的节点不少于强电，并且入门级只有弱电或兼有。
        nodes = find_map(DOC, "electrical-engineering")["nodes"]
        weak = [n for n in nodes if n["current"] in ("weak", "both")]
        strong = [n for n in nodes if n["current"] == "strong"]
        # 弱电侧补深之后（ADR 0021 决策 2），弱电与兼有的节点至少是强电节点的三倍。
        self.assertGreaterEqual(len(weak), 3 * len(strong))
        self.assertTrue(strong, "强电节点不能缺：弱电优先不等于不写强电")
        for n in nodes:
            if n["stage"] == "junior":
                self.assertNotEqual(n["current"], "strong", n["id"])

    def test_codesign_map_covers_every_contract(self) -> None:
        nodes = find_map(DOC, "hw-sw-interface")["nodes"]
        self.assertEqual(len(nodes), 17)
        # 六份跨层契约每一份至少有一个节点；覆盖缺口要写在 summary 里，不能假装齐全。
        self.assertEqual({n["contract"] for n in nodes}, contract.KNOWN_CONTRACT)
        # 入门、中级、资深三档都有节点，阶段分列才有意义。
        self.assertEqual({n["stage"] for n in nodes}, set(contract.STAGE_RANK))
        self.assertIn("尚未覆盖", find_map(DOC, "hw-sw-interface")["summary"])

    def test_routes_cover_the_codesign_map_and_both_ends_of_the_axis(self) -> None:
        routes = DOC["routes"]
        self.assertEqual(len({r["id"] for r in routes}), len(routes))
        self.assertEqual({r["balance"] for r in routes}, contract.KNOWN_BALANCE)
        self.assertEqual({r["lens"] for r in routes}, contract.KNOWN_LENS)
        used = {n for r in routes for s in r["stages"] for n in s["nodes"]}
        orphans = [n["id"] for n in find_map(DOC, "hw-sw-interface")["nodes"] if n["id"] not in used]
        self.assertEqual(orphans, [], "软硬接口节点没有被任何一条路线引用")
        # 路线只引用节点 id、不复制节点：路线里不应出现节点自己的正文字段。
        for r in routes:
            self.assertFalse({"stable_definition", "practice", "pitfall"} & set(r))

    def test_every_node_has_practice_and_validation(self) -> None:
        for m in DOC["maps"]:
            for node in m["nodes"]:
                self.assertTrue(node["practice"].strip(), node["id"])
                self.assertTrue(node["validation"].strip(), node["id"])

    def test_course_graphs_keep_the_original_shape(self) -> None:
        cs = find_map(DOC, "computer-science")
        self.assertGreaterEqual(len(cs["nodes"]), 15)
        self.assertGreaterEqual(len(cs["edges"]), 13)
        cpp = find_node(DOC, "polaris.cs.cpp")
        self.assertIs(cpp["entry"], True)
        self.assertEqual(cpp["verify"], "code")
        self.assertEqual(cpp.get("requires", []), [])
        weak = [e for e in cs["edges"] if e["from"] == "polaris.cs.c_lang" and e["to"] == "polaris.cs.cpp"]
        self.assertEqual([e["relation"] for e in weak], ["enables"])

        ei = find_map(DOC, "electronic-information")
        self.assertGreaterEqual(len(ei["nodes"]), 13)
        basics = find_node(DOC, "polaris.ei.electronics_basics")
        self.assertIs(basics["entry"], True)
        self.assertEqual(basics["verify"], "bench")
        for node_id in ("polaris.ei.analog", "polaris.ei.digital"):
            find_node(DOC, node_id)

    def test_course_chapters_carry_necessity_and_practice(self) -> None:
        for map_id in ("computer-science", "electronic-information", "automation", "electrical-engineering"):
            for node in find_map(DOC, map_id)["nodes"]:
                self.assertGreaterEqual(len(node["chapters"]), 3, node["id"])
                self.assertTrue(node["priority_reason"].strip(), node["id"])
        # 计算机一章里，熟悉档的章节一律是理论（原 C++ 测试的断言）。
        for node in find_map(DOC, "computer-science")["nodes"]:
            for chapter in node["chapters"]:
                if chapter["mastery"] == "familiarity":
                    self.assertEqual(chapter["kind"], "theory", chapter["id"])

    def test_cross_map_dependency_stays_reachable(self) -> None:
        # C 语言在计算机一章、51 单片机在电子一章，这条强先修必须还在（ADR 0009 第 6 条）。
        links = [e for e in DOC["cross_edges"]
                 if e["from"] == "polaris.cs.c_lang" and e["to"] == "polaris.ei.mcu_8051"]
        self.assertEqual(len(links), 1)
        self.assertTrue(links[0]["rationale"].strip())


class Counterexamples(unittest.TestCase):
    """每条规则编号一个反例；断言「改坏之后这个编号一定出现」。"""

    def expect(self, code: str, mutate) -> None:
        with self.subTest(code=code):
            self.assertIn(code, codes_after(mutate))

    def test_document_and_sources(self) -> None:
        self.expect("doc.fields", lambda d: d.update(title=""))
        self.expect("doc.min_maps", lambda d: d.update(maps=d["maps"][:1]))
        self.expect("source.fields", lambda d: d["sources"][0].update(url=""))
        self.expect("source.duplicate_id", lambda d: d["sources"].append(copy.deepcopy(d["sources"][0])))
        self.expect("source.empty", lambda d: d.update(sources=[]))

    def test_maps(self) -> None:
        self.expect("map.fields", lambda d: d["maps"][0].update(summary=""))
        self.expect("map.duplicate_id", lambda d: d["maps"][1].update(id=d["maps"][0]["id"]))
        self.expect("map.min_nodes", lambda d: find_map(d, "target-gnc").update(
            nodes=find_map(d, "target-gnc")["nodes"][:2]))
        self.expect("map.theory", lambda d: d["maps"][0].update(theory=[{"name": "只有名字"}]))

    def test_nodes(self) -> None:
        self.expect("node.fields", lambda d: first_academic_node(d).update(stable_definition=""))
        self.expect("node.fields", lambda d: first_academic_node(d).update(pitfall=""))
        self.expect("node.duplicate_id", lambda d: find_map(d, "target-gnc")["nodes"][0].update(
            id=first_academic_node(d)["id"]))
        self.expect("node.validation", lambda d: first_academic_node(d).update(validation="bogus"))
        self.expect("node.volatility", lambda d: first_academic_node(d).update(volatility="bogus"))
        self.expect("node.priority", lambda d: first_academic_node(d).update(priority="bogus"))
        self.expect("node.domain", lambda d: first_academic_node(d).update(domain="bogus"))
        self.expect("node.domain", lambda d: first_academic_node(d).pop("domain"))
        self.expect("node.stage", lambda d: first_academic_node(d).update(stage="bogus"))
        self.expect("node.stage_reason", lambda d: first_academic_node(d).update(stage_reason=""))
        self.expect("node.targets_unknown", lambda d: first_academic_node(d).update(targets=["nope"]))
        self.expect("node.targets_kind", lambda d: first_academic_node(d).update(targets=["computer-science"]))
        self.expect("node.app", lambda d: first_academic_node(d).update(app="no-such-app"))
        self.expect("node.source_refs", lambda d: first_academic_node(d).update(source_refs=[]))
        self.expect("node.source_refs", lambda d: first_academic_node(d)["source_refs"][0].update(source_id="ghost"))
        self.expect("node.source_relation", lambda d: first_academic_node(d)["source_refs"][0].update(relation="informed"))
        self.expect("node.source_content", lambda d: [r.update(relation="see_also") for r in first_academic_node(d)["source_refs"]])
        self.expect("node.self_requires", lambda d: first_academic_node(d).update(
            requires=[first_academic_node(d)["id"]]))

    def test_course_nodes(self) -> None:
        cpp = lambda d: find_node(d, "polaris.cs.cpp")
        self.expect("course.entry", lambda d: cpp(d).pop("entry"))
        self.expect("course.verify", lambda d: cpp(d).update(verify="bogus"))
        self.expect("course.chapters_min", lambda d: cpp(d).update(chapters=cpp(d)["chapters"][:2]))
        self.expect("course.chapter_fields", lambda d: cpp(d)["chapters"][0].update(summary=""))
        self.expect("course.chapter_duplicate", lambda d: cpp(d)["chapters"][1].update(id=cpp(d)["chapters"][0]["id"]))
        self.expect("course.mastery", lambda d: cpp(d)["chapters"][0].update(mastery="bogus"))
        self.expect("course.practice", lambda d: cpp(d)["chapters"][0].update(
            mastery="usage", kind="theory", hands_on=False))
        self.expect("course.chapter_requires", lambda d: cpp(d)["chapters"][0].update(requires=["ghost"]))

    def test_requires_and_edges(self) -> None:
        def outside_map(d):
            first_academic_node(d)["requires"] = [find_map(d, "target-gnc")["nodes"][0]["id"]]

        def higher_stage(d):
            edge = a_requires_edge(d)
            find_node(d, edge["from"])["stage"] = "senior"
            find_node(d, edge["to"])["stage"] = "junior"

        def not_declared(d):
            edge = a_requires_edge(d)
            node = find_node(d, edge["to"])
            node["requires"] = [r for r in node["requires"] if r != edge["from"]]

        def enables_in_requires(d):
            edge = next(e for e in find_map(d, "computer-science")["edges"] if e["relation"] == "enables")
            find_node(d, edge["to"]).setdefault("requires", []).append(edge["from"])

        def missing_edge(d):
            m = find_map(d, "computer-science")
            edge = a_requires_edge(d)
            m["edges"] = [e for e in m["edges"] if e is not edge and e != edge]

        def cycle(d):
            edge = a_requires_edge(d)
            find_node(d, edge["from"]).setdefault("requires", []).append(edge["to"])

        self.expect("requires.outside_map", outside_map)
        self.expect("requires.higher_stage", higher_stage)
        self.expect("edge.requires_not_declared", not_declared)
        self.expect("edge.enables_in_requires", enables_in_requires)
        self.expect("edge.requires_missing_edge", missing_edge)
        self.expect("requires.cycle", cycle)
        self.expect("edge.fields", lambda d: a_requires_edge(d).update(rationale=""))
        self.expect("edge.endpoint", lambda d: a_requires_edge(d).update(to="ghost"))
        self.expect("edge.evidence", lambda d: a_requires_edge(d).update(evidence_refs=[]))
        self.expect("edge.relation", lambda d: a_requires_edge(d).update(relation="bogus"))

    def test_cross_edges(self) -> None:
        self.expect("cross.fields", lambda d: d["cross_edges"][0].update(rationale=""))
        self.expect("cross.endpoint", lambda d: d["cross_edges"][0].update(to="ghost"))
        self.expect("cross.same_map", lambda d: d["cross_edges"][0].update(
            to=next(e for e in find_map(d, "computer-science")["nodes"]
                    if e["id"] != d["cross_edges"][0]["from"])["id"],
            **{"from": find_map(d, "computer-science")["nodes"][0]["id"]}))
        self.expect("cross.duplicate", lambda d: d["cross_edges"].append(copy.deepcopy(d["cross_edges"][0])))
        self.expect("cross.evidence", lambda d: d["cross_edges"][0].update(evidence_refs=[]))

    def test_every_rule_code_has_a_counterexample(self) -> None:
        """防止新增规则忘了配反例：contract.py 里出现过的编号都必须在本文件里被引用。"""
        import re
        from pathlib import Path

        source = Path(contract.__file__).read_text(encoding="utf-8")
        declared = set(re.findall(r'"((?:doc|source|map|node|course|requires|edge|cross|codesign|route)\.[a-z_]+)"', source))
        tested = set(re.findall(r'"((?:doc|source|map|node|course|requires|edge|cross|codesign|route)\.[a-z_]+)"',
                                Path(__file__).read_text(encoding="utf-8")))
        self.assertEqual(sorted(declared - tested), [])


# —— 软硬接口图与路线：用最小夹具写反例，不依赖真实内容里写了多少 ——

def _node(node_id: str, stage: str, requires: list[str] | None = None) -> dict:
    return {
        "id": node_id, "title": node_id, "track": "hardware", "stable_definition": "x", "engineering_role": "x",
        "practice": "x", "validation": "measurement", "volatility": "stable", "pitfall": "x",
        "priority": "essential", "priority_reason": "x", "stage": stage, "stage_reason": "x",
        "contract": "timing", "hw_side": "硬件一侧提供什么", "sw_side": "软件一侧依赖什么", "domain": "embedded",
        "requires": requires or [], "source_refs": [{"relation": "adapted", "source_id": "csapp", "locator": "x"}],
    }


def _edge(src: str, dst: str) -> dict:
    return {"from": src, "to": dst, "relation": "requires", "rationale": "x", "strong": True,
            "evidence_refs": [{"relation": "adapted", "source_id": "csapp", "locator": "x"}]}


def with_codesign_and_route(document: dict) -> dict:
    """在真实内容上追加一张最小的 codesign 图（三阶段三节点）和一条引用它的路线。"""
    document["maps"].append({
        "id": "fixture-codesign", "title": "夹具", "summary": "夹具", "view_kind": "codesign", "discipline": "cross",
        "nodes": [_node("fx.a", "junior"), _node("fx.b", "intermediate", ["fx.a"]), _node("fx.c", "senior", ["fx.b"])],
        "edges": [_edge("fx.a", "fx.b"), _edge("fx.b", "fx.c")],
    })
    document["routes"] = [{
        "id": "route.fixture", "title": "夹具路线", "summary": "x", "lens": "direction", "balance": "balanced", "discipline": "cross",
        "audience": "x", "artifact": "一块点亮的板",
        "stages": [
            {"title": "起步", "goal": "x", "nodes": ["fx.a"], "checkpoint": "x"},
            {"title": "进阶", "goal": "x", "nodes": ["fx.b", "polaris.cs.c_lang"], "checkpoint": "x"},
        ],
        "source_refs": [{"relation": "adapted", "source_id": "csapp", "locator": "x"}],
    }]
    return document


def fixture_codes_after(mutate) -> set[str]:
    document = with_codesign_and_route(copy.deepcopy(DOC))
    mutate(document)
    return {v.code for v in contract.validate(document)}


def fixture_map(d: dict) -> dict:
    return find_map(d, "fixture-codesign")


class CodesignAndRoutes(unittest.TestCase):
    def test_fixture_is_clean(self) -> None:
        document = with_codesign_and_route(copy.deepcopy(DOC))
        self.assertEqual([str(v) for v in contract.validate(document)], [])

    def expect(self, code: str, mutate) -> None:
        with self.subTest(code=code):
            self.assertIn(code, fixture_codes_after(mutate))

    def test_codesign_nodes(self) -> None:
        self.expect("codesign.contract", lambda d: fixture_map(d)["nodes"][0].update(contract="bogus"))
        self.expect("codesign.sides", lambda d: fixture_map(d)["nodes"][0].update(hw_side=""))
        self.expect("codesign.sides", lambda d: fixture_map(d)["nodes"][0].pop("sw_side"))
        self.expect("node.stage_required", lambda d: fixture_map(d)["nodes"][0].pop("stage"))
        # codesign 节点不要求 targets：夹具里没有 targets 却是干净的（见 test_fixture_is_clean）。

    def test_routes(self) -> None:
        route = lambda d: d["routes"][0]
        self.expect("route.fields", lambda d: route(d).update(artifact=""))
        self.expect("route.duplicate_id", lambda d: d["routes"].append(copy.deepcopy(route(d))))
        self.expect("route.lens", lambda d: route(d).update(lens="bogus"))
        self.expect("route.balance", lambda d: route(d).update(balance="bogus"))
        self.expect("route.source_refs", lambda d: route(d).update(source_refs=[]))
        self.expect("route.stages_min", lambda d: route(d).update(stages=route(d)["stages"][:1]))
        self.expect("route.stage_fields", lambda d: route(d)["stages"][0].update(checkpoint=""))
        self.expect("route.stage_nodes", lambda d: route(d)["stages"][0].update(nodes=[]))
        self.expect("route.node_unknown", lambda d: route(d)["stages"][0].update(nodes=["ghost"]))
        # 路线只能引用开放地图：参考层的 target-gnc 节点不行。
        self.expect("route.node_closed", lambda d: route(d)["stages"][0].update(
            nodes=[find_map(d, "target-gnc")["nodes"][0]["id"]]))
        self.expect("route.node_repeated", lambda d: route(d)["stages"][1]["nodes"].append("fx.a"))
        # fx.b 强先修 fx.a：把 fx.a 排到 fx.b 之后的阶段就违反次序。
        self.expect("route.order", lambda d: route(d).update(stages=[
            {"title": "先", "goal": "x", "nodes": ["fx.b"], "checkpoint": "x"},
            {"title": "后", "goal": "x", "nodes": ["fx.a"], "checkpoint": "x"},
        ]))

    def test_open_view_kinds_match_the_frontend(self) -> None:
        """开放地图的定义在 contract.py 与 src/content/catalog.ts 各有一份，防止改一处漏一处。"""
        import re
        from pathlib import Path

        text = (Path(contract.__file__).resolve().parent.parent / "src" / "content" / "catalog.ts").read_text(encoding="utf-8")
        match = re.search(r"OPEN_VIEW_KINDS: readonly ViewKind\[\] = \[(.*?)\]", text)
        self.assertIsNotNone(match)
        self.assertEqual(set(re.findall(r'"(\w+)"', match.group(1))), contract.OPEN_VIEW_KINDS)


class DepthAndBalance(unittest.TestCase):
    """ADR 0018：十二个能力域、通才阶梯、纵深图、学习原则。"""

    def test_every_open_node_has_a_domain_and_every_domain_is_used(self) -> None:
        used = {n["domain"] for m in DOC["maps"] if m["view_kind"] in contract.OPEN_VIEW_KINDS for n in m["nodes"]}
        self.assertEqual(used, contract.KNOWN_DOMAIN)

    def test_the_ladder_leaves_no_domain_out(self) -> None:
        # 通才阶梯是「不偏科」的承诺：十二个能力域一个都不缺，有测试守着。
        ladder = next(r for r in DOC["routes"] if r["id"] == "route.generalist-ladder")
        node_domain = {n["id"]: n["domain"] for m in DOC["maps"] for n in m["nodes"] if "domain" in n}
        covered = {node_domain[i] for st in ladder["stages"] for i in st["nodes"]}
        self.assertEqual(sorted(contract.KNOWN_DOMAIN - covered), [])
        self.assertEqual(len(ladder["stages"]), 5)

    def test_every_frontier_node_is_on_some_route(self) -> None:
        used = {n for r in DOC["routes"] for s in r["stages"] for n in s["nodes"]}
        orphans = [n["id"] for n in find_map(DOC, "frontier-depth")["nodes"] if n["id"] not in used]
        self.assertEqual(orphans, [])

    def test_every_route_has_pitfalls_and_depth_routes_are_after_the_ladder(self) -> None:
        for r in DOC["routes"]:
            self.assertTrue(r.get("pitfalls"), r["id"])
        self.assertEqual(DOC["routes"][0]["id"], "route.generalist-ladder")

    def test_profiles_are_sourced_samples_not_promises(self) -> None:
        profiled = [r for r in DOC["routes"] if "profile" in r]
        self.assertGreaterEqual(len(profiled), 2)
        for r in profiled:
            self.assertIn("时效性样本", r["profile"])
            self.assertIn("不构成录用承诺", r["profile"])
            self.assertTrue(any(ref["source_id"].endswith("-job") for ref in r["source_refs"]), r["id"])

    DEPTH_ROUTES = ["route.cpu-soc-architecture", "route.digital-ic-verification", "route.ai-accelerator-systems",
                    "route.firmware-trusted", "route.highrel-aerospace"]

    def test_every_node_on_a_depth_route_has_chapters(self) -> None:
        # ADR 0019：五条纵深路线用到的节点必须全部细化到章节。
        nodes = {n["id"]: n for m in DOC["maps"] for n in m["nodes"]}
        for route in (r for r in DOC["routes"] if r["id"] in self.DEPTH_ROUTES):
            for stage in route["stages"]:
                for node_id in stage["nodes"]:
                    self.assertGreaterEqual(len(nodes[node_id].get("chapters", [])), 3, f"{route['id']} / {node_id}")

    def test_every_open_node_has_chapters(self) -> None:
        # ADR 0020：开放地图的每个节点都细化到章节，新增节点时必须同时写章节。
        missing = [n["id"] for m in DOC["maps"] if m["view_kind"] in contract.OPEN_VIEW_KINDS
                   for n in m["nodes"] if len(n.get("chapters", [])) < 3]
        self.assertEqual(missing, [])

    def test_every_depth_chapter_list_ends_with_something_you_make(self) -> None:
        # 最后一章是做出来的验收（评估档、实践），不是又一个概念。
        for m in DOC["maps"]:
            if m["view_kind"] not in ("codesign", "frontier"):
                continue
            for n in m["nodes"]:
                if "chapters" in n:
                    last = n["chapters"][-1]
                    self.assertEqual(last["mastery"], "assessment", n["id"])
                    self.assertTrue(last.get("hands_on"), n["id"])

    def test_principles_are_sourced(self) -> None:
        principles = DOC["principles"]
        self.assertGreaterEqual(len(principles), 7)
        for p in principles:
            self.assertTrue(p["source_refs"], p["id"])
            self.assertTrue(any(r["relation"] == "adapted" for r in p["source_refs"]), p["id"])

    def test_counterexamples_for_the_new_rules(self) -> None:
        def expect(code, mutate):
            with self.subTest(code=code):
                self.assertIn(code, codes_after(mutate))

        expect("course.chapter_ref", lambda d: find_map(d, "frontier-depth")["nodes"][0]["chapters"][0]["ref"].update(source_id="ghost"))
        expect("course.chapter_ref", lambda d: find_map(d, "frontier-depth")["nodes"][0]["chapters"][0]["ref"].update(locator=""))
        # 章节先修只能指向排在前面的章节
        expect("course.chapter_requires", lambda d: find_map(d, "frontier-depth")["nodes"][0]["chapters"][0].update(requires=["math.apply"]))
        expect("course.chapters_min", lambda d: find_map(d, "frontier-depth")["nodes"][0].update(chapters=find_map(d, "frontier-depth")["nodes"][0]["chapters"][:2]))
        expect("map.discipline", lambda d: d["maps"][0].update(discipline="bogus"))
        expect("route.discipline", lambda d: d["routes"][0].pop("discipline"))
        expect("node.current", lambda d: find_map(d, "electrical-engineering")["nodes"][0].update(current="bogus"))
        expect("node.current_required", lambda d: find_map(d, "electrical-engineering")["nodes"][0].pop("current"))
        expect("principle.fields", lambda d: d["principles"][0].update(body=""))
        expect("principle.duplicate_id", lambda d: d["principles"].append(copy.deepcopy(d["principles"][0])))
        expect("principle.source_refs", lambda d: d["principles"][0].update(source_refs=[]))
        expect("route.pitfalls", lambda d: d["routes"][0].update(pitfalls=[]))
        expect("route.pitfalls", lambda d: d["routes"][0].update(pitfalls=["", "x"]))
        expect("route.profile", lambda d: next(r for r in d["routes"] if "profile" in r).update(profile=""))
        # frontier 节点同样必须有 stage 与 domain
        expect("node.stage_required", lambda d: find_map(d, "frontier-depth")["nodes"][0].pop("stage"))
        expect("node.domain", lambda d: find_map(d, "frontier-depth")["nodes"][0].pop("domain"))


if __name__ == "__main__":
    unittest.main()
