// 函数图像视图（ADR 0028）：高等数学初级版的「动手试」画布。
//
// 一块画布、六种读法：同一条曲线，换一组辅助线就是不同的概念——
//   limit    左右两侧的点向 x₀ 夹拢（极限）
//   secant   割线绕定点转向切线（导数的定义）
//   slope    切线斜率沿曲线描出另一条曲线（导函数）
//   riemann  矩形越分越细（定积分）
//   accum    面积随 x 累积，下图画出累积函数（微积分基本定理）
//   plain    只有曲线与可拖的点（函数、连续）
// 数字全部由 calculus.ts 算出，画面和读数不会各说各话；换色走主题变量，
// 深色模式自动跟随。

import { fnById, riemannSum, exactIntegral, secantSlope, type Fn, type RiemannRule } from "./calculus";

export type FuncMode = "plain" | "limit" | "secant" | "slope" | "riemann" | "accum";

export interface FuncState {
  /** 关注点 x₀（riemann 模式里不用） */
  x0: number;
  /** 步长 h：limit 的夹拢距离 / secant 的第二点距离 */
  h: number;
  /** 黎曼和的等分数 */
  n: number;
  rule: RiemannRule;
  /** 积分/累积的下限 */
  a: number;
  /** 黎曼和的上限 */
  b: number;
}

export interface FuncConfig {
  fn: string;
  mode: FuncMode;
  xmin?: number;
  xmax?: number;
  state?: Partial<FuncState>;
}

export type Readout = Array<[label: string, value: string, alert?: boolean]>;

const W = 1360;
const H = 1020;
const PAD_L = 74;
const PAD_R = 40;

interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

const fmt = (v: number, d = 3): string =>
  Number.isFinite(v) ? String(+v.toFixed(d)) : "不存在";

export class FuncView {
  state: FuncState;
  fn: Fn;
  mode: FuncMode;
  private ctx: CanvasRenderingContext2D;
  private xmin: number;
  private xmax: number;
  private yMain: [number, number] = [-1, 1];
  private yLow: [number, number] = [-1, 1];
  private dragging = false;
  private anim = 0;
  onChange: (r: Readout, s: FuncState) => void = () => {};
  /** 使用者亲手拖动时回调，用来停掉讲解动画 */
  onUserEdit: () => void = () => {};

  constructor(private canvas: HTMLCanvasElement, cfg: FuncConfig) {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("画布不可用");
    this.ctx = ctx;
    this.fn = fnById(cfg.fn);
    this.mode = cfg.mode;
    this.xmin = cfg.xmin ?? -3;
    this.xmax = cfg.xmax ?? 3;
    this.state = { x0: 1, h: 1, n: 4, rule: "left", a: 0, b: 1, ...cfg.state };
    this.fitY();
    this.bind();
    this.draw();
  }

  // ── 对外 ───────────────────────────────────
  set(patch: Partial<FuncState>) {
    this.state = { ...this.state, ...patch };
    if (this.mode === "riemann" || this.mode === "accum") this.fitY();
    this.draw();
  }

  /** 换一个函数（白名单 id），纵轴随之重新适配 */
  setFn(id: string) {
    this.fn = fnById(id);
    this.fitY();
    this.draw();
  }

  /** 平滑过渡到目标状态（讲解动画用）。数值字段线性插值，rule 直接切换。 */
  animateTo(patch: Partial<FuncState>, ms = 1100): Promise<void> {
    cancelAnimationFrame(this.anim);
    const from = { ...this.state };
    const t0 = performance.now();
    return new Promise((resolve) => {
      const tick = (now: number) => {
        const u = Math.min(1, (now - t0) / ms);
        const e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
        const next = { ...this.state };
        for (const k of ["x0", "h", "n", "a", "b"] as const) {
          const to = patch[k];
          if (to !== undefined) next[k] = from[k] + (to - from[k]) * e;
        }
        if (patch.rule) next.rule = patch.rule;
        this.state = next;
        this.draw();
        if (u < 1) this.anim = requestAnimationFrame(tick);
        else resolve();
      };
      this.anim = requestAnimationFrame(tick);
    });
  }

  cancelAnimation() {
    cancelAnimationFrame(this.anim);
  }

  // ── 坐标 ───────────────────────────────────
  private mainRect(): Rect {
    const low = this.hasLower();
    return { x: PAD_L, y: 36, w: W - PAD_L - PAD_R, h: low ? 560 : 900 };
  }

  private lowRect(): Rect {
    return { x: PAD_L, y: 680, w: W - PAD_L - PAD_R, h: 280 };
  }

