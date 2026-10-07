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
  useApp.setState({ drawerWide: false, hoverId: null, edgeKey: null });
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

  it("总览按专业类：四类阶梯入口与筛选；切到电气类后只剩电气类的路线", () => {
    let html = render({ view: "home" });
    for (const name of ["计算机类主干阶梯", "电子信息类主干阶梯", "电气类主干阶梯", "自动化类主干阶梯"]) expect(html).toContain(name);
    const button = [...container.querySelectorAll("button")].find((b) => b.textContent?.startsWith("电气类") && b.getAttribute("aria-pressed") !== null)!;
    act(() => button.click());
    html = container.innerHTML;
    for (const route of catalog.routes.filter((r) => r.discipline === "ee")) expect(html).toContain(route.title);
    expect(html).not.toContain("实时控制与半实物仿真");
  });

  it("电气类的节点卡片与抽屉标出弱电 / 强电", () => {
    const html = render({ view: "base", mapId: "electrical-engineering", nodeId: "polaris.ee.electric_machines" });
    expect(html).toContain("强电");
    expect(html).toContain("弱电");
  });

  it("总览有推荐发展方向（按推荐等级分组），路线卡片带推荐等级与各维迷你条", () => {
    const html = render({ view: "home" });
    expect(html).toContain("推荐发展方向");
    for (const label of ["优先推荐", "推荐", "可选", "进阶"]) expect(html).toContain(label);
    expect(html).toContain('aria-label="各维度的评级"');
  });

  it("总览有「国家重点领域与目标方向」：支持度、官方信号与出处、最契合的路线", () => {
    const html = render({ view: "home" });
    expect(html).toContain("国家重点领域与目标方向");
    for (const title of ["人工智能与大模型", "机器人", "无人机与低空经济", "卫星互联网与商业航天", "集成电路与半导体", "电子硬件与 PCB"]) expect(html).toContain(title);
    expect(html).toContain("国家支持度");
    expect(html).toContain("规划点名");
    expect(html).toContain("最契合的路线");
  });

  it("节点抽屉有「对应的国家重点领域」；按领域着色后卡片显示支撑等级", () => {
    let html = render({ view: "base", mapId: "electrical-engineering", nodeId: "polaris.ee.battery_bms" });
    expect(html).toContain("对应的国家重点领域");
    expect(html).toContain("新能源汽车");
    const button = [...container.querySelectorAll("button")].find((b) => b.textContent?.startsWith("新能源汽车") && b.getAttribute("aria-pressed") !== null)!;
    act(() => button.click());
    expect(container.querySelector('[data-node-id="polaris.ee.battery_bms"]')?.textContent).toContain("核心支撑");
    expect(container.querySelector('[data-node-id="polaris.ee.circuit_analysis"]')?.textContent).toContain("相关");
    act(() => useApp.getState().setRateBy(null));
    html = container.innerHTML;
    expect(container.querySelector('[data-node-id="polaris.ee.battery_bms"]')?.textContent).not.toContain("核心支撑");
  });

  it("路线评估面板列出对应的国家重点领域", () => {
    render({ view: "route", routeId: "route.satcom-leo" });
    const button = [...container.querySelectorAll("button")].find((b) => b.textContent?.includes("评估"))!;
    act(() => button.click());
    expect(container.innerHTML).toContain("对应的国家重点领域");
    expect(container.innerHTML).toContain("卫星互联网与商业航天");
  });

  it("总览单列「技术前景最好的方向」，每条路线带前景均值", () => {
    const html = render({ view: "home" });
    expect(html).toContain("技术前景最好的方向");
    expect(html).toContain("市场需求");
  });

  it("路线页有评估面板：六维评级、优劣与推荐的后续方向，可以点过去", () => {
    const route = catalog.routes.find((r) => r.id === "route.board-hardware")!;
    render({ view: "route", routeId: route.id });
    const button = [...container.querySelectorAll("button")].find((b) => b.textContent?.includes("评估"))!;
    act(() => button.click());
    const html = container.innerHTML;
    expect(html).toContain("路线评估");
    expect(html).toContain(route.assessment!.verdict_reason.slice(0, 12));
    expect(html).toContain("推荐的后续方向");
    expect(html).toContain("代价与局限");
    for (const next of route.assessment!.next) expect(html).toContain(catalog.routes.find((r) => r.id === next.route_id)!.title);
  });

  it("节点抽屉有评级区；选择着色维度后，卡片显示该维度的等级名", () => {
    const html = render({ view: "base", mapId: "electrical-engineering", nodeId: "polaris.ee.switching_converters" });
    expect(html).toContain("评级");
    expect(html).toContain("由内容推导");
    expect(html).toContain("编辑评估");
    const button = [...container.querySelectorAll("button")].find((b) => b.textContent === "实用性" && b.getAttribute("aria-pressed") !== null)!;
    act(() => button.click());
    // 仪器使用与板级调试的实用性是 5 级「日常必备」，卡片上要显示出来（不是只靠图例）。
    expect(container.querySelector('[data-node-id="polaris.ee.instruments_bringup"]')?.textContent).toContain("日常必备");
    act(() => useApp.getState().setRateBy(null));
    expect(container.querySelector('[data-node-id="polaris.ee.instruments_bringup"]')?.textContent).not.toContain("日常必备");
  });

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

  it("总览有通才阶梯入口与学习原则（每条原则带出处按钮）", () => {
    const html = render({ view: "home" });
    expect(html).toContain("先走这条，再选方向");
    for (const principle of catalog.principles) expect(html).toContain(principle.title);
    expect(html).toContain("个域");
  });

  it("路线视图有均衡度入口；打开面板能看到偏科提示与最常见的偏科", () => {
    const route = catalog.routes.find((r) => r.id === "route.digital-ic-verification")!;
    let html = render({ view: "route", routeId: route.id });
    expect(html).toContain("均衡度");
    const button = [...container.querySelectorAll("button")].find((b) => b.textContent?.includes("均衡度"))!;
    act(() => button.click());
    html = container.innerHTML;
    expect(html).toContain("这条路线没有碰到的域，建议补上");
    expect(html).toContain("这个方向最常见的偏科");
    for (const item of route.pitfalls!) expect(html).toContain(item.slice(0, 10));
  });

  it("通才阶梯的均衡度面板说明十二个域一个不缺", () => {
    render({ view: "route", routeId: "route.generalist-ladder" });
    const button = [...container.querySelectorAll("button")].find((b) => b.textContent?.includes("均衡度"))!;
    act(() => button.click());
    expect(container.innerHTML).toContain("一个不缺");
  });

  it("抽屉里显示节点所属的能力域", () => {
    const html = render({ view: "base", mapId: "frontier-depth", nodeId: "polaris.frontier.rtl_to_gds" });
    expect(html).toContain("数字逻辑与 HDL");
  });

  it("有岗位画像的路线会显示，并写明是时效性样本", () => {
    const html = render({ view: "route", routeId: "route.firmware-trusted" });
    expect(html).toContain("高端岗位的能力画像");
    expect(html).toContain("不构成录用承诺");
  });

  it("纵深节点的抽屉显示章节、每章的先修与出处；路线显示细化到多少章", () => {
    const html = render({ view: "base", mapId: "hw-sw-interface", nodeId: "polaris.codesign.interrupts" });
    expect(html).toContain("细分学习流程");
    expect(html).toContain("中断控制器、优先级与向量表");
    expect(html).toContain("先修：第");
    expect(html).toContain("NVIC");
    const route = render({ view: "route", routeId: "route.firmware-trusted" });
    expect(route).toContain("细化到");
    expect(route).toContain(" 章");
  });

  it("不存在的路线或参考层的图：给出说明而不是白屏", () => {
    expect(render({ view: "route", routeId: "route.nope" })).toContain("找不到这条路线");
    expect(render({ view: "base", mapId: "target-gnc" })).toContain("不对外开放");
  });
});
