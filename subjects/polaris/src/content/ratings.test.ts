import { describe, expect, it } from "vitest";
import { loadCatalog } from "./load";
import { RATING_DIMS, RATING_SCHEME, VERDICTS, levelName, ratingVar, routesByVerdict, strongAndWeak } from "./ratings";

const catalog = loadCatalog();

describe("评级（ADR 0022）", () => {
  it("口径里是六个维度，每个五级，等级名都不空", () => {
    expect(RATING_DIMS).toEqual(["utility", "hands_on", "theory", "verifiable", "core", "demand"]);
    for (const dim of RATING_SCHEME.dimensions) {
      expect(dim.levels.map((l) => l.level)).toEqual([1, 2, 3, 4, 5]);
      for (const level of dim.levels) expect(level.name.trim(), `${dim.id}/${level.level}`).not.toBe("");
    }
  });

  it("开放地图的每个节点、每条路线都有六个维度，且等级都在 1–5", () => {
    for (const map of catalog.maps) {
      for (const node of map.nodes) {
        for (const dim of RATING_DIMS) {
          const level = node.ratings?.[dim]?.level;
          expect(level, `${node.id}/${dim}`).toBeGreaterThanOrEqual(1);
          expect(level, `${node.id}/${dim}`).toBeLessThanOrEqual(5);
        }
      }
    }
    for (const route of catalog.routes) {
      expect(route.ratings, route.id).toBeDefined();
      expect(route.assessment, route.id).toBeDefined();
    }
  });

  it("参考层的节点不评级", () => {
    for (const map of catalog.allMaps) {
      if (catalog.isOpenMap(map.id)) continue;
      for (const node of map.nodes) expect(node.ratings, node.id).toBeUndefined();
    }
  });

  it("等级名按口径查，颜色变量落在 1–5 之内", () => {
    expect(levelName("utility", 5)).toBe("日常必备");
    expect(levelName("demand", 1)).toBe("小众");
    expect(ratingVar(0)).toBe("var(--rate-1)");
    expect(ratingVar(3)).toBe("var(--rate-3)");
    expect(ratingVar(9)).toBe("var(--rate-5)");
  });

  it("强项是 ≥4 级、弱项是 ≤2 级，缺评级时两者都为空", () => {
    expect(strongAndWeak(undefined)).toEqual({ strong: [], weak: [] });
    const make = (levels: number[]) =>
      Object.fromEntries(RATING_DIMS.map((dim, i) => [dim, { level: levels[i], reason: "x" }])) as never;
    expect(strongAndWeak(make([4, 3, 5, 2, 1, 3]))).toEqual({ strong: ["utility", "theory"], weak: ["verifiable", "core"] });
  });

  it("按推荐等级分组：四档齐全，路线一条不丢；每条后续方向都指向存在的别条路线", () => {
    const groups = routesByVerdict(catalog.routes);
    expect(VERDICTS.reduce((sum, v) => sum + groups[v].length, 0)).toBe(catalog.routes.length);
    expect(groups.priority.length).toBeGreaterThan(0);
    const ids = new Set(catalog.routes.map((r) => r.id));
    for (const route of catalog.routes) {
      for (const next of route.assessment!.next) {
        expect(ids.has(next.route_id), `${route.id} → ${next.route_id}`).toBe(true);
        expect(next.route_id).not.toBe(route.id);
      }
    }
  });
});
