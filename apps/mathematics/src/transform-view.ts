// 二维线性变换画布。
// 用代码而非声明式模板构建，因为它是 Canvas 自绘（主仓库 GTK 规则 3 的 Web 对应）。
// 只暴露「拖两个基向量」这一个自由度，其余收起（ADR 0011 第 6 节）。

export interface Mat2 {
  a: number;
  b: number;
  c: number;
  d: number;
}

export interface Readout {
  det: number;
  flipped: boolean;
  rank: 0 | 1 | 2;
  /** 实特征方向的单位向量；旋转类变换没有实特征方向，返回空数组 */
  eigenDirs: Array<[number, number]>;
}

const EPS = 1e-9;

export function readoutOf(m: Mat2): Readout {
  const { a, b, c, d } = m;
  const det = a * d - b * c;
  const zero =
    Math.abs(a) < EPS && Math.abs(b) < EPS && Math.abs(c) < EPS && Math.abs(d) < EPS;
  const rank: 0 | 1 | 2 = zero ? 0 : Math.abs(det) < EPS ? 1 : 2;

  const eigenDirs: Array<[number, number]> = [];
  const tr = a + d;
  const disc = tr * tr - 4 * det;
  if (disc >= -EPS && rank === 2) {
    const s = Math.sqrt(Math.max(disc, 0));
    for (const lam of [(tr + s) / 2, (tr - s) / 2]) {
      let vx: number, vy: number;
      if (Math.abs(b) > EPS) {
        vx = b;
        vy = lam - a;
      } else if (Math.abs(c) > EPS) {
        vx = lam - d;
        vy = c;
      } else {
        const isFirst = Math.abs(lam - a) < EPS;
        vx = isFirst ? 1 : 0;
        vy = isFirst ? 0 : 1;
      }
      const n = Math.hypot(vx, vy);
      if (n > EPS) eigenDirs.push([vx / n, vy / n]);
    }
  }
  return { det, flipped: det < -EPS, rank, eigenDirs };
}

export interface TransformViewOptions {
  /** 第一章先不画特征方向，避免还没讲的绿虚线抢视线 */
  showEigen?: boolean;
  /**
   * 解方程组那一节用：画一个可拖的目标点 b，并把「沿蓝箭头走几步、
   * 再沿橙箭头走几步才能到它」这条路径画出来。Ax = b 的三种情形
   * （唯一解 / 无解 / 无穷多解）因此变成看得见的事。
   */
  target?: [number, number];
}

/** 到达目标点的走法：x 步蓝箭头 + y 步橙箭头 */
export type Reach =
  | { kind: "one"; x: number; y: number }
  | { kind: "none" }
  | { kind: "many"; x: number; y: number; dirX: number; dirY: number };

export class TransformView {
  private ctx: CanvasRenderingContext2D;
  private m: Mat2 = { a: 1, b: 0, c: 0, d: 1 };
  private dragging: "i" | "j" | "t" | "pan" | null = null;
  /** 平移起点：[鼠标 clientX, clientY, 起始 panX, 起始 panY] */
  private panFrom: [number, number, number, number] = [0, 0, 0, 0];
  private target: [number, number] | null = null;
  private animToken = 0;
  /** 每格像素。缩放会改它，所以不能是 readonly */
  private S: number;
  private readonly baseS: number;
  private readonly ox: number;
  private readonly oy: number;
  /** 拖空白处平移视图用的偏移 */
  private panX = 0;
  private panY = 0;
  private zoom = 1;

  constructor(
    private canvas: HTMLCanvasElement,
    private onChange: (m: Mat2, r: Readout) => void,
    private options: TransformViewOptions = {},
  ) {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("画布不可用");
    this.ctx = ctx;
    // 一格大约占画布短边的 1/6.5，箭头和线头跟着格子走，避免缩成针尖
    this.baseS = Math.min(canvas.width, canvas.height) / 6.5;
    this.S = this.baseS;
    this.ox = canvas.width / 2;
    this.oy = canvas.height / 2;
    this.target = options.target ?? null;
    this.bindDrag();
    // 目标点可能落在默认视野之外——那是最该看的东西，先缩到看得见
    if (this.target) this.fitPoints([this.target]);
  }