  private hasLower(): boolean {
    return this.mode === "slope" || this.mode === "accum";
  }

  private px(r: Rect, x: number): number {
    return r.x + ((x - this.xmin) / (this.xmax - this.xmin)) * r.w;
  }

  private py(r: Rect, y: number, [lo, hi]: [number, number]): number {
    return r.y + r.h - ((y - lo) / (hi - lo)) * r.h;
  }

  /** 按曲线实际取值定纵轴范围；陡峭的反例（1/x）截在 ±6 以内 */
  private fitY() {
    const range = (g: (x: number) => number): [number, number] => {
      let lo = 0;
      let hi = 0;
      for (let i = 0; i <= 400; i++) {
        const v = g(this.xmin + ((this.xmax - this.xmin) * i) / 400);
        if (Number.isFinite(v)) {
          lo = Math.min(lo, v);
          hi = Math.max(hi, v);
        }
      }
      lo = Math.max(lo, -6);
      hi = Math.min(hi, 6);
      const pad = Math.max(0.4, (hi - lo) * 0.12);
      return [lo - pad, hi + pad];
    };
    this.yMain = range(this.fn.f);
    if (this.mode === "slope") this.yLow = range(this.fn.df);
    if (this.mode === "accum" && this.fn.F) {
      const F = this.fn.F;
      const base = F(this.state.a);
      this.yLow = range((x) => F(x) - base);
    }
  }

  // ── 交互 ───────────────────────────────────
  private bind() {
    const at = (e: PointerEvent): number => {
      const box = this.canvas.getBoundingClientRect();
      const cx = ((e.clientX - box.left) / box.width) * W;
      const r = this.mainRect();
      return this.xmin + ((cx - r.x) / r.w) * (this.xmax - this.xmin);
    };
    const move = (e: PointerEvent) => {
      if (!this.dragging) return;
      const x = Math.min(this.xmax - 0.05, Math.max(this.xmin + 0.05, at(e)));
      // 四舍五入到 0.05：拖动时读数不会满屏小数，也方便恰好落在整数点上
      this.set({ x0: Math.round(x * 20) / 20 });
      this.onUserEdit();
    };
    this.canvas.addEventListener("pointerdown", (e) => {
      if (this.mode === "riemann") return;
      this.dragging = true;
      this.canvas.setPointerCapture(e.pointerId);
      move(e);
    });
    this.canvas.addEventListener("pointermove", move);
    const up = () => (this.dragging = false);
    this.canvas.addEventListener("pointerup", up);
    this.canvas.addEventListener("pointercancel", up);
  }

