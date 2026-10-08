import { useState } from "react";
import { VizShell } from "./common";

const NODES = [
  { id: "ready", label: "就绪", x: 300, y: 40, color: "#6D5AE6" },
  { id: "running", label: "运行", x: 300, y: 200, color: "#0E8A6D" },
  { id: "blocked", label: "阻塞", x: 80, y: 200, color: "#E05B5B" },
];

const EDGES: { from: string; to: string; label: string; why: string; path: string; hx: number }[] = [
  {
    from: "ready",
    to: "running",
    label: "调度选中",
    why: "调度程序从就绪队列挑中它,分配 CPU。",
    path: "M 340 70 Q 400 120 340 182",
    hx: 372,
  },
  {
    from: "running",
    to: "ready",
    label: "时间片到 / 被抢占",
    why: "时间片用完(或更高优先级到来),回到就绪队列排队。",
    path: "M 262 182 Q 200 120 262 70",
    hx: 216,
  },
  {
    from: "running",
    to: "blocked",
    label: "等 I/O / P 操作失败",
    why: "主动让出 CPU 等待事件,进入阻塞态。",
    path: "M 262 210 L 150 210",
    hx: 206,
  },
  {
    from: "blocked",
    to: "ready",
    label: "事件发生",
    why: "I/O 完成或 V 操作唤醒——注意:只能回到就绪排队,不能直达运行!",
    path: "M 100 182 Q 80 120 262 52",
    hx: 96,
  },
];

export function ProcessStates() {
  const [selected, setSelected] = useState(3); // 默认讲「事件发生」这条最易错的边
  const edge = EDGES[selected];
  return (
    <VizShell title="进程三态图 · 点边看触发事件" controls={<span className="text-ink/50">阻塞 → 运行这条边不存在</span>}>
      <svg viewBox="0 0 460 250" className="w-full max-w-[560px]">
        {EDGES.map((e, i) => {
          const active = i === selected;
          const id = `${e.from}-${e.to}`;
          return (
            <g key={id} onClick={() => setSelected(i)} className="cursor-pointer">
              <path
                d={e.path}
                fill="none"
                stroke={active ? "#6D5AE6" : "rgba(30,27,46,0.22)"}
                strokeWidth={active ? 3 : 2}
                markerEnd={`url(#arrow-${active ? "on" : "off"})`}
              />
            </g>
          );
        })}
        <defs>
          <marker id="arrow-on" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="#6D5AE6" />
          </marker>
          <marker id="arrow-off" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="rgba(30,27,46,0.3)" />
          </marker>
        </defs>
        {NODES.map((nd) => (
          <g key={nd.id}>
            <rect x={nd.x - 62} y={nd.y - 24} width={124} height={48} rx={14} fill={nd.color} opacity={0.92} />
            <text x={nd.x} y={nd.y + 6} textAnchor="middle" fontSize={17} fontWeight="bold" fill="#fff">
              {nd.label}
            </text>
          </g>
        ))}
        {EDGES.map((e, i) => (
          <text
            key={i}
            x={e.hx}
            y={i === selected ? undefined : undefined}
            fontSize={11}
            fill={i === selected ? "#4936AB" : "rgba(30,27,46,0.4)"}
            fontWeight={i === selected ? "bold" : "normal"}
          >
            <textPath href={`#${e.from}-${e.to}-label`} startOffset="8%" style={{ display: "none" }} />
          </text>
        ))}
      </svg>
      <div className="mt-2 rounded-xl bg-brand-50 px-4 py-3">
        <span className="font-bold text-brand-700">{edge.label}</span>
        <span className="ml-2 text-[13.5px] text-ink/75">{edge.why}</span>
      </div>
    </VizShell>
  );
}
