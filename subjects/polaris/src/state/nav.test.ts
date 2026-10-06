import { describe, expect, it } from "vitest";
import { loadCatalog } from "@/content/load";
import { locationForNode } from "./nav";

const catalog = loadCatalog();

describe("节点跳转", () => {
  it("在路线里跳到同一路线的节点：留在路线", () => {
    const route = catalog.routes.find((r) => r.id === "route.embedded-realtime")!;
    const target = route.stages[1].nodes[0];
    expect(locationForNode(catalog, { view: "route", routeId: route.id }, target)).toEqual({
      view: "route",
      routeId: route.id,
      nodeId: target,
    });
  });

  it("跳到路线之外的节点：去它所在的开放地图", () => {
    const location = locationForNode(catalog, { view: "route", routeId: "route.embedded-realtime" }, "polaris.cs.da");
    expect(location).toEqual({ view: "base", mapId: "computer-science", nodeId: "polaris.cs.da" });
  });

  it("参考层节点没有去处，不提供跳转", () => {
    expect(locationForNode(catalog, { view: "home" }, "polaris.target.gnc.fusion")).toBeNull();
  });

  it("同一张图内跳转只换选中", () => {
    expect(locationForNode(catalog, { view: "base", mapId: "computer-science" }, "polaris.cs.cpp")).toEqual({
      view: "base",
      mapId: "computer-science",
      nodeId: "polaris.cs.cpp",
    });
  });
});
