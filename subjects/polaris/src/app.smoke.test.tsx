// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeAll, beforeEach, describe, expect, it } from "vitest";
import { App } from "./App";
import { loadCatalog } from "./content/load";
import type { Location } from "./state/router";
import { useApp } from "./state/store";

// 冒烟：每个位置都能真的渲染出来（含副作用），且不会因为某一条内容而崩。逻辑层有各自的单测，
// 这里只看「渲染得出」；平移、缩放、拖动这类要真实指针的交互，靠开发服务器里实际打开看。

const catalog = loadCatalog();

beforeAll(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  // happy-dom 没有真正的布局，画布量到的尺寸是 0，视口适配会跳过；动画在这里不需要。
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

let container: HTMLElement;
let root: Root;

beforeEach(() => {
  useApp.setState({ aimByMap: {}, drawerWide: false, hoverId: null, edgeKey: null });
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

function render(loc: Location): string {
  act(() => {
    useApp.setState({ loc });
    root.render(<App />);
  });
  return container.innerHTML;
}

describe("界面冒烟", () => {
  it("总览：每条路线的标题都出现，空格子也有占位", () => {
    const html = render({ view: "home" });
    for (const route of catalog.routes) expect(html).toContain(route.title);
    expect(html).toContain("偏软件");
    expect(html).toContain("偏硬件");
    expect(html).toContain("这里还没有路线");
  });

  for (const route of catalog.routes) {
    it(`路线 ${route.id}：标题、阶段与终点产物都在`, () => {
      const html = render({ view: "route", routeId: route.id });
      expect(html).toContain(route.title);
      expect(html).toContain(route.artifact.slice(0, 12));
      for (const stage of route.stages) expect(html).toContain(stage.title);
      // 路线里的每个节点都渲染成卡片
      for (const stage of route.stages) for (const id of stage.nodes) expect(html).toContain(`data-node-id="${id}"`);
    });
  }

  for (const map of catalog.maps) {
    it(`底盘 ${map.id}：每个节点都渲染成卡片`, () => {
      const html = render({ view: "base", mapId: map.id });
      for (const node of map.nodes) expect(html).toContain(`data-node-id="${node.id}"`);
    });
  }

  it("节点抽屉：软硬接口节点同时显示硬件一侧与软件一侧，出处可见", () => {
    const html = render({ view: "base", mapId: "hw-sw-interface", nodeId: "polaris.codesign.dma_cache" });
    expect(html).toContain("硬件一侧");
    expect(html).toContain("软件一侧");
    expect(html).toContain("出处");
    expect(html).toContain("三问");
  });

  it("课程节点的抽屉里有细分学习流程", () => {
    const html = render({ view: "base", mapId: "computer-science", nodeId: "polaris.cs.cpp" });
    expect(html).toContain("细分学习流程");
  });

  it("内容里有的字段，界面里都看得见：理论科目、工程现场的支撑、验证方式、下游应用", () => {
    expect(render({ view: "base", mapId: "computer-science" })).toContain("不建节点的理论科目");
    const nodes = catalog.maps.flatMap((m) => m.nodes.map((n) => ({ map: m.id, node: n })));
    const withIndustry = nodes.find(({ node }) => node.industry_reason)!;
    expect(render({ view: "base", mapId: withIndustry.map, nodeId: withIndustry.node.id })).toContain("在工程现场它还支撑");
    const withApp = nodes.find(({ node }) => node.app)!;
    expect(render({ view: "base", mapId: withApp.map, nodeId: withApp.node.id })).toContain("下游的学习应用");
    const withVerify = nodes.find(({ node }) => node.verify)!;
    expect(render({ view: "base", mapId: withVerify.map, nodeId: withVerify.node.id })).toMatch(/写代码验证|上板验证|台架与仪器测量/);
  });

  it("不存在的路线或参考层的图：给出说明而不是白屏", () => {
    expect(render({ view: "route", routeId: "route.nope" })).toContain("找不到这条路线");
    expect(render({ view: "base", mapId: "target-gnc" })).toContain("不对外开放");
  });
});
