import { useMemo, useState } from "react";
import {
  COLORS,
  UNPAINTED,
  isometric,
  label,
  layerSlots,
  parse,
  run,
  solved,
  type Stickers,
} from "./cube";

// 讲解里的两种图：魔方步骤回放（展开图 + 立体图），和一张简单的条形图。

export type CubeFigureSpec = {
  kind: "cube";
  title: string;
  caption: string;
  /** 先从复原态转这一串，得到起点。不写就是复原态。 */
  setup?: string;
  /** 或者直接给 24 位数字作为起点（可以是真魔方上不可能出现的状态）。优先于 setup。 */
  state?: string;
  /** 逐步回放的转法。不写就是一张静态图。 */
  moves?: string;
  /** 额外圈出的贴纸编号（0..23）。 */
  marks?: number[];
  /** 回放走完后应当满足的阶段条件。只给 scripts/check.py 核对用，页面不显示。 */
  expect?: "solved" | "layer" | "oriented";
};

export type BarsFigureSpec = {
  kind: "bars";
  title: string;
  caption: string;
  items: { label: string; value: number }[];
};

export type Visual = CubeFigureSpec | BarsFigureSpec;

// ---- 展开图 ----
// 十字形：U 在上，L F R B 一排，D 在下。每个面 2×2 格，面与面之间留一点缝。
const GAP = 0.28;
const SPOTS: [number, number][] = [
  [1, 0], // U
  [2, 1], // R
  [1, 1], // F
  [1, 2], // D
  [0, 1], // L
  [3, 1], // B
];
const FACE_NAMES = ["U", "R", "F", "D", "L", "B"];

function fill(state: Stickers, slot: number) {
  const c = state[slot];
  return c >= 0 && c < 6 ? COLORS[c] : UNPAINTED;
}

function Net({ state, marks }: { state: Stickers; marks: Set<number> }) {
  const width = 4 * 2 + 3 * GAP;
  const height = 3 * 2 + 2 * GAP;
  return (
    <svg className="cubefig-net" viewBox={`-0.1 -0.35 ${width + 0.2} ${height + 0.45}`} role="img" aria-label="展开图">
      {SPOTS.map(([col, row], face) => {
        const fx = col * (2 + GAP);
        const fy = row * (2 + GAP);
        return (
          <g key={face}>
            <text x={fx + 0.02} y={fy - 0.06} className="face-name">
              {FACE_NAMES[face]}
            </text>
            {[0, 1, 2, 3].map((k) => {
              const slot = face * 4 + k;
              const x = fx + (k % 2);
              const y = fy + Math.floor(k / 2);
              return (
                <rect
                  key={slot}
                  x={x + 0.06}
                  y={y + 0.06}
                  width={0.88}
                  height={0.88}
                  rx={0.14}
                  fill={fill(state, slot)}
                  className={marks.has(slot) ? "sticker marked" : "sticker"}
                />
              );
            })}
          </g>
        );
      })}
    </svg>
  );
}

// ---- 立体图 ----

const QUADS = isometric();

function Iso({ state, marks }: { state: Stickers; marks: Set<number> }) {
  const { min, max } = useMemo(() => {
    const xs = QUADS.flatMap((q) => q.points.map((p) => p[0]));
    const ys = QUADS.flatMap((q) => q.points.map((p) => p[1]));
    return {
      min: [Math.min(...xs) - 0.2, Math.min(...ys) - 0.2],
      max: [Math.max(...xs) + 0.2, Math.max(...ys) + 0.2],
    };
  }, []);
  return (
    <svg
      className="cubefig-iso"
      viewBox={`${min[0]} ${min[1]} ${max[0] - min[0]} ${max[1] - min[1]}`}
      role="img"
      aria-label="立体图"
    >
      {QUADS.map((q) => (
        <polygon
          key={q.slot}
          points={q.points.map((p) => p.join(",")).join(" ")}
          fill={fill(state, q.slot)}
          className={marks.has(q.slot) ? "sticker3d marked" : "sticker3d"}
        />
      ))}
    </svg>
  );
}

function CubeFigure({ spec }: { spec: CubeFigureSpec }) {
  const { start, moves, states } = useMemo(() => {
    const start = spec.state
      ? spec.state.split("").map(Number)
      : spec.setup
        ? run(solved(), parse(spec.setup))
        : solved();
    const moves = spec.moves ? parse(spec.moves) : [];
    const states = [start];
    for (const move of moves) states.push(run(states[states.length - 1], [move]));
    return { start, moves, states };
  }, [spec.state, spec.setup, spec.moves]);
  const [step, setStep] = useState(0);
  const at = Math.min(step, moves.length);
  const state = states[at] ?? start;
  // 圈出刚转过的那一层；没有转法时圈 spec.marks。
  const marks = useMemo(() => {
    const set = new Set<number>(spec.marks ?? []);
    if (at > 0) for (const slot of layerSlots(moves[at - 1])) set.add(slot);
    return set;
  }, [at, moves, spec.marks]);

  return (
    <div className="cubefig">
      <div className="cubefig-views">
        <Net state={state} marks={marks} />
        <Iso state={state} marks={marks} />
      </div>
      {moves.length > 0 ? (
        <div className="cubefig-controls">
          <button type="button" onClick={() => setStep(0)} disabled={at === 0} aria-label="回到起点">
            ⏮
          </button>
          <button type="button" onClick={() => setStep(Math.max(0, at - 1))} disabled={at === 0}>
            上一步
          </button>
          <button type="button" onClick={() => setStep(Math.min(moves.length, at + 1))} disabled={at === moves.length}>
            下一步
          </button>
          <button type="button" onClick={() => setStep(moves.length)} disabled={at === moves.length} aria-label="跳到结尾">
            ⏭
          </button>
          <code className="cubefig-moves">
            {moves.map((move, i) => (
              <button
                key={i}
                type="button"
                className={i + 1 === at ? "now" : i < at ? "past" : ""}
                onClick={() => setStep(i + 1)}
              >
                {label(move)}
              </button>
            ))}
          </code>
        </div>
      ) : null}
    </div>
  );
}

function Bars({ spec }: { spec: BarsFigureSpec }) {
  const top = Math.max(...spec.items.map((item) => item.value));
  return (
    <div className="bars">
      {spec.items.map((item) => (
        <div className="bar" key={item.label}>
          <span className="bar-label">{item.label}</span>
          <span className="bar-track">
            <i style={{ width: `${(item.value / top) * 100}%` }} />
          </span>
          <span className="bar-value">{item.value.toLocaleString("zh-CN")}</span>
        </div>
      ))}
    </div>
  );
}

export function VisualFigure({ spec }: { spec: Visual }) {
  return (
    <figure className="diagram cubefig-wrap">
      <figcaption>{spec.title}</figcaption>
      {spec.kind === "cube" ? <CubeFigure spec={spec} /> : <Bars spec={spec} />}
      <p>{spec.caption}</p>
    </figure>
  );
}