  /** 解 Ax = b：两根箭头各走几步能到 b */
  reach(): Reach | null {
    if (!this.target) return null;
    const { a, b, c, d } = this.m;
    const [bx, by] = this.target;
    const det = a * d - b * c;
    if (Math.abs(det) > EPS) {
      // 可逆：走法唯一
      return { kind: "one", x: (d * bx - b * by) / det, y: (-c * bx + a * by) / det };
    }
    // 压扁了：两根箭头共线。目标点在那条线上才够得着，且走法有无穷多种
    const cx = Math.abs(a) > EPS || Math.abs(c) > EPS ? [a, c] : [b, d];
    if (Math.abs(cx[0]) < EPS && Math.abs(cx[1]) < EPS) {
      // 两根箭头都塌到原点，只有 b 也在原点才够得着
      return Math.hypot(bx, by) < EPS
        ? { kind: "many", x: 0, y: 0, dirX: 1, dirY: 0 }
        : { kind: "none" };
    }
    // b 是否与列方向共线
    if (Math.abs(cx[0] * by - cx[1] * bx) > 1e-6) return { kind: "none" };
    // 找一组特解；零空间方向是 (b, -a) 或 (d, -c)
    let x = 0;
    let y = 0;
    if (Math.abs(a) > EPS || Math.abs(c) > EPS) {
      const t = Math.abs(a) > EPS ? bx / a : by / c;
      x = t;
    } else {
      const t = Math.abs(b) > EPS ? bx / b : by / d;
      y = t;
    }
    const nx = b;
    const ny = -a;
    const n = Math.hypot(nx, ny);
    return n > EPS
      ? { kind: "many", x, y, dirX: nx / n, dirY: ny / n }
      : { kind: "many", x, y, dirX: d, dirY: -c };
  }

  /** 当前缩放倍率（1 = 每格约占画布高度的十一分之一） */
  get zoomLevel(): number {
    return this.zoom;
  }

  resetView() {
    this.panX = 0;
    this.panY = 0;
    this.zoom = 1;
    this.S = this.baseS;
    this.draw();
  }

  setZoom(z: number) {
    this.zoom = Math.min(4, Math.max(0.18, z));
    this.S = this.baseS * this.zoom;
    this.draw();
  }

  /**
   * 自动缩到能看见这些点为止。目标点落在画布外是很隐蔽的坑——
   * 图看着一切正常，只是那个最该看的点不在画面里。
   */
  fitPoints(pts: Array<[number, number]>, margin = 1.25) {
    this.panX = 0;
    this.panY = 0;
    const all = [...pts, [this.m.a, this.m.c], [this.m.b, this.m.d], [0, 0]] as Array<
      [number, number]
    >;
    const maxX = Math.max(...all.map(([x]) => Math.abs(x)), 1);
    const maxY = Math.max(...all.map(([, y]) => Math.abs(y)), 1);
    const needX = this.ox / (maxX * margin);
    const needY = this.oy / (maxY * margin);
    this.setZoom(Math.min(needX, needY) / this.baseS);
  }

  setTarget(t: [number, number] | null) {
    this.target = t;
    this.draw();
  }

  get matrix(): Mat2 {
    return { ...this.m };
  }

  set(m: Mat2) {
    this.animToken += 1;
    this.m = { ...m };
    this.draw();
  }

  /** 把当前矩阵平滑搬到目标。离开页面或再次 set 会取消。 */
  animateTo(target: Mat2, ms = 1100): Promise<void> {
    const token = ++this.animToken;
    const from = { ...this.m };
    return new Promise((resolve) => {
      const t0 = performance.now();
      const tick = (now: number) => {
        if (token !== this.animToken) {
          resolve();
          return;
        }
        const u = Math.min(1, (now - t0) / ms);
        const e = 1 - (1 - u) ** 3;
        this.m = {
          a: from.a + (target.a - from.a) * e,
          b: from.b + (target.b - from.b) * e,
          c: from.c + (target.c - from.c) * e,
          d: from.d + (target.d - from.d) * e,
        };
        this.draw();
        if (u < 1) requestAnimationFrame(tick);
        else resolve();
      };
      requestAnimationFrame(tick);
    });
  }

  cancelAnimation() {
    this.animToken += 1;
  }

