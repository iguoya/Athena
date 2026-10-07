import { describe, expect, it } from "vitest";
import { loadCatalog } from "./load";
import { RATING_DIMS, RATING_SCHEME, VERDICTS, levelName, ratingVar, routeDimMean, routesByOutlook, routesByVerdict, strongAndWeak } from "./ratings";

const catalog = loadCatalog();

describe("评级（ADR 0022）", () => {
  it("口径里是七个维度，每个五级，等级名都不空", () => {
    expect(RATING_DIMS).toEqual(["utility", "hands_on", "theory", "verifiable", "core", "demand", "outlook"]);
    for (const dim of RATING_SCHEME.dimensions) {
      expect(dim.levels.map((l) => l.level)).toEqual([1, 2, 3, 4, 5]);
      for (const level of dim.levels) expect(level.name.trim(), `${dim.id}/${level.level}`).not.toBe("");
    }
  });

  it("开放地图的每个节点、每条路线都有全部维度，且等级都在 1–5", () => {
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
    expect(levelName("outlook", 1)).toBe("萎缩");
    expect(levelName("outlook", 5)).toBe("前景广阔");
    expect(ratingVar(0)).toBe("var(--rate-1)");
    expect(ratingVar(3)).toBe("var(--rate-3)");
    expect(ratingVar(9)).toBe("var(--rate-5)");
  });

  it("强项是 ≥4 级、弱项是 ≤2 级，缺评级时两者都为空", () => {
    expect(strongAndWeak(undefined)).toEqual({ strong: [], weak: [] });
    const make = (levels: number[]) =>
      Object.fromEntries(RATING_DIMS.map((dim, i) => [dim, { level: levels[i], reason: "x" }])) as never;
    expect(strongAndWeak(make([4, 3, 5, 2, 1, 3, 3]))).toEqual({ strong: ["utility", "theory"], weak: ["verifiable", "core"] });
  });

  it("市场需求度是「市场」口径，id 仍是 demand；技术前景是第七个维度", () => {
    const demand = RATING_SCHEME.dimensions.find((d) => d.id === "demand")!;
    expect(demand.title).toBe("市场需求度");
    expect(RATING_SCHEME.dimensions.map((d) => d.title)).not.toContain("就业需求度");
    expect(RATING_SCHEME.dimensions.at(-1)!.title).toBe("技术发展前景");
  });

  it("技术前景最好的方向：只含汇总前景 ≥4 的路线，按均值从高到低；均值四舍五入就是路线的评级", () => {
    const list = routesByOutlook(catalog, catalog.routes);
    expect(list.length).toBeGreaterThan(0);
    for (const { route, mean } of list) {
      expect(route.ratings!.outlook.level).toBeGreaterThanOrEqual(4);
      expect(Math.floor(mean + 0.5)).toBe(route.ratings!.outlook.level);
    }
    for (let i = 1; i < list.length; i++) expect(list[i - 1].mean).toBeGreaterThanOrEqual(list[i].mean);
    expect(routeDimMean(catalog, catalog.routes[0], "outlook")).toBeGreaterThan(0);
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
