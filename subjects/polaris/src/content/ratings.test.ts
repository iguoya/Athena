import { describe, expect, it } from "vitest";
import { loadCatalog } from "./load";
import {
  FIELD_IDS,
  POLICY_SCHEME,
  RATING_DIMS,
  RATING_SCHEME,
  VERDICTS,
  fieldDef,
  fieldKey,
  isFieldKey,
  levelName,
  lensLevel,
  lensLevels,
  lensTitle,
  ratingVar,
  routeDimMean,
  routeFieldMean,
  routesByField,
  routesByOutlook,
  routesByVerdict,
  strongAndWeak,
} from "./ratings";

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

  it("国家重点领域：九个领域，使用者点名的六个是目标方向；支持度 = 1 + 信号类别数，每条信号都有出处", () => {
    expect(FIELD_IDS.length).toBe(9);
    expect(POLICY_SCHEME.fields.filter((f) => f.headline).map((f) => f.id).sort()).toEqual(["ai", "chip", "pcb", "robot", "satcom", "uav"]);
    for (const field of POLICY_SCHEME.fields) {
      expect(field.support.level, field.id).toBe(1 + new Set(field.signals.map((s) => s.kind)).size);
      for (const signal of field.signals) expect(catalog.sources.has(signal.source_id), `${field.id}/${signal.source_id}`).toBe(true);
    }
    expect(fieldDef("chip")?.support.level).toBe(5);
  });

  it("视角工具：领域视角是「1 无关」加 2–5 级；节点没写的领域按 1；参考层节点没有评级", () => {
    const key = fieldKey("nev");
    expect(isFieldKey(key)).toBe(true);
    expect(isFieldKey("utility")).toBe(false);
    expect(lensTitle(key)).toBe("新能源汽车");
    expect(lensLevels(key).map((l) => l.level)).toEqual([1, 2, 3, 4, 5]);
    expect(levelName(key, 5)).toBe("核心支撑");
    expect(levelName(key, 1)).toBe("无关");
    const battery = catalog.nodeById.get("polaris.ee.battery_bms")!;
    expect(lensLevel(battery, key)).toBe(5);
    expect(lensLevel(battery, fieldKey("satcom"))).toBe(2);
    expect(lensLevel(catalog.nodeById.get("polaris.ee.circuit_analysis")!, fieldKey("ai"))).toBe(1);
    const reference = catalog.allMaps.find((m) => !catalog.isOpenMap(m.id))!.nodes[0];
    expect(lensLevel(reference, key)).toBeUndefined();
  });

  it("每个领域最契合的路线：均值从高到低，且是该领域里最相关的方向", () => {
    for (const fid of FIELD_IDS) {
      const top = routesByField(catalog, catalog.routes, fid, 3);
      expect(top.length).toBe(3);
      for (let i = 1; i < top.length; i++) expect(top[i - 1].mean).toBeGreaterThanOrEqual(top[i].mean);
      expect(top[0].mean).toBe(routeFieldMean(catalog, top[0].route, fid));
    }
    expect(routesByField(catalog, catalog.routes, "chip", 1)[0].route.id).toBe("route.semiconductor-chip");
    expect(routesByField(catalog, catalog.routes, "satcom", 1)[0].route.id).toBe("route.satcom-leo");
    expect(routesByField(catalog, catalog.routes, "ai", 1)[0].route.id).toBe("route.ml-foundations");
  });

  it("前景与国家投入一致：前景为 5 级的节点都至少对应一个支持度为 5 的领域", () => {
    for (const map of catalog.maps) {
      for (const node of map.nodes) {
        if (node.ratings?.outlook.level !== 5) continue;
        const strong = Object.entries(node.fields ?? {}).some(([fid, item]) => item.level >= 4 && fieldDef(fid)?.support.level === 5);
        expect(strong, node.id).toBe(true);
      }
    }
  });
});
