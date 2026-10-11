// SVG 进度环:掌握率可视化,成绩必须有出口(ADR 0052)。
import type { ReactNode } from "react";

interface Props {
  value: number; // 0–1
  size?: number;
  stroke?: number;
  color?: string;
  label?: string;
  children?: ReactNode;
}

export default function ProgressRing({ value, size = 44, stroke = 5, color, label, children }: Props) {
  const clamped = Math.max(0, Math.min(1, value));
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - clamped);
  const fallback = clamped > 0 ? `${Math.round(clamped * 100)}%` : "";

  return (
    <span
      className="relative inline-flex items-center justify-center"
      style={{ width: `${size}px`, height: `${size}px` }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(0,0,0,0.07)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color ?? "var(--tk-accent)"}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s cubic-bezier(0.22, 1, 0.36, 1)" }}
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center text-[10px] font-bold"
        style={{ color: "var(--tk-muted)" }}
      >
        {children ?? label ?? fallback}
      </span>
    </span>
  );
}