  private css(name: string): string {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  private toPx(x: number, y: number): [number, number] {
    return [this.ox + this.panX + x * this.S, this.oy + this.panY - y * this.S];
  }

  private toMath(px: number, py: number): [number, number] {
    return [(px - this.ox - this.panX) / this.S, (this.oy + this.panY - py) / this.S];
  }

  private eventPoint(ev: PointerEvent): [number, number] {
    const r = this.canvas.getBoundingClientRect();
    const px = (ev.clientX - r.left) * (this.canvas.width / r.width);
    const py = (ev.clientY - r.top) * (this.canvas.height / r.height);
    return this.toMath(px, py);
  }

  /** 拖了把手（箭头或目标点）才算「开始自己动手」；平移视图不算 */
  onUserEdit?: () => void;

  private bindDrag() {
    this.canvas.addEventListener("pointerdown", (ev) => {
      const [x, y] = this.eventPoint(ev);
      if (this.target) {
        const dt = Math.hypot(x - this.target[0], y - this.target[1]);
        if (dt < 0.55) {
          this.dragging = "t";
          this.canvas.setPointerCapture(ev.pointerId);
          this.canvas.classList.add("dragging");
          return;
        }
      }
      const di = Math.hypot(x - this.m.a, y - this.m.c);
      const dj = Math.hypot(x - this.m.b, y - this.m.d);
      if (Math.min(di, dj) > 0.42) return;
      this.animToken += 1;
      this.dragging = di < dj ? "i" : "j";
      this.canvas.setPointerCapture(ev.pointerId);
      this.canvas.classList.add("dragging");
    });

    this.canvas.addEventListener("pointermove", (ev) => {
      if (!this.dragging) return;
      let [x, y] = this.eventPoint(ev);
      // 默认吸附到四分之一格，按住 shift 自由拖：先让人容易拖到整数，再放开精度
      if (!ev.shiftKey) {
        x = Math.round(x * 4) / 4;
        y = Math.round(y * 4) / 4;
      }
      if (this.dragging === "pan") {
        const r = this.canvas.getBoundingClientRect();
        const k = this.canvas.width / r.width; // CSS 像素 → 画布像素
        this.panX = this.panFrom[2] + (ev.clientX - this.panFrom[0]) * k;
        this.panY = this.panFrom[3] + (ev.clientY - this.panFrom[1]) * k;
        this.draw();
        return;
      }
      if (this.dragging === "t") {
        this.target = [x, y];
        this.draw();
        return;
      }
      this.onUserEdit?.();
      if (this.dragging === "i") {
        this.m.a = x;
        this.m.c = y;
      } else {
        this.m.b = x;
        this.m.d = y;
      }
      this.draw();
    });

    this.canvas.addEventListener(
      "wheel",
      (ev) => {
        ev.preventDefault();
        this.setZoom(this.zoom * (ev.deltaY > 0 ? 0.9 : 1.1));
      },
      { passive: false },
    );

    const stop = () => {
      this.dragging = null;
      this.canvas.classList.remove("dragging");
    };
    this.canvas.addEventListener("pointerup", stop);
    this.canvas.addEventListener("pointercancel", stop);
  }

  private arrow(x: number, y: number, color: string, label: string) {
    const ctx = this.ctx;
    const [px, py] = this.toPx(x, y);
    const shaft = this.S * 0.085;
    const head = this.S * 0.34;
    const tip = this.S * 0.16;
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = shaft;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(this.ox, this.oy);
    ctx.lineTo(px, py);
    ctx.stroke();

    const ang = Math.atan2(py - this.oy, px - this.ox);
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.lineTo(px - head * Math.cos(ang - 0.38), py - head * Math.sin(ang - 0.38));
    ctx.lineTo(px - head * Math.cos(ang + 0.38), py - head * Math.sin(ang + 0.38));
    ctx.closePath();
    ctx.fill();

    ctx.beginPath();
    ctx.arc(px, py, tip, 0, Math.PI * 2);
    ctx.fill();

    ctx.font = `600 ${Math.round(this.S * 0.24)}px -apple-system, "PingFang SC", sans-serif`;
    ctx.fillText(label, px + tip + 8, py - tip);
  }

  /**
   * 原点。画在最上层并留白一圈，因为它是这张图里唯一不动的点——
   * 线性变换把直线送成直线、且始终把原点送回原点，能平移的变换矩阵表达不了。
   */
  private origin() {
    const ctx = this.ctx;
    const [x, y] = this.toPx(0, 0);

    // 先铺一圈底色，把底下的网格线压淡，免得原点混在格子里
    const halo = this.S * 0.14;
    ctx.beginPath();
    ctx.arc(x, y, halo, 0, Math.PI * 2);
    ctx.fillStyle = this.css("--bg");
    ctx.fill();

    ctx.beginPath();
    ctx.arc(x, y, halo * 0.78, 0, Math.PI * 2);
    ctx.strokeStyle = this.css("--ink");
    ctx.lineWidth = this.S * 0.04;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(x, y, halo * 0.34, 0, Math.PI * 2);
    ctx.fillStyle = this.css("--ink");
    ctx.fill();

    ctx.font = `600 ${Math.round(this.S * 0.2)}px -apple-system, "PingFang SC", sans-serif`;
    ctx.fillText("原点（不动）", x - this.S * 1.05, y + this.S * 0.28);
  }

  /** 把「走 x 步蓝箭头、再走 y 步橙箭头到达 b」这条路径画出来 */
  private drawReach() {
    if (!this.target) return;
    const ctx = this.ctx;
    const { a, b, c, d } = this.m;
    const [bx, by] = this.target;
    const res = this.reach();
    const warn = this.css("--warn");
    const ok = this.css("--eigen");

    // 无穷多解：所有走法落在一条直线上，把它整条画出来
    if (res?.kind === "many") {
      const L = 14;
      ctx.save();
      ctx.strokeStyle = ok;
      ctx.lineWidth = this.S * 0.03;
      ctx.setLineDash([10, 8]);
      // 解集在「步数平面」上是直线，映射回图上仍沿着同一条列方向
      const p = this.toPx(bx - L * (a || b), by - L * (c || d));
      const q = this.toPx(bx + L * (a || b), by + L * (c || d));
      ctx.beginPath();
      ctx.moveTo(p[0], p[1]);
      ctx.lineTo(q[0], q[1]);
      ctx.stroke();
      ctx.restore();
    }

    // 唯一解为什么唯一：从 b 沿橙方向退回蓝所在的直线，只可能退到一个点。
    // 把这两条平行辅助线画出来，「只有一个交点」就是看得见的（而不是一句断言）。
    if (res?.kind === "one") {
      const L = 20;
      const mid: [number, number] = [a * res.x, c * res.x];
      ctx.save();
      ctx.setLineDash([7, 7]);
      ctx.lineWidth = this.S * 0.018;
      ctx.globalAlpha = 0.75;
      // 过 b 平行于橙箭头
      ctx.strokeStyle = this.css("--basis-j");
      let p = this.toPx(bx - L * b, by - L * d);
      let q = this.toPx(bx + L * b, by + L * d);
      ctx.beginPath();
      ctx.moveTo(p[0], p[1]);
      ctx.lineTo(q[0], q[1]);
      ctx.stroke();
      // 蓝箭头所在的整条直线
      ctx.strokeStyle = this.css("--basis-i");
      p = this.toPx(-L * a, -L * c);
      q = this.toPx(L * a, L * c);
      ctx.beginPath();
      ctx.moveTo(p[0], p[1]);
      ctx.lineTo(q[0], q[1]);
      ctx.stroke();
      ctx.restore();

      // 交点：蓝要走几步，到这里就定死了
      const [mx, my] = this.toPx(mid[0], mid[1]);
      ctx.beginPath();
      ctx.arc(mx, my, this.S * 0.07, 0, Math.PI * 2);
      ctx.fillStyle = this.css("--bg");
      ctx.fill();
      ctx.strokeStyle = this.css("--ink");
      ctx.lineWidth = this.S * 0.025;
      ctx.stroke();
    }

    // 走法路径：原点 → 走 x 步蓝箭头 → 再走 y 步橙箭头 → 到 b
    if (res && res.kind !== "none") {
      const midX = a * res.x;
      const midY = c * res.x;
      ctx.save();
      ctx.lineWidth = this.S * 0.05;
      ctx.lineCap = "round";
      ctx.strokeStyle = this.css("--basis-i");
      ctx.globalAlpha = 0.55;
      let p = this.toPx(0, 0);
      let q = this.toPx(midX, midY);
      ctx.beginPath();
      ctx.moveTo(p[0], p[1]);
      ctx.lineTo(q[0], q[1]);
      ctx.stroke();
      ctx.strokeStyle = this.css("--basis-j");
      p = q;
      q = this.toPx(midX + b * res.y, midY + d * res.y);
      ctx.beginPath();
      ctx.moveTo(p[0], p[1]);
      ctx.lineTo(q[0], q[1]);
      ctx.stroke();
      ctx.restore();
    }

    // 目标点
    const [tx, ty] = this.toPx(bx, by);
    const rr = this.S * 0.13;
    ctx.beginPath();
    ctx.arc(tx, ty, rr, 0, Math.PI * 2);
    ctx.fillStyle = res?.kind === "none" ? warn : ok;
    ctx.fill();
    ctx.strokeStyle = this.css("--bg");
    ctx.lineWidth = this.S * 0.03;
    ctx.stroke();
    ctx.fillStyle = res?.kind === "none" ? warn : ok;
    ctx.font = `600 ${Math.round(this.S * 0.21)}px -apple-system, "PingFang SC", sans-serif`;
    ctx.fillText(
      res?.kind === "none" ? "b（走不到）" : "b（要到这里）",
      tx + rr * 1.4,
      ty - rr * 0.8,
    );
  }

  draw() {
    const ctx = this.ctx;
    const { a, b, c, d } = this.m;
    const r = readoutOf(this.m);
    const W = this.canvas.width;
    const H = this.canvas.height;
    const L = 8;

    ctx.clearRect(0, 0, W, H);

    // 原始网格
    ctx.strokeStyle = this.css("--grid");
    ctx.lineWidth = Math.max(2, this.S * 0.012);
    for (let k = -L; k <= L; k++) {
      let p = this.toPx(k, -L);
      let q = this.toPx(k, L);
      ctx.beginPath();
      ctx.moveTo(p[0], p[1]);
      ctx.lineTo(q[0], q[1]);
      ctx.stroke();
      p = this.toPx(-L, k);
      q = this.toPx(L, k);
      ctx.beginPath();
      ctx.moveTo(p[0], p[1]);
      ctx.lineTo(q[0], q[1]);
      ctx.stroke();
    }

    // 变换后的网格：原网格线的像
    ctx.strokeStyle = this.css("--grid-image");
    ctx.lineWidth = Math.max(2.5, this.S * 0.018);
    for (let k = -L; k <= L; k++) {
      // x = k 的像：过 k·i，方向 j
      let p = this.toPx(k * a - L * b, k * c - L * d);
      let q = this.toPx(k * a + L * b, k * c + L * d);
      ctx.beginPath();
      ctx.moveTo(p[0], p[1]);
      ctx.lineTo(q[0], q[1]);
      ctx.stroke();
      // y = k 的像：过 k·j，方向 i
      p = this.toPx(-L * a + k * b, -L * c + k * d);
      q = this.toPx(L * a + k * b, L * c + k * d);
      ctx.beginPath();
      ctx.moveTo(p[0], p[1]);
      ctx.lineTo(q[0], q[1]);
      ctx.stroke();
    }

    // 单位正方形的像：面积就是 |det|
    const P = [this.toPx(0, 0), this.toPx(a, c), this.toPx(a + b, c + d), this.toPx(b, d)];
    ctx.beginPath();
    ctx.moveTo(P[0][0], P[0][1]);
    for (let k = 1; k < 4; k++) ctx.lineTo(P[k][0], P[k][1]);
    ctx.closePath();
    ctx.fillStyle = r.flipped ? "rgba(217,72,15,.20)" : "rgba(10,88,202,.17)";
    ctx.fill();

    if (this.options.showEigen !== false) {
      ctx.strokeStyle = this.css("--eigen");
      ctx.lineWidth = this.S * 0.022;
      ctx.setLineDash([12, 9]);
      for (const [vx, vy] of r.eigenDirs) {
        const p = this.toPx(-L * vx, -L * vy);
        const q = this.toPx(L * vx, L * vy);
        ctx.beginPath();
        ctx.moveTo(p[0], p[1]);
        ctx.lineTo(q[0], q[1]);
        ctx.stroke();
      }
      ctx.setLineDash([]);
    }

    // 坐标轴
    ctx.strokeStyle = this.css("--line");
    ctx.lineWidth = Math.max(3, this.S * 0.02);
    ctx.beginPath();
    ctx.moveTo(0, this.oy);
    ctx.lineTo(W, this.oy);
    ctx.moveTo(this.ox, 0);
    ctx.lineTo(this.ox, H);
    ctx.stroke();

    this.drawReach();

    this.arrow(a, c, this.css("--basis-i"), "向右一格");
    this.arrow(b, d, this.css("--basis-j"), "向上一格");
    this.origin();

    this.onChange(this.matrix, r);
  }
}
