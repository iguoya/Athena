// 轻量 UI 小件:徽章与指示条。
import type { Grade, KnowledgeType, MasteryGoal } from "../types";
import { cn } from "@/lib/utils";

/** 分值档位:S 核心 / A 重要 / B 次要 / C 突击 */
const GRADE_STYLE: Record<Grade, string> = {
  S: "bg-rose-100 text-rose-700 border-rose-200",
  A: "bg-amber-100 text-amber-700 border-amber-200",
  B: "bg-sky-100 text-sky-700 border-sky-200",
  C: "bg-slate-100 text-slate-600 border-slate-200",
};
const GRADE_LABEL: Record<Grade, string> = {
  S: "S 核心",
  A: "A 重要",
  B: "B 次要",
  C: "C 突击",
};

export function GradeBadge({ value }: { value: Grade }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        GRADE_STYLE[value],
      )}
    >
      {GRADE_LABEL[value] ?? value}
    </span>
  );
}

const MASTERY_LABEL: Record<MasteryGoal, string> = {
  proficient: "熟练",
  understand: "理解",
  aware: "了解",
};

export function MasteryGoalBadge({ goal }: { goal: MasteryGoal }) {
  return (
    <span
      className="rounded-full border px-2.5 py-0.5 text-xs font-medium"
      style={{
        borderColor: "var(--tk-line)",
        background: "var(--tk-accent-soft)",
        color: "var(--tk-accent-deep)",
      }}
    >
      {`目标:${MASTERY_LABEL[goal]}`}
    </span>
  );
}

const TYPE_LABEL: Record<KnowledgeType, string> = {
  concept: "概念",
  skill: "技能",
  strategy: "策略",
};
const TYPE_STYLE: Record<KnowledgeType, string> = {
  concept: "bg-violet-100 text-violet-700",
  skill: "bg-emerald-100 text-emerald-700",
  strategy: "bg-orange-100 text-orange-700",
};

export function KnowledgeTypeBadge({ type }: { type: KnowledgeType }) {
  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", TYPE_STYLE[type])}>
      {TYPE_LABEL[type]}
    </span>
  );
}

export function WeightStars({ weight }: { weight: number }) {
  return (
    <span className="inline-flex items-center gap-0.5" title={`分值权重 ${weight}/3`}>
      {[1, 2, 3].map((i) => (
        <span
          key={i}
          className="inline-block h-1.5 w-4 rounded-full"
          style={{
            background:
              i <= weight
                ? "var(--tk-accent)"
                : "color-mix(in srgb, var(--tk-accent) 18%, white)",
          }}
        />
      ))}
    </span>
  );
}

export function DifficultyDots({ difficulty }: { difficulty: number }) {
  return (
    <span className="inline-flex items-center gap-1" title={`难度 ${difficulty}/5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={cn(
            "inline-block h-2 w-2 rounded-full",
            i <= difficulty ? "bg-orange-400" : "bg-orange-100",
          )}
        />
      ))}
    </span>
  );
}
