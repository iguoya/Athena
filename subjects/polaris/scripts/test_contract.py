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

    def test_map_inventory(self) -> None:
        self.assertEqual(len(DOC["maps"]), 17)
        by_kind: dict[str, int] = {}
        for m in DOC["maps"]:
            by_kind[m["view_kind"]] = by_kind.get(m["view_kind"], 0) + 1
        # 课程知识图谱恢复为两章，实践主干两张仍在（ADR 0010）；只开放 4 张学术图（ADR 0012）。
        self.assertEqual(by_kind["academic"], 4)
        self.assertEqual(by_kind["target"], 8)
        self.assertEqual(by_kind.get("career", 0) + by_kind.get("engineering", 0), 5)
        self.assertEqual(DOC["maps"][0]["id"], "computer-science")

    def test_every_node_has_practice_and_validation(self) -> None:
        for m in DOC["maps"]:
            for node in m["nodes"]:
                self.assertTrue(node["practice"].strip(), node["id"])
                self.assertTrue(node["validation"].strip(), node["id"])

    def test_course_graphs_keep_the_original_shape(self) -> None:
        cs = find_map(DOC, "computer-science")
        self.assertEqual(len(cs["nodes"]), 15)
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
        for map_id in ("computer-science", "electronic-information"):
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
        self.expect("node.stage", lambda d: first_academic_node(d).update(stage="bogus"))
        self.expect("node.stage_reason", lambda d: first_academic_node(d).update(stage_reason=""))
        self.expect("node.targets_missing", lambda d: first_academic_node(d).update(targets=[]))
        self.expect("node.targets_unknown", lambda d: first_academic_node(d).update(targets=["nope"]))
        self.expect("node.targets_kind", lambda d: first_academic_node(d).update(targets=["computer-science"]))
        self.expect("node.app", lambda d: first_academic_node(d).update(app="no-such-app"))
        self.expect("node.source_refs", lambda d: first_academic_node(d).update(source_refs=[]))
        self.expect("node.source_refs", lambda d: first_academic_node(d)["source_refs"][0].update(source_id="ghost"))
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
        declared = set(re.findall(r'"((?:doc|source|map|node|course|requires|edge|cross)\.[a-z_]+)"', source))
        tested = set(re.findall(r'"((?:doc|source|map|node|course|requires|edge|cross)\.[a-z_]+)"',
                                Path(__file__).read_text(encoding="utf-8")))
        self.assertEqual(sorted(declared - tested), [])


if __name__ == "__main__":
    unittest.main()
