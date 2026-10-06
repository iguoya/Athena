import { describe, expect, it } from "vitest";
import { MAX_K, MIN_K, centerOn, ensureVisible, fitViewport, fitWidthViewport, zoomAt } from "./viewport";

describe("视口数学", () => {
  it("缩放以光标为不动点：光标下的内容点缩放前后屏幕位置不变", () => {
    const view = { x: 40, y: -20, k: 0.8 };
    const [cx, cy] = [300, 220];
    const contentPoint = { x: (cx - view.x) / view.k, y: (cy - view.y) / view.k };
    const next = zoomAt(view, 1.25, cx, cy);
    expect(next.x + contentPoint.x * next.k).toBeCloseTo(cx);
    expect(next.y + contentPoint.y * next.k).toBeCloseTo(cy);
  });

  it("缩放被夹在 [MIN_K, MAX_K]，到头后不再平移", () => {
    let view = { x: 0, y: 0, k: 1 };
    for (let i = 0; i < 50; i++) view = zoomAt(view, 1.5, 100, 100);
    expect(view.k).toBe(MAX_K);
    const atMax = zoomAt(view, 1.5, 100, 100);
    expect(atMax).toEqual(view);
    for (let i = 0; i < 100; i++) view = zoomAt(view, 0.5, 100, 100);
    expect(view.k).toBe(MIN_K);
  });

  it("适配：大图缩小到完整可见并居中，小图不被放大超过 maxK", () => {
    const big = fitViewport({ w: 2000, h: 1500 }, { w: 1000, h: 700 });
    expect(big.k).toBeLessThan(1);
    expect(2000 * big.k).toBeLessThanOrEqual(1000);
    expect(1500 * big.k).toBeLessThanOrEqual(700);
    expect(big.x).toBeCloseTo((1000 - 2000 * big.k) / 2);
    const small = fitViewport({ w: 300, h: 200 }, { w: 1000, h: 700 });
    expect(small.k).toBe(1);
  });

  it("居中：选中的点出现在「去掉抽屉后」的可见区域中心", () => {
    const view = centerOn({ x: 0, y: 0, k: 0.5 }, { x: 800, y: 400 }, { w: 1200, h: 800 }, 400);
    expect(800 * 0.5 + view.x).toBeCloseTo((1200 - 400) / 2);
    expect(400 * 0.5 + view.y).toBeCloseTo(400);
  });

  it("按宽度适配：宽度刚好放进视口、从顶部开始，高图不被缩小", () => {
    const view = fitWidthViewport({ w: 1200, h: 3000 }, { w: 1000, h: 700 }, 24);
    expect(1200 * view.k).toBeLessThanOrEqual(1000 - 48 + 1e-9);
    expect(view.y).toBe(24);
    // 窄图不放大超过 1
    expect(fitWidthViewport({ w: 400, h: 300 }, { w: 1000, h: 700 }).k).toBe(1);
  });

  it("保证可见：已在可见区内不动，在抽屉下面或视口外才居中", () => {
    const size = { w: 1200, h: 800 };
    const home = { x: 0, y: 0, k: 1 };
    const inside = { x: 200, y: 200, w: 264, h: 104 };
    expect(ensureVisible(home, inside, size, 400)).toBe(home);
    // 被 400px 宽的抽屉盖住（屏幕上 x 在 [800,1200]）
    const covered = { x: 900, y: 200, w: 264, h: 104 };
    const moved = ensureVisible(home, covered, size, 400);
    expect((covered.x + covered.w / 2) * moved.k + moved.x).toBeCloseTo((1200 - 400) / 2);
    // 视口外
    const far = { x: 200, y: 2000, w: 264, h: 104 };
    expect(ensureVisible(home, far, size, 0).y).not.toBe(0);
  });
});
