// 线代知识图谱：按 requires 实时绘制的先修图（ADR 0008 第 1 节）。
// 布局、连线、状态全部由课表与进度算出来，不是一张会跟数据漂移的图片。
// Canvas 自绘而非 SVG 静态图，因为要 hover 追依赖链、点击跳转（ADR 0010 第 2 节）。

export interface GraphNode {
  id: string;
  title: string;
  requires: string[];
  /** 走过（overview 层看过） */
  seen: boolean;
  /** 判过对错且答对 */
  passed: boolean;
  scope: string;
}

interface Placed extends GraphNode {
  x: number;
  y: number;
  layer: number;
}

const NW = 252; // 节点宽
const NH = 56; // 节点高
const VGAP = 128; // 层间距
const HGAP = 34; // 同层间距
const PAD_TOP = 54;

export class GraphView {
  private ctx: CanvasRenderingContext2D;
  private placed: Placed[] = [];
  private byId = new Map<string, Placed>();
  private hover: string | null = null;

  constructor(
    private canvas: HTMLCanvasElement,
    nodes: GraphNode[],
    private onPick: (id: string) => void,
    private current?: string,
  ) {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("画布不可用");
    this.ctx = ctx;
    this.layout(nodes);
    this.bind();
  }

  /** 拓扑分层：节点的层号 = 所有先修里最深的那个 + 1 */
  private layout(nodes: GraphNode[]) {
    const src = new Map(nodes.map((n) => [n.id, n]));
    const depth = new Map<string, number>();
    const of = (id: string): number => {
      if (depth.has(id)) return depth.get(id)!;
      const n = src.get(id);
      const reqs = n?.requires.filter((r) => src.has(r)) ?? [];
      const d = reqs.length ? 1 + Math.max(...reqs.map(of)) : 0;
      depth.set(id, d);
      return d;
    };
    nodes.forEach((n) => of(n.id));

    const rows = new Map<number, GraphNode[]>();
    for (const n of nodes) {
      const d = depth.get(n.id)!;
      if (!rows.has(d)) rows.set(d, []);
      rows.get(d)!.push(n);
    }

    const W = this.canvas.width;
    for (const [layer, list] of [...rows.entries()].sort((a, b) => a[0] - b[0])) {
      const total = list.length * NW + (list.length - 1) * HGAP;
      let x = (W - total) / 2;
      for (const n of list) {
        const p: Placed = { ...n, x, y: PAD_TOP + layer * VGAP, layer };
        this.placed.push(p);
        this.byId.set(n.id, p);
        x += NW + HGAP;
      }
    }
  }

  /** 某个节点的全部先修（递归），用来在 hover 时把整条依赖链点亮 */
  private ancestors(id: string, out = new Set<string>()): Set<string> {
    for (const r of this.byId.get(id)?.requires ?? []) {
      if (!out.has(r)) {
        out.add(r);
        this.ancestors(r, out);
      }
    }
    return out;
  }

  private hit(ev: PointerEvent | MouseEvent): string | null {
    const r = this.canvas.getBoundingClientRect();
    const x = (ev.clientX - r.left) * (this.canvas.width / r.width);
    const y = (ev.clientY - r.top) * (this.canvas.height / r.height);
    for (const p of this.placed) {
      if (x >= p.x && x <= p.x + NW && y >= p.y && y <= p.y + NH) return p.id;
    }
    return null;
  }

  private bind() {
    this.canvas.addEventListener("mousemove", (ev) => {
      const id = this.hit(ev);
      if (id !== this.hover) {
        this.hover = id;
        this.canvas.style.cursor = id ? "pointer" : "default";
        this.draw();
      }
    });
    this.canvas.addEventListener("mouseleave", () => {
      if (this.hover) {
        this.hover = null;
        this.draw();
      }
    });
    this.canvas.addEventListener("click", (ev) => {
      const id = this.hit(ev);
      if (id) this.onPick(id);
    });
  }

  private css(n: string): string {
    return getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  }

  private roundRect(x: number, y: number, w: number, h: number, r: number) {
    const ctx = this.ctx;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  draw() {
    const ctx = this.ctx;
    const W = this.canvas.width;
    const H = this.canvas.height;
    ctx.clearRect(0, 0, W, H);

    const lit = this.hover ? this.ancestors(this.hover) : new Set<string>();
    if (this.hover) lit.add(this.hover);

    // ── 连线：从先修的底部连到本节点的顶部 ──
    for (const p of this.placed) {
      for (const r of p.requires) {
        const q = this.byId.get(r);
        if (!q) continue;
        const onPath = lit.has(p.id) && lit.has(r);
        const x1 = q.x + NW / 2;
        const y1 = q.y + NH;
        const x2 = p.x + NW / 2;
        const y2 = p.y;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.bezierCurveTo(x1, y1 + VGAP * 0.42, x2, y2 - VGAP * 0.42, x2, y2);
        // 连线是这张图的主体信息，用比边框更深的颜色，别让它淡到看不见
        ctx.strokeStyle = onPath ? this.css("--accent") : this.css("--grid-image");
        ctx.lineWidth = onPath ? 4 : 2.2;
        ctx.stroke();
      }
    }

    // ── 节点 ──
    ctx.textBaseline = "middle";
    ctx.textAlign = "center";
    for (const p of this.placed) {
      const isCur = p.id === this.current;
      const onPath = lit.has(p.id);

      this.roundRect(p.x, p.y, NW, NH, 10);
      ctx.fillStyle = onPath || isCur ? this.css("--panel-2") : this.css("--panel");
      ctx.fill();

      // 边框颜色说的是状态：答对 > 走过 > 未走；当前所在与 hover 链用强调色盖过
      let border = this.css("--line");
      let width = 1.8;
      if (p.passed) {
        border = this.css("--ok");
        width = 3;
      } else if (p.seen) {
        border = this.css("--muted");
        width = 2.4;
      }
      if (onPath || isCur) {
        border = this.css("--accent");
        width = 3.5;
      }
      ctx.strokeStyle = border;
      ctx.lineWidth = width;
      this.roundRect(p.x, p.y, NW, NH, 10);
      ctx.stroke();

      // 拓展节点（考纲外）用虚线底纹提示，不喧宾夺主
      if (p.scope === "beyond") {
        ctx.save();
        ctx.setLineDash([5, 5]);
        ctx.strokeStyle = this.css("--muted");
        ctx.lineWidth = 1.2;
        this.roundRect(p.x + 5, p.y + 5, NW - 10, NH - 10, 7);
        ctx.stroke();
        ctx.restore();
      }

      ctx.fillStyle =
        onPath || isCur
          ? this.css("--accent")
          : p.seen || p.passed
            ? this.css("--ink")
            : this.css("--muted");
      ctx.font = `${p.passed || isCur ? 600 : 500} 19px -apple-system, "PingFang SC", sans-serif`;
      ctx.fillText(p.title, p.x + NW / 2, p.y + NH / 2 + 1, NW - 22);

      if (p.passed) {
        ctx.fillStyle = this.css("--ok");
        ctx.font = '700 17px -apple-system, sans-serif';
        ctx.fillText("✓", p.x + 14, p.y + NH / 2 + 1);
      }
    }
    ctx.textAlign = "left";
  }
}
