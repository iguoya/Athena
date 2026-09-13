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

export class TransformView {
  private ctx: CanvasRenderingContext2D;
  private m: Mat2 = { a: 1, b: 0, c: 0, d: 1 };
  private dragging: "i" | "j" | null = null;
  private readonly S: number;
  private readonly ox: number;
  private readonly oy: number;

  constructor(
    private canvas: HTMLCanvasElement,
    private onChange: (m: Mat2, r: Readout) => void,
  ) {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("画布不可用");
    this.ctx = ctx;
    this.S = Math.min(canvas.width, canvas.height) / 11;
    this.ox = canvas.width / 2;
    this.oy = canvas.height / 2;
    this.bindDrag();
  }

  get matrix(): Mat2 {
    return { ...this.m };
  }

  set(m: Mat2) {
    this.m = { ...m };
    this.draw();
  }

  private css(name: string): string {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  private toPx(x: number, y: number): [number, number] {
    return [this.ox + x * this.S, this.oy - y * this.S];
  }

  private toMath(px: number, py: number): [number, number] {
    return [(px - this.ox) / this.S, (this.oy - py) / this.S];
  }

  private eventPoint(ev: PointerEvent): [number, number] {
    const r = this.canvas.getBoundingClientRect();
    const px = (ev.clientX - r.left) * (this.canvas.width / r.width);
    const py = (ev.clientY - r.top) * (this.canvas.height / r.height);
    return this.toMath(px, py);
  }

  private bindDrag() {
    this.canvas.addEventListener("pointerdown", (ev) => {
      const [x, y] = this.eventPoint(ev);
      const di = Math.hypot(x - this.m.a, y - this.m.c);
      const dj = Math.hypot(x - this.m.b, y - this.m.d);
      if (Math.min(di, dj) > 0.55) return;
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
      if (this.dragging === "i") {
        this.m.a = x;
        this.m.c = y;
      } else {
        this.m.b = x;
        this.m.d = y;
      }
      this.draw();
    });

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
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.moveTo(this.ox, this.oy);
    ctx.lineTo(px, py);
    ctx.stroke();

    const ang = Math.atan2(py - this.oy, px - this.ox);
    const h = 22;
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.lineTo(px - h * Math.cos(ang - 0.4), py - h * Math.sin(ang - 0.4));
    ctx.lineTo(px - h * Math.cos(ang + 0.4), py - h * Math.sin(ang + 0.4));
    ctx.closePath();
    ctx.fill();

    ctx.beginPath();
    ctx.arc(px, py, 11, 0, Math.PI * 2);
    ctx.fill();

    ctx.font = '600 30px -apple-system, "PingFang SC", sans-serif';
    ctx.fillText(label, px + 16, py - 14);
  }

  draw() {
    const ctx = this.ctx;
    const { a, b, c, d } = this.m;
    const r = readoutOf(this.m);
    const W = this.canvas.width;
    const H = this.canvas.height;
    const L = 12;

    ctx.clearRect(0, 0, W, H);

    // 原始网格
    ctx.strokeStyle = this.css("--grid");
    ctx.lineWidth = 1.5;
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
    ctx.lineWidth = 2;
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

    // 方向不变的方向
    ctx.strokeStyle = this.css("--eigen");
    ctx.lineWidth = 2.5;
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

    // 坐标轴
    ctx.strokeStyle = this.css("--line");
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(0, this.oy);
    ctx.lineTo(W, this.oy);
    ctx.moveTo(this.ox, 0);
    ctx.lineTo(this.ox, H);
    ctx.stroke();

    this.arrow(a, c, this.css("--basis-i"), "向右一格");
    this.arrow(b, d, this.css("--basis-j"), "向上一格");

    this.onChange(this.matrix, r);
  }
}
