import { describe, expect, it } from "vitest";
import { DOMAINS, LADDER_ID, blindSpots, coveredDomains, domainTotals, routeCoverage } from "./coverage";
import { loadCatalog } from "./load";

const catalog = loadCatalog();
const route = (id: string) => catalog.routes.find((r) => r.id === id)!;

describe("能力域覆盖", () => {
  it("十二个域都有节点，开放地图的每个节点都归入某个域", () => {
    const totals = domainTotals(catalog);
    expect(DOMAINS.length).toBe(12);
    for (const { id } of DOMAINS) expect(totals.get(id) ?? 0, id).toBeGreaterThan(0);
    const open = catalog.maps.flatMap((m) => m.nodes);
    expect([...totals.values()].reduce((a, b) => a + b, 0)).toBe(open.length);
  });

  it("通才阶梯覆盖十二个域，没有偏科提示", () => {
    const ladder = route(LADDER_ID);
    expect(coveredDomains(catalog, ladder)).toBe(12);
    expect(blindSpots(catalog, ladder)).toEqual([]);
  });

  it("纵深方向的路线碰不到的域会被指出，并给出来自阶梯的补法", () => {
    const direction = route("route.digital-ic-verification");
    const spots = blindSpots(catalog, direction);
    expect(spots.length).toBeGreaterThan(0);
    const ladderIds = new Set(route(LADDER_ID).stages.flatMap((s) => s.nodes));
    const have = new Set(direction.stages.flatMap((s) => s.nodes));
    for (const spot of spots) {
      expect(spot.suggestions.length).toBeGreaterThan(0);
      for (const node of spot.suggestions) {
        expect(node.domain).toBe(spot.domain);
        expect(ladderIds.has(node.id)).toBe(true);
        expect(have.has(node.id)).toBe(false);
      }
    }
  });

  it("覆盖率在 [0,1]，且 covered 不超过 total", () => {
    for (const r of catalog.routes) {
      for (const entry of routeCoverage(catalog, r)) {
        expect(entry.fraction).toBeGreaterThanOrEqual(0);
        expect(entry.fraction).toBeLessThanOrEqual(1);
        expect(entry.covered).toBeLessThanOrEqual(entry.total);
      }
    }
  });
});
