import { describe, expect, it } from "vitest";
import { formatHash, parseHash, type Location } from "./router";

describe("哈希路由", () => {
  const cases: Location[] = [
    { view: "home" },
    { view: "route", routeId: "route.codesign-spine" },
    { view: "route", routeId: "route.embedded-realtime", nodeId: "polaris.codesign.mmio" },
    { view: "base", mapId: "computer-science" },
    { view: "base", mapId: "hw-sw-interface", nodeId: "polaris.codesign.interrupts" },
  ];

  it("format 与 parse 互为逆运算", () => {
    for (const location of cases) {
      const parsed = parseHash(formatHash(location));
      expect(parsed).toMatchObject(location);
    }
  });

  it("不认识的哈希回到总览，不抛错", () => {
    expect(parseHash("")).toEqual({ view: "home" });
    expect(parseHash("#/nope/whatever")).toEqual({ view: "home" });
    expect(parseHash("#/route")).toEqual({ view: "home" });
  });

  it("id 里的点和连字符不需要转义，特殊字符会被编码", () => {
    expect(formatHash({ view: "base", mapId: "hw-sw-interface" })).toBe("#/base/hw-sw-interface");
    expect(parseHash(formatHash({ view: "base", mapId: "a/b", nodeId: "x?y" }))).toMatchObject({ mapId: "a/b", nodeId: "x?y" });
  });
});
