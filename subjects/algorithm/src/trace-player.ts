// 步进可视化回放器（本应用 ADR 0004）。
// 只消费 C++ 驱动打印的 `#dsa-trace {...}` 状态快照行并逐步渲染，不在前端
// 复刻任何算法真相；stdout 无快照时观察区走原 key=value 文本模式。
// 观察区同一时刻至多一个回放器，播放定时器用模块级单例管理。

export interface TraceFrame {
  kind: string;
  step: number;
  note: string;
  focus: number;
  values: number[];
}

const PREFIX = "#dsa-trace ";
const PLAY_INTERVAL_MS = 600;

export function parseTrace(stdout: string): TraceFrame[] {
  const frames: TraceFrame[] = [];
  for (const raw of stdout.split("\n")) {
    const line = raw.trimStart();
    if (!line.startsWith(PREFIX)) continue;
    try {
      const f = JSON.parse(line.slice(PREFIX.length)) as Partial<TraceFrame>;
      // 协议要求每行独立合法；坏行跳过，不拖垮整段回放。
      if (typeof f.kind === "string" && typeof f.step === "number") {
        frames.push(f as TraceFrame);
      }
    } catch {
      // 同上：坏行跳过。
    }
  }
  return frames.sort((a, b) => a.step - b.step);
}

let playTimer: ReturnType<typeof setInterval> | null = null;

export function stopTracePlayback() {
  if (playTimer !== null) {
    clearInterval(playTimer);
    playTimer = null;
  }
}

function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// 链表快照：横向节点框 + 箭头 + focus 高亮 + null 结尾。只画快照。
function renderListSvg(f: TraceFrame): string {
  const values = Array.isArray(f.values) ? f.values : [];
  const focus = typeof f.focus === "number" ? f.focus : -1;
  const BW = 56;
  const BH = 40;
  const GAP = 44;
  const NULL_W = 48;
  const X0 = 14;
  const Y0 = 22;
  const cy = Y0 + BH / 2;
  const tailGap = values.length ? GAP : 0;
  const w = X0 * 2 + values.length * (BW + GAP) - (values.length ? GAP : 0) + tailGap + NULL_W;
  const h = Y0 * 2 + BH;
  const nodeX = (i: number) => X0 + i * (BW + GAP);
  const nullX = X0 + values.length * (BW + GAP);

  const nodes = values
    .map((v, i) => {
      const x = nodeX(i);
      const cls = i === focus ? "list-node focused" : "list-node";
      return `<g class="${cls}">
          <rect x="${x}" y="${Y0}" width="${BW}" height="${BH}" rx="6"></rect>
          <text x="${x + BW / 2}" y="${cy + 5}" text-anchor="middle" class="list-val">${v}</text>
        </g>`;
    })
    .join("");

  const arrows = values
    .map((_, i) => {
      const x1 = nodeX(i) + BW;
      const x2 = nodeX(i + 1) - 9;
      return `<g class="list-arrow">
          <line x1="${x1}" y1="${cy}" x2="${x2}" y2="${cy}"></line>
          <polygon points="${x2},${cy - 5} ${x2 + 8},${cy} ${x2},${cy + 5}"></polygon>
        </g>`;
    })
    .join("");

  const nullBox = `<g class="list-null">
      <rect x="${nullX}" y="${Y0}" width="${NULL_W}" height="${BH}" rx="6"></rect>
      <text x="${nullX + NULL_W / 2}" y="${cy + 5}" text-anchor="middle">null</text>
    </g>`;

  return `<svg viewBox="0 0 ${w} ${h}" class="trace-svg" role="img"
      aria-label="链表快照：${values.join(" → ") || "空链表"}">
      ${nodes}${arrows}${nullBox}
    </svg>`;
}

// 未知 kind 降级为列出原始 JSON：协议前向演进不迫使旧回放器崩溃（ADR 0004）。
function renderUnknown(f: TraceFrame): string {
  return `<pre class="trace-raw">${esc(JSON.stringify(f, null, 2))}</pre>`;
}

function renderFrame(f: TraceFrame): string {
  return f.kind === "list" ? renderListSvg(f) : renderUnknown(f);
}

export function mountTracePlayer(container: HTMLElement, frames: TraceFrame[]) {
  stopTracePlayback();

  const root = document.createElement("div");
  root.className = "trace-player";
  root.innerHTML = `
    <div class="trace-stage"></div>
    <div class="trace-note"></div>
    <div class="trace-controls">
      <button type="button" data-act="first" title="跳到第一步">|&lt;</button>
      <button type="button" data-act="prev" title="上一步">&lt;</button>
      <button type="button" data-act="play" class="trace-play">播放</button>
      <button type="button" data-act="next" title="下一步">&gt;</button>
      <button type="button" data-act="last" title="跳到最后一步">|&gt;</button>
      <span class="trace-step"></span>
      <input type="range" class="trace-range" min="0" max="${frames.length - 1}" value="0" />
    </div>`;
  container.appendChild(root);

  const stage = root.querySelector<HTMLElement>(".trace-stage")!;
  const note = root.querySelector<HTMLElement>(".trace-note")!;
  const stepLabel = root.querySelector<HTMLElement>(".trace-step")!;
  const range = root.querySelector<HTMLInputElement>(".trace-range")!;
  const playBtn = root.querySelector<HTMLButtonElement>('[data-act="play"]')!;
  const buttons = root.querySelectorAll<HTMLButtonElement>(".trace-controls button");

  let idx = 0;

  const render = (i: number) => {
    idx = Math.max(0, Math.min(frames.length - 1, i));
    const f = frames[idx];
    stage.innerHTML = renderFrame(f);
    note.textContent = f.note ?? "";
    stepLabel.textContent = `第 ${idx + 1} / ${frames.length} 步`;
    range.value = String(idx);
    const atEnd = idx === frames.length - 1;
    const atStart = idx === 0;
    buttons.forEach((b) => {
      const act = b.dataset.act;
      if (act === "prev" || act === "first") b.disabled = atStart;
      if (act === "next" || act === "last") b.disabled = atEnd;
    });
  };

  const setPlaying = (on: boolean) => {
    stopTracePlayback();
    playBtn.textContent = on ? "暂停" : "播放";
    if (!on) return;
    playTimer = setInterval(() => {
      if (idx >= frames.length - 1) {
        setPlaying(false);
        return;
      }
      render(idx + 1);
    }, PLAY_INTERVAL_MS);
  };

  root.querySelector(".trace-controls")!.addEventListener("click", (ev) => {
    const btn = (ev.target as HTMLElement).closest("button");
    if (!btn) return;
    const act = btn.dataset.act;
    if (act === "first") render(0);
    else if (act === "prev") render(idx - 1);
    else if (act === "next") render(idx + 1);
    else if (act === "last") render(frames.length - 1);
    else if (act === "play") setPlaying(playTimer === null);
  });
  range.addEventListener("input", () => {
    setPlaying(false);
    render(Number(range.value));
  });
  root.addEventListener("dblclick", () => setPlaying(false));

  render(0);
}