  // ── 绘制 ───────────────────────────────────
  private css(name: string): string {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  draw() {
    const { ctx } = this;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = this.css("--bg");
    ctx.fillRect(0, 0, W, H);

    const m = this.mainRect();
    this.axes(m, this.yMain);
    const rows: Readout = [];

    if (this.mode === "riemann") this.drawRiemann(m, rows);
    if (this.mode === "accum") this.drawAccumArea(m);
    this.curve(m, this.yMain, this.fn.f, this.css("--accent"), 5);
    this.marks(m);

    if (this.mode === "limit") this.drawLimit(m, rows);
    else if (this.mode === "secant") this.drawSecant(m, rows);
    else if (this.mode === "slope") this.drawTangent(m, rows);
    else if (this.mode === "accum") this.accumRows(rows);
    else if (this.mode === "plain") this.drawPlain(m, rows);

    if (this.hasLower()) this.drawLower();
    this.onChange(rows, this.state);
  }

  private axes(r: Rect, [lo, hi]: [number, number]) {
    const { ctx } = this;
    ctx.save();
    ctx.lineWidth = 1;
    ctx.strokeStyle = this.css("--grid");
    ctx.fillStyle = this.css("--muted");
    ctx.font = "22px system-ui, sans-serif";
    ctx.textAlign = "center";
    for (let x = Math.ceil(this.xmin); x <= this.xmax; x++) {
      const X = this.px(r, x);
      ctx.beginPath();
      ctx.moveTo(X, r.y);
      ctx.lineTo(X, r.y + r.h);
      ctx.stroke();
      if (x !== 0) ctx.fillText(String(x), X, Math.min(r.y + r.h - 6, this.py(r, 0, [lo, hi]) + 26));
    }
    ctx.textAlign = "right";
    for (let y = Math.ceil(lo); y <= hi; y++) {
      const Y = this.py(r, y, [lo, hi]);
      ctx.beginPath();
      ctx.moveTo(r.x, Y);
      ctx.lineTo(r.x + r.w, Y);
      ctx.stroke();
      if (y !== 0) ctx.fillText(String(y), this.px(r, 0) - 8, Y + 7);
    }
    ctx.strokeStyle = this.css("--ink");
    ctx.lineWidth = 2;
    const Y0 = this.py(r, 0, [lo, hi]);
    const X0 = this.px(r, 0);
    ctx.beginPath();
    ctx.moveTo(r.x, Y0);
    ctx.lineTo(r.x + r.w, Y0);
    ctx.moveTo(X0, r.y);
    ctx.lineTo(X0, r.y + r.h);
    ctx.stroke();
    ctx.restore();
  }

  private curve(
    r: Rect,
    yr: [number, number],
    g: (x: number) => number,
    color: string,
    width: number,
  ) {
    const { ctx } = this;
    ctx.save();
    ctx.beginPath();
    ctx.rect(r.x, r.y, r.w, r.h);
    ctx.clip();
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineJoin = "round";
    const N = 900;
    const jump = (yr[1] - yr[0]) * 0.5;
    let pen = false;
    let prev = NaN;
    ctx.beginPath();
    for (let i = 0; i <= N; i++) {
      const x = this.xmin + ((this.xmax - this.xmin) * i) / N;
      const y = g(x);
      // 断开：没有定义，或相邻两点跳得比半个画面还高（跳变、1/x 过零）
      if (!Number.isFinite(y) || (pen && Math.abs(y - prev) > jump)) {
        pen = false;
        prev = Number.isFinite(y) ? y : NaN;
        if (Number.isFinite(y)) {
          ctx.moveTo(this.px(r, x), this.py(r, y, yr));
          pen = true;
        }
        continue;
      }
      const X = this.px(r, x);
      const Y = this.py(r, y, yr);
      if (!pen) ctx.moveTo(X, Y);
      else ctx.lineTo(X, Y);
      pen = true;
      prev = y;
    }
    ctx.stroke();
    ctx.restore();
  }

  /** 空心圈与孤立点：它们是「图像上缺了什么」的视觉证据 */
  private marks(r: Rect) {
    const { ctx } = this;
    for (const [x, y] of this.fn.holes ?? []) {
      ctx.beginPath();
      ctx.arc(this.px(r, x), this.py(r, y, this.yMain), 9, 0, Math.PI * 2);
      ctx.fillStyle = this.css("--bg");
      ctx.fill();
      ctx.lineWidth = 4;
      ctx.strokeStyle = this.css("--accent");
      ctx.stroke();
    }
    for (const [x, y] of this.fn.dots ?? []) this.dot(r, this.yMain, x, y, this.css("--accent"), 9);
  }

  private dot(r: Rect, yr: [number, number], x: number, y: number, color: string, rad = 11) {
    if (!Number.isFinite(y)) return;
    const { ctx } = this;
    ctx.beginPath();
    ctx.arc(this.px(r, x), this.py(r, y, yr), rad, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.lineWidth = 3;
    ctx.strokeStyle = this.css("--bg");
    ctx.stroke();
  }

  private label(text: string, x: number, y: number, color: string, align: CanvasTextAlign = "left") {
    const { ctx } = this;
    ctx.save();
    ctx.font = "600 25px system-ui, sans-serif";
    ctx.textAlign = align;
    ctx.lineWidth = 6;
    ctx.strokeStyle = this.css("--bg");
    ctx.strokeText(text, x, y);
    ctx.fillStyle = color;
    ctx.fillText(text, x, y);
    ctx.restore();
  }

  private line(r: Rect, yr: [number, number], x1: number, y1: number, slope: number, color: string, dash: number[] = []) {
    const { ctx } = this;
    const xa = this.xmin;
    const xb = this.xmax;
    ctx.save();
    ctx.beginPath();
    ctx.rect(r.x, r.y, r.w, r.h);
    ctx.clip();
    ctx.setLineDash(dash);
    ctx.lineWidth = 4;
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(this.px(r, xa), this.py(r, y1 + slope * (xa - x1), yr));
    ctx.lineTo(this.px(r, xb), this.py(r, y1 + slope * (xb - x1), yr));
    ctx.stroke();
    ctx.restore();
  }

  private vline(r: Rect, x: number, color: string, dash: number[] = [8, 8]) {
    const { ctx } = this;
    ctx.save();
    ctx.setLineDash(dash);
    ctx.lineWidth = 2;
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(this.px(r, x), r.y);
    ctx.lineTo(this.px(r, x), r.y + r.h);
    ctx.stroke();
    ctx.restore();
  }

  private hline(r: Rect, yr: [number, number], y: number, x1: number, x2: number, color: string) {
    const { ctx } = this;
    ctx.save();
    ctx.setLineDash([8, 8]);
    ctx.lineWidth = 2;
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(this.px(r, x1), this.py(r, y, yr));
    ctx.lineTo(this.px(r, x2), this.py(r, y, yr));
    ctx.stroke();
    ctx.restore();
  }

  // ── plain：看图读值 ─────────────────────────
  private drawPlain(r: Rect, rows: Readout) {
    const { x0 } = this.state;
    const y = this.fn.f(x0);
    this.vline(r, x0, this.css("--muted"));
    if (Number.isFinite(y)) {
      this.hline(r, this.yMain, y, this.xmin, x0, this.css("--muted"));
      this.dot(r, this.yMain, x0, y, this.css("--basis-j"));
    }
    rows.push(["x", fmt(x0, 2)]);
    rows.push(["f(x)", Number.isFinite(y) ? fmt(y) : "没有定义", !Number.isFinite(y)]);
  }

  // ── limit：从两侧夹拢 ───────────────────────
  private drawLimit(r: Rect, rows: Readout) {
    const { x0, h } = this.state;
    const yl = this.fn.f(x0 - h);
    const yr = this.fn.f(x0 + h);
    const { ctx } = this;
    ctx.save();
    ctx.fillStyle = this.css("--grid");
    ctx.globalAlpha = 0.5;
    ctx.fillRect(this.px(r, x0 - h), r.y, this.px(r, x0 + h) - this.px(r, x0 - h), r.h);
    ctx.restore();
    this.vline(r, x0, this.css("--muted"));
    const cl = this.css("--basis-i");
    const cr = this.css("--basis-j");
    if (Number.isFinite(yl)) {
      this.hline(r, this.yMain, yl, this.xmin, x0 - h, cl);
      this.dot(r, this.yMain, x0 - h, yl, cl);
    }
    if (Number.isFinite(yr)) {
      this.hline(r, this.yMain, yr, x0 + h, this.xmax, cr);
      this.dot(r, this.yMain, x0 + h, yr, cr);
    }
    rows.push(["x₀", fmt(x0, 2)]);
    rows.push(["距离 h", fmt(h, 3)]);
    rows.push(["左边 f(x₀−h)", fmt(yl)]);
    rows.push(["右边 f(x₀+h)", fmt(yr)]);
    const close = Number.isFinite(yl) && Number.isFinite(yr) && Math.abs(yl - yr) < 0.05;
    rows.push(["左右夹到一起了吗", close ? "是" : "还没有", !close]);
  }

  // ── secant：割线转成切线 ────────────────────
  private drawSecant(r: Rect, rows: Readout) {
    const { x0, h } = this.state;
    const y0 = this.fn.f(x0);
    const y1 = this.fn.f(x0 + h);
    const slope = secantSlope(this.fn, x0, h);
    const tan = this.fn.df(x0);
    if (Number.isFinite(tan) && Number.isFinite(y0)) {
      this.line(r, this.yMain, x0, y0, tan, this.css("--eigen"), [14, 10]);
    }
    if (Number.isFinite(slope)) this.line(r, this.yMain, x0, y0, slope, this.css("--basis-j"));
    this.dot(r, this.yMain, x0, y0, this.css("--ink"));
    this.dot(r, this.yMain, x0 + h, y1, this.css("--basis-j"));
    rows.push(["x₀", fmt(x0, 2)]);
    rows.push(["h", fmt(h, 3)]);
    rows.push(["割线斜率（橙）", fmt(slope, 4)]);
    rows.push(["切线斜率（绿虚线）", fmt(tan, 4), !Number.isFinite(tan)]);
  }

  // ── slope：切线与导函数 ─────────────────────
  private drawTangent(r: Rect, rows: Readout) {
    const { x0 } = this.state;
    const y0 = this.fn.f(x0);
    const d = this.fn.df(x0);
    if (Number.isFinite(d) && Number.isFinite(y0)) {
      this.line(r, this.yMain, x0, y0, d, this.css("--basis-j"));
    }
    this.vline(r, x0, this.css("--muted"));
    this.dot(r, this.yMain, x0, y0, this.css("--ink"));
    rows.push(["x", fmt(x0, 2)]);
    rows.push(["f(x)", fmt(y0)]);
    rows.push(["切线斜率 f′(x)", Number.isFinite(d) ? fmt(d, 4) : "不可导", !Number.isFinite(d)]);
  }

  // ── riemann：矩形 ───────────────────────────
  private drawRiemann(r: Rect, rows: Readout) {
    const { a, b, rule } = this.state;
    const n = Math.max(1, Math.round(this.state.n));
    const dx = (b - a) / n;
    const { ctx } = this;
    ctx.save();
    ctx.beginPath();
    ctx.rect(r.x, r.y, r.w, r.h);
    ctx.clip();
    for (let i = 0; i < n; i++) {
      const x = rule === "left" ? a + i * dx : rule === "right" ? a + (i + 1) * dx : a + (i + 0.5) * dx;
      const y = this.fn.f(x);
      if (!Number.isFinite(y)) continue;
      const X1 = this.px(r, a + i * dx);
      const X2 = this.px(r, a + (i + 1) * dx);
      const Y0 = this.py(r, 0, this.yMain);
      const Y1 = this.py(r, y, this.yMain);
      ctx.globalAlpha = 0.28;
      ctx.fillStyle = this.css("--basis-i");
      ctx.fillRect(X1, Math.min(Y0, Y1), X2 - X1, Math.abs(Y1 - Y0));
      ctx.globalAlpha = 1;
      ctx.lineWidth = n > 40 ? 1 : 3;
      ctx.strokeStyle = this.css("--basis-i");
      ctx.strokeRect(X1, Math.min(Y0, Y1), X2 - X1, Math.abs(Y1 - Y0));
    }
    ctx.restore();
    this.vline(r, a, this.css("--muted"), [4, 6]);
    this.vline(r, b, this.css("--muted"), [4, 6]);
    const s = riemannSum(this.fn, a, b, n, rule);
    const exact = exactIntegral(this.fn, a, b);
    rows.push(["区间", `[${fmt(a, 2)}, ${fmt(b, 2)}]`]);
    rows.push(["分成几份", String(n)]);
    rows.push(["矩形面积之和", fmt(s, 4)]);
    if (Number.isFinite(exact)) {
      rows.push(["真正的面积", fmt(exact, 4)]);
      rows.push(["差多少", fmt(s - exact, 4)]);
    }
  }

  // ── accum：累积面积 ─────────────────────────
  private drawAccumArea(r: Rect) {
    const { a, x0 } = this.state;
    const N = 160;
    const { ctx } = this;
    ctx.save();
    ctx.beginPath();
    ctx.rect(r.x, r.y, r.w, r.h);
    ctx.clip();
    ctx.globalAlpha = 0.28;
    ctx.fillStyle = this.css("--basis-i");
    ctx.beginPath();
    const Y0 = this.py(r, 0, this.yMain);
    ctx.moveTo(this.px(r, a), Y0);
    for (let i = 0; i <= N; i++) {
      const x = a + ((x0 - a) * i) / N;
      const y = this.fn.f(x);
      ctx.lineTo(this.px(r, x), Number.isFinite(y) ? this.py(r, y, this.yMain) : Y0);
    }
    ctx.lineTo(this.px(r, x0), Y0);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
    this.vline(r, a, this.css("--muted"), [4, 6]);
    this.vline(r, x0, this.css("--basis-j"));
    this.dot(r, this.yMain, x0, this.fn.f(x0), this.css("--basis-j"));
  }

  private accumRows(rows: Readout) {
    const { a, x0 } = this.state;
    const area = exactIntegral(this.fn, a, x0);
    rows.push(["从 a 到 x 的面积", fmt(area, 4)]);
    rows.push(["x 处的高度 f(x)", fmt(this.fn.f(x0), 4)]);
  }

  // ── 下图：导函数 / 累积函数 ──────────────────
  private drawLower() {
    const r = this.lowRect();
    const { ctx } = this;
    this.axes(r, this.yLow);
    const x0 = this.state.x0;
    if (this.mode === "slope") {
      this.curve(r, this.yLow, this.fn.df, this.css("--basis-j"), 5);
      this.vline(r, x0, this.css("--muted"));
      this.dot(r, this.yLow, x0, this.fn.df(x0), this.css("--basis-j"));
      this.label("f′(x)：每一点切线的斜率", r.x + 10, r.y + 30, this.css("--basis-j"));
    } else if (this.fn.F) {
      const F = this.fn.F;
      const base = F(this.state.a);
      const g = (x: number) => F(x) - base;
      this.curve(r, this.yLow, g, this.css("--basis-i"), 5);
      this.vline(r, x0, this.css("--muted"));
      this.dot(r, this.yLow, x0, g(x0), this.css("--basis-i"));
      this.label("累积面积 A(x)：从 a 积到 x", r.x + 10, r.y + 30, this.css("--basis-i"));
    }
    ctx.save();
    ctx.strokeStyle = this.css("--line");
    ctx.lineWidth = 1;
    ctx.strokeRect(r.x, r.y, r.w, r.h);
    ctx.restore();
  }
}
