// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";

// 冒烟测试只验证 2D 界面（面板、图表、读数）的装配：Canvas mock 成空 div，
// 场景子树不挂载——happy-dom 没有 WebGL 上下文，3D 场景的正确性由类型检查
// 与人工打开验证，数据数值的正确性由 catalog.test.ts 把关。
vi.mock("@react-three/fiber", () => ({
  Canvas: () => <div data-testid="earth-canvas-stub" />,
}));

import { App } from "./App";

beforeAll(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
});

let container: HTMLElement | null = null;
let root: Root | null = null;

function renderApp() {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(<App />);
  });
}

afterEach(() => {
  const currentRoot = root;
  const currentContainer = container;
  if (currentRoot && currentContainer) {
    act(() => currentRoot.unmount());
    currentContainer.remove();
  }
  root = null;
  container = null;
});

describe("App 装配", () => {
  it("标题与真实比例徽章在位", () => {
    renderApp();
    expect(document.body.textContent).toContain("地球 · 真实比例分层");
    expect(document.body.textContent).toContain("真实比例 · 垂直方向未放大");
  });

  it("五层大气与六层内部结构都列在面板里", () => {
    renderApp();
    for (const name of ["对流层", "平流层", "中间层", "热层", "外逸层"]) {
      expect(document.body.textContent).toContain(name);
    }
    for (const name of ["地壳", "上地幔", "过渡带", "下地幔", "外核", "内核"]) {
      expect(document.body.textContent).toContain(name);
    }
  });

  it("剖面开关与标注开关存在，Canvas 桩被挂载", () => {
    renderApp();
    expect(document.body.textContent).toContain("四分之一剖面");
    expect(screenHas("标注"));
    expect(document.querySelector('[data-testid="earth-canvas-stub"]')).not.toBeNull();
  });

  it("探针默认在内部模式，读数显示地表密度 2.72 g/cm³", () => {
    renderApp();
    expect(document.body.textContent).toContain("向内（深度）");
    expect(document.body.textContent).toContain("深度 0 km");
    expect(document.body.textContent).toContain("2.72");
  });
});

function screenHas(text: string): boolean {
  return document.body.textContent!.includes(text);
}
