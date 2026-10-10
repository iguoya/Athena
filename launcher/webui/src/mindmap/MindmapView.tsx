// 2D 椭圆思维导图视图：gui 版构图的 Web 移植（ADR 0127）。
// 布局坐标全部来自 launcher-core 的 mindmap::layout，这里只渲染与转发交互。

import { useEffect, useState } from "react";
import { openApp, stopApp, type RunState } from "../api";
import { invoke } from "@tauri-apps/api/core";

export interface MindNodeDto {
  id: string;
  title: string;
  letter: string;
  accent: string;
  icon: string | null;
  state: RunState;
  reference: boolean;
  x: number;
  y: number;
}

export interface MindGroupDto {
  name: string;
  color: string;
  x: number;
  y: number;
  w: number;
}

export interface MindLinkDto {
  kind: number;
  color: string;
  hot: string;
  a: number;
  b: number;
  x0: number; y0: number;
  cx1: number; cy1: number;
  cx2: number; cy2: number;
  x1: number; y1: number;
  has_arrow: boolean;
  ax: number; ay: number;
  bx: number; by: number;
  cx: number; cy: number;
  dashes: [number, number, number, number][];
}

export interface MindmapDto {
  width: number;
  height: number;
  center_x: number;
  center_y: number;
  nodes: MindNodeDto[];
  groups: MindGroupDto[];
  links: MindLinkDto[];
  rings: string;
  rings_x: number;
  rings_y: number;
  rings_w: number;
  rings_h: number;
}

const STATE_COLOR: Record<RunState, string> = {
  stopped: "#b0b4c8",
  starting: "#e8940f",
  ready: "#2e9e44",
};

function fetchMindmap(): Promise<MindmapDto> {
  return invoke<MindmapDto>("mindmap");
}

function Tile({
  node, index, active, onHover,
}: {
  node: MindNodeDto;
  index: number;
  active: boolean;
  onHover: (i: number | null) => void;
}) {
  return (
    <div
      className="tile"
      data-state={node.state}
      title={node.title}
      style={{
        position: "absolute",
        left: node.x - 58,
        top: node.y - 38,
        opacity: active ? 1 : 0.55,
        transition: "opacity 120ms",
      }}
      onClick={() => openApp(node.id).catch(console.error)}
      onContextMenu={(e) => {
        e.preventDefault();
        if (node.state !== "stopped") stopApp(node.id).catch(console.error);
      }}
      onMouseEnter={() => onHover(index)}
      onMouseLeave={() => onHover(null)}
    >
      {node.icon ? (
        <img src={node.icon} alt="" />
      ) : (
        <div className="fallback" style={{ background: node.accent }}>
          {node.letter}
        </div>
      )}
      <span className="name">{node.title}</span>
      <span className="dot" style={{ background: STATE_COLOR[node.state] }} />
    </div>
  );
}

// 椭圆导图：同心环底图（core 预渲染 PNG）→ 连线（默认虚线，悬停节点点亮相关线为
// 实线）→ 领域胶囊 → 虎头 → 图块。节点下标即连线端点下标（nodes 与 ends 同一序列）。
export default function MindmapView() {
  const [map, setMap] = useState<MindmapDto | null>(null);
  const [hovered, setHovered] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const pull = () =>
      fetchMindmap()
        .then((m) => {
          if (alive) {
            setMap(m);
            setError(null);
          }
        })
        .catch((e) => alive && setError(String(e)));
    pull();
    const timer = setInterval(pull, 3000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  if (error) return <div className="status">导图读取失败：{error}</div>;
  if (!map) return <div className="status">排布导图…</div>;

  return (
    <div style={{ height: "100vh", overflow: "auto", padding: "52px 12px 12px" }}>
      <div
        style={{
          position: "relative",
          width: map.width,
          height: map.height,
          margin: "0 auto",
        }}
      >
        <img
          src={map.rings}
          alt=""
          style={{
            position: "absolute",
            left: map.rings_x,
            top: map.rings_y,
            width: map.rings_w,
            height: map.rings_h,
            pointerEvents: "none",
          }}
        />
        <svg
          width={map.width}
          height={map.height}
          style={{ position: "absolute", left: 0, top: 0, pointerEvents: "none" }}
        >
          {map.links.map((l, i) => {
            const active = hovered !== null && (l.a === hovered || l.b === hovered);
            const dim = hovered !== null && !active;
            return (
              <g key={i}>
                {!active &&
                  l.dashes.map(([x0, y0, x1, y1], k) => (
                    <line
                      key={k}
                      x1={x0} y1={y0} x2={x1} y2={y1}
                      stroke={l.color}
                      strokeWidth={1.4}
                      opacity={dim ? 0.45 : 1}
                      style={{ transition: "opacity 120ms" }}
                    />
                  ))}
                {active && (
                  <path
                    d={`M ${l.x0} ${l.y0} C ${l.cx1} ${l.cy1}, ${l.cx2} ${l.cy2}, ${l.x1} ${l.y1}`}
                    fill="none"
                    stroke={l.hot}
                    strokeWidth={l.kind === 2 ? 2.4 : 1.8}
                  />
                )}
                {l.has_arrow && (
                  <polygon
                    points={`${l.ax},${l.ay} ${l.bx},${l.by} ${l.cx},${l.cy}`}
                    fill={active ? l.hot : l.color}
                    opacity={dim ? 0.45 : 1}
                  />
                )}
              </g>
            );
          })}
          {map.groups.map((g, i) => (
            <g key={i}>
              <rect
                x={g.x - g.w / 2} y={g.y - 16} width={g.w} height={32} rx={16}
                fill={g.color}
              />
              <text
                x={g.x} y={g.y} textAnchor="middle" dominantBaseline="central"
                fill="white" fontSize={13} fontWeight={600}
              >
                {g.name}
              </text>
            </g>
          ))}
        </svg>
        <img
          src="/tiger-mark.png"
          alt=""
          style={{
            position: "absolute",
            left: map.center_x - 36,
            top: map.center_y - 36,
            width: 72,
            height: 72,
            pointerEvents: "none",
          }}
        />
        {map.nodes.map((n, i) => (
          <Tile
            key={`${n.id}-${i}`}
            node={n}
            index={i}
            active={hovered === null || hovered === i}
            onHover={setHovered}
          />
        ))}
      </div>
    </div>
  );
}
