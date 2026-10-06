import { describe, expect, it } from "vitest";
import { OPEN_VIEW_KINDS, priorityRank, stageRank } from "./catalog";
import { loadCatalog } from "./load";

const catalog = loadCatalog();

describe("目录索引", () => {
  it("只开放学术图与软硬接口图，参考层图仍在内容里但不开放", () => {
    for (const map of catalog.maps) expect(OPEN_VIEW_KINDS).toContain(map.view_kind);
    const openIds = catalog.maps.map((map) => map.id);
    // 原有 4 张学术图一张不少，默认入口仍是第一张（ADR 0012、0016）。
    expect(openIds.slice(0, 4)).toEqual([
      "computer-science",
      "electronic-information",
      "computer-practice",
      "electronic-practice",
    ]);
    expect(catalog.isOpenMap("embedded-realtime")).toBe(false);
    expect(catalog.isOpenMap("target-gnc")).toBe(false);
    // 内容一个不删：全部地图仍在。
    expect(catalog.allMaps.length).toBeGreaterThanOrEqual(17);
  });

  it("每个节点 id 全局唯一，且能反查所在地图", () => {
    let total = 0;
    for (const map of catalog.allMaps) {
      for (const node of map.nodes) {
        total += 1;
        expect(catalog.mapIdOfNode.get(node.id)).toBe(map.id);
      }
    }
    expect(catalog.nodeById.size).toBe(total);
  });

  it("跨图关联能顺着走到对端：C 语言 → 51 单片机", () => {
    const links = catalog.crossLinks("polaris.ei.mcu_8051");
    const fromC = links.find((link) => link.peerId === "polaris.cs.c_lang");
    expect(fromC?.incoming).toBe(true);
    expect(fromC?.peerMapId).toBe("computer-science");
    expect(fromC?.edge.rationale.trim()).not.toBe("");
  });

  it("入边与出边：C 语言只是 C++ 的虚线来路（enables），不是强先修", () => {
    const { inbound } = catalog.edgesOf("polaris.cs.cpp");
    const fromC = inbound.find((edge) => edge.from === "polaris.cs.c_lang");
    expect(fromC?.relation).toBe("enables");
  });

  it("每个节点的出处都能在来源目录里找到", () => {
    for (const node of catalog.nodeById.values()) {
      for (const ref of node.source_refs) expect(catalog.sources.has(ref.source_id)).toBe(true);
    }
  });

  it("排序约定：阶段由低到高，必要程度 essential 在前，缺省排最后", () => {
    expect(stageRank("junior")).toBeLessThan(stageRank("intermediate"));
    expect(stageRank("intermediate")).toBeLessThan(stageRank("senior"));
    expect(stageRank(undefined)).toBe(stageRank("senior"));
    expect(priorityRank("essential")).toBeLessThan(priorityRank("important"));
    expect(priorityRank(undefined)).toBe(priorityRank("optional"));
  });
});
