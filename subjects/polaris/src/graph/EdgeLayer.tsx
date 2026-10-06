import type { PlacedEdge } from "@/content/layout";

export type EdgeState = "idle" | "active" | "dim" | "selected";

interface Props {
  width: number;
  height: number;
  edges: PlacedEdge[];
  stateOf(edge: PlacedEdge): EdgeState;
}

// 三个箭头分别配三种状态的颜色：markerUnits 用 userSpaceOnUse，缩放时箭头跟着连线一起缩放。
const ARROWS: Record<"idle" | "active" | "dim", string> = {
  idle: "var(--edge)",
  active: "var(--accent)",
  dim: "var(--edge)",
};

export function EdgeLayer({ width, height, edges, stateOf }: Props) {
  return (
    <svg width={width} height={height} className="pointer-events-none absolute left-0 top-0 overflow-visible" aria-hidden>
      <defs>
        {(Object.keys(ARROWS) as (keyof typeof ARROWS)[]).map((key) => (
          <marker
            key={key}
            id={`arrow-${key}`}
            viewBox="0 0 10 10"
            refX="8.6"
            refY="5"
            markerWidth="9"
            markerHeight="9"
            markerUnits="userSpaceOnUse"
            orient="auto"
          >
            <path d="M0 0 L10 5 L0 10 z" fill={ARROWS[key]} />
          </marker>
        ))}
      </defs>
      {edges.map((placed) => {
        const state = stateOf(placed);
        const hot = state === "active" || state === "selected";
        const requires = placed.edge.relation === "requires";
        return (
          <path
            key={`${placed.edge.from}>${placed.edge.to}`}
            d={placed.path}
            fill="none"
            stroke={hot ? "var(--accent)" : "var(--edge)"}
            strokeWidth={hot ? 2.6 : requires ? 2 : 1.6}
            strokeLinecap="round"
            // 强先修画实线，来路画虚线；聚焦时让线沿方向流动（ADR 0013 决策 4）。
            strokeDasharray={hot ? "10 7" : requires ? undefined : "2 7"}
            opacity={state === "dim" ? 0.18 : 1}
            markerEnd={`url(#arrow-${hot ? "active" : state === "dim" ? "dim" : "idle"})`}
            style={hot ? { animation: "edge-flow 0.9s linear infinite" } : { transition: "opacity 200ms, stroke 200ms" }}
          />
        );
      })}
    </svg>
  );
}
