import { describe, expect, it } from "vitest";
import { loadCatalog } from "./load";
import { BALANCES, LENSES, layoutRoute, routeEdges, routeMatrix, routeNodeCount, routesOfNode } from "./routes";

const catalog = loadCatalog();

describe("路线", () => {
  it("路线引用的节点都存在，且只来自开放地图（ADR 0016 决策 3）", () => {
    expect(catalog.routes.length).toBeGreaterThanOrEqual(10);
    for (const route of catalog.routes) {
      for (const stage of route.stages) {
        for (const id of stage.nodes) {
          expect(catalog.nodeById.has(id), id).toBe(true);
          expect(catalog.isOpenMap(catalog.mapIdOfNode.get(id)!), id).toBe(true);
        }
      }
    }
  });

  for (const route of catalog.routes) {
    describe(route.id, () => {
      const layout = layoutRoute(catalog, route);

      it("列数等于阶段数，每个节点恰好放一次", () => {
        expect(layout.columns.length).toBe(route.stages.length);
        expect(layout.nodes.length).toBe(routeNodeCount(route));
        expect(new Set(layout.nodes.map((n) => n.id)).size).toBe(layout.nodes.length);
      });

      it("每个节点都落在它所属阶段的那一列", () => {
        route.stages.forEach((stage, index) => {
          for (const id of stage.nodes) expect(layout.byId.get(id)!.column).toBe(index);
        });
      });

      it("边只取两端都在路线里的，且不重复", () => {
        const edges = routeEdges(catalog, route);
        const keys = edges.map((e) => `${e.from}>${e.to}`);
        expect(new Set(keys).size).toBe(keys.length);
        for (const edge of edges) {
          expect(layout.byId.has(edge.from) && layout.byId.has(edge.to)).toBe(true);
        }
        expect(layout.edges.length).toBe(edges.length);
      });

      it("路线里的强先修不会向左指（契约保证，布局再确认一遍）", () => {
        for (const { edge } of layout.edges) {
          if (edge.relation !== "requires") continue;
          expect(layout.byId.get(edge.from)!.column).toBeLessThanOrEqual(layout.byId.get(edge.to)!.column);
        }
      });
    });
  }

  it("总览矩阵覆盖全部路线，且每个软硬权重都至少有一条", () => {
    const matrix = routeMatrix(catalog);
    const flat = LENSES.flatMap((lens) => BALANCES.flatMap((balance) => matrix[lens][balance]));
    expect(flat.length).toBe(catalog.routes.length);
    for (const balance of BALANCES) {
      expect(LENSES.some((lens) => matrix[lens][balance].length > 0), balance).toBe(true);
    }
  });

  it("反查：MMIO 出现在多条路线里，参考层节点不在任何路线里", () => {
    expect(routesOfNode(catalog, "polaris.codesign.mmio").length).toBeGreaterThanOrEqual(4);
    expect(routesOfNode(catalog, "polaris.target.gnc.fusion")).toEqual([]);
  });
});
