// 高等数学初级版的函数库与数值工具（ADR 0028）。
//
// 只收一张白名单里的函数：每个都带解析导数 df 与原函数 F，画面上的割线斜率、
// 黎曼和、累积面积都由这里算出来，而不是手写的数字。白名单而不是让使用者
// 输入任意表达式，是因为初级版要的是「每个函数都是为某个概念挑的反例或典型」，
// 不是计算器；任意输入留给中高级版（经符号引擎）。

export interface Fn {
  id: string;
  /** 界面上显示的解析式 */
  label: string;
  f: (x: number) => number;
  /** 解析导数；在不可导点返回 NaN */
  df: (x: number) => number;
  /** 一个原函数（积分常数取 0）；没有闭式时省略 */
  F?: (x: number) => number;
  /** 画成空心圈的点：函数在那里没有定义，或取值不是图像走向的那个值 */
  holes?: Array<[number, number]>;
  /** 画成实心点的孤立点（跳变点上真正取到的那个值） */
  dots?: Array<[number, number]>;
}

export const FUNCTIONS: Fn[] = [
  { id: "lin", label: "f(x) = 0.5x + 1", f: (x) => 0.5 * x + 1, df: () => 0.5, F: (x) => 0.25 * x * x + x },
  { id: "x2", label: "f(x) = x²", f: (x) => x * x, df: (x) => 2 * x, F: (x) => (x * x * x) / 3 },
  { id: "x3", label: "f(x) = x³", f: (x) => x * x * x, df: (x) => 3 * x * x, F: (x) => (x * x * x * x) / 4 },
  {
    id: "x3m3x",
    label: "f(x) = x³ − 3x",
    f: (x) => x * x * x - 3 * x,
    df: (x) => 3 * x * x - 3,
    F: (x) => (x * x * x * x) / 4 - (3 * x * x) / 2,
  },
  {
    id: "abs",
    label: "f(x) = |x|",
    f: (x) => Math.abs(x),
    df: (x) => (x === 0 ? NaN : x > 0 ? 1 : -1),
    F: (x) => (x * Math.abs(x)) / 2,
  },
  { id: "sin", label: "f(x) = sin x", f: (x) => Math.sin(x), df: (x) => Math.cos(x), F: (x) => -Math.cos(x) },
  { id: "exp", label: "f(x) = eˣ", f: (x) => Math.exp(x), df: (x) => Math.exp(x), F: (x) => Math.exp(x) },
  {
    id: "sqrt",
    label: "f(x) = √x",
    f: (x) => (x < 0 ? NaN : Math.sqrt(x)),
    df: (x) => (x <= 0 ? NaN : 0.5 / Math.sqrt(x)),
    F: (x) => (x < 0 ? NaN : (2 / 3) * x * Math.sqrt(x)),
  },
  // 下面几个是「极限存在与函数值无关」「左右不等」「趋向无穷」的反例，各服务一个概念。
  {
    id: "removable",
    label: "f(x) = (x² − 1)/(x − 1)",
    f: (x) => (x === 1 ? NaN : (x * x - 1) / (x - 1)),
    df: () => 1,
    holes: [[1, 2]],
  },
  {
    id: "step",
    label: "f(x) = −1（x<0），1（x≥0）",
    f: (x) => (x < 0 ? -1 : 1),
    df: (x) => (x === 0 ? NaN : 0),
    holes: [[0, -1]],
    dots: [[0, 1]],
  },
  { id: "inv", label: "f(x) = 1/x", f: (x) => (x === 0 ? NaN : 1 / x), df: (x) => (x === 0 ? NaN : -1 / (x * x)) },
  {
    id: "hill",
    label: "f(x) = 2 − (x − 1)²/2 的一段",
    f: (x) => 2 - ((x - 1) * (x - 1)) / 2,
    df: (x) => -(x - 1),
    F: (x) => 2 * x - (x - 1) ** 3 / 6,
  },
];

const BY_ID = new Map(FUNCTIONS.map((fn) => [fn.id, fn]));

export function fnById(id: string): Fn {
  const fn = BY_ID.get(id);
  if (!fn) throw new Error(`未知函数：${id}`);
  return fn;
}

/** 过 (x0, f(x0)) 与 (x0+h, f(x0+h)) 的割线斜率；两点之一无定义时返回 NaN */
export function secantSlope(fn: Fn, x0: number, h: number): number {
  const a = fn.f(x0);
  const b = fn.f(x0 + h);
  if (h === 0 || !Number.isFinite(a) || !Number.isFinite(b)) return NaN;
  return (b - a) / h;
}

export type RiemannRule = "left" | "right" | "mid";

/** 把 [a,b] 分成 n 等份的黎曼和 */
export function riemannSum(fn: Fn, a: number, b: number, n: number, rule: RiemannRule = "left"): number {
  const dx = (b - a) / n;
  let s = 0;
  for (let i = 0; i < n; i++) {
    const x = rule === "left" ? a + i * dx : rule === "right" ? a + (i + 1) * dx : a + (i + 0.5) * dx;
    s += fn.f(x) * dx;
  }
  return s;
}

/** 用牛顿—莱布尼茨公式算的精确定积分；没有原函数时返回 NaN */
export function exactIntegral(fn: Fn, a: number, b: number): number {
  return fn.F ? fn.F(b) - fn.F(a) : NaN;
}

/** 在 x0 的左右各取一点看函数值，用来给「极限」一节的读数 */
export function sideValues(fn: Fn, x0: number, h: number): { left: number; right: number } {
  return { left: fn.f(x0 - h), right: fn.f(x0 + h) };
}
