import type { ReactNode } from "react";
import type { Grade, KnowledgeType, MasteryGoal } from "../types";

/** 分值档位:S 核心 / A 重要 / B 次要 / C 突击 */
export function GradeBadge({ grade }: { grade: Grade }) {
  const style: Record<Grade, string> = {
    S: "bg-rose-100 text-rose-700 border-rose-200",
    A: "bg-amber-100 text-amber-700 border-amber-200",
    B: "bg-sky-100 text-sky-700 border-sky-200",
    C: "bg-slate-100 text-slate-600 border-slate-200",
  };
  const label: Record<Grade, string> = {
    S: "S 核心",
    A: "A 重要",
    B: "B 次要",
    C: "C 突击",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${style[grade]}`}>
      {label[grade]}
    </span>
  );
}

export function WeightStars({ weight }: { weight: number }) {
  return (
    <span className="inline-flex items-center gap-0.5" title={`分值权重 ${weight}/3`}>
      {[1, 2, 3].map((i) => (
        <span
          key={i}
          className={`inline-block h-1.5 w-4 rounded-full ${
            i <= weight ? "bg-brand-500" : "bg-brand-100"
          }`}
        />
      ))}
    </span>
  );
}

const masteryLabel: Record<MasteryGoal, string> = {
  proficient: "熟练",
  understand: "理解",
  aware: "了解",
};

export function MasteryGoalBadge({ goal }: { goal: MasteryGoal }) {
  return (
    <span className="rounded-full border border-brand-200 bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700">
      目标:{masteryLabel[goal]}
    </span>
  );
}

const typeLabel: Record<KnowledgeType, string> = {
  concept: "概念",
  skill: "技能",
  strategy: "策略",
};

export function KnowledgeTypeBadge({ type }: { type: KnowledgeType }) {
  const style: Record<KnowledgeType, string> = {
    concept: "bg-violet-100 text-violet-700",
    skill: "bg-emerald-100 text-emerald-700",
    strategy: "bg-orange-100 text-orange-700",
  };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${style[type]}`}>
      {typeLabel[type]}
    </span>
  );
}

export function DifficultyDots({ difficulty }: { difficulty: number }) {
  return (
    <span className="inline-flex items-center gap-1" title={`难度 ${difficulty}/5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={`inline-block h-2 w-2 rounded-full ${
            i <= difficulty ? "bg-orange-400" : "bg-orange-100"
          }`}
        />
      ))}
    </span>
  );
}

/** SVG 进度环:掌握率可视化,成绩必须有出口(ADR 0052)。 */
export function ProgressRing({
  value,
  size = 44,
  stroke = 5,
  color = "#6D5AE6",
  children,
}: {
  value: number; // 0–1
  size?: number;
  stroke?: number;
  color?: string;
  children?: ReactNode;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(1, value));
  return (
    <span className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#EDEAFB" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - clamped)}
          style={{ transition: "stroke-dashoffset 0.6s cubic-bezier(0.22,1,0.36,1)" }}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-ink/70">
        {children ?? (clamped > 0 ? `${Math.round(clamped * 100)}%` : "")}
      </span>
    </span>
  );
}
