// 轻量 UI 小件:徽章与指示条。函数式组件(h 渲染)足够,不各开 SFC。
import { h, type PropType } from "vue";
import type { Grade, KnowledgeType, MasteryGoal } from "../types";

/** 分值档位:S 核心 / A 重要 / B 次要 / C 突击 */
export const GradeBadge = defineBadge({
  grade: {
    S: "bg-rose-100 text-rose-700 border-rose-200",
    A: "bg-amber-100 text-amber-700 border-amber-200",
    B: "bg-sky-100 text-sky-700 border-sky-200",
    C: "bg-slate-100 text-slate-600 border-slate-200",
  } as Record<Grade, string>,
  label: {
    S: "S 核心",
    A: "A 重要",
    B: "B 次要",
    C: "C 突击",
  } as Record<Grade, string>,
});

type BadgeDef = { grade: Record<string, string>; label: Record<string, string> };

function defineBadge(def: BadgeDef) {
  return {
    props: { value: { type: String as PropType<Grade>, required: true } },
    setup(props: { value: Grade }) {
      return () =>
        h(
          "span",
          {
            class: `inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${def.grade[props.value] ?? ""}`,
          },
          def.label[props.value] ?? props.value,
        );
    },
  };
}

export const MasteryGoalBadge = {
  props: { goal: { type: String as PropType<MasteryGoal>, required: true } },
  setup(props: { goal: MasteryGoal }) {
    const label: Record<MasteryGoal, string> = {
      proficient: "熟练",
      understand: "理解",
      aware: "了解",
    };
    return () =>
      h(
        "span",
        {
          class:
            "rounded-full border px-2.5 py-0.5 text-xs font-medium",
          style: { borderColor: "var(--tk-line)", background: "var(--tk-accent-soft)", color: "var(--tk-accent-deep)" },
        },
        `目标:${label[props.goal]}`,
      );
  },
};

export const KnowledgeTypeBadge = {
  props: { type: { type: String as PropType<KnowledgeType>, required: true } },
  setup(props: { type: KnowledgeType }) {
    const label: Record<KnowledgeType, string> = {
      concept: "概念",
      skill: "技能",
      strategy: "策略",
    };
    const style: Record<KnowledgeType, string> = {
      concept: "bg-violet-100 text-violet-700",
      skill: "bg-emerald-100 text-emerald-700",
      strategy: "bg-orange-100 text-orange-700",
    };
    return () =>
      h("span", { class: `rounded-full px-2.5 py-0.5 text-xs font-medium ${style[props.type]}` }, label[props.type]);
  },
};

export const WeightStars = {
  props: { weight: { type: Number, required: true } },
  setup(props: { weight: number }) {
    return () =>
      h(
        "span",
        { class: "inline-flex items-center gap-0.5", title: `分值权重 ${props.weight}/3` },
        [1, 2, 3].map((i) =>
          h("span", {
            key: i,
            class: "inline-block h-1.5 w-4 rounded-full",
            style: { background: i <= props.weight ? "var(--tk-accent)" : "color-mix(in srgb, var(--tk-accent) 18%, white)" },
          }),
        ),
      );
  },
};

export const DifficultyDots = {
  props: { difficulty: { type: Number, required: true } },
  setup(props: { difficulty: number }) {
    return () =>
      h(
        "span",
        { class: "inline-flex items-center gap-1", title: `难度 ${props.difficulty}/5` },
        [1, 2, 3, 4, 5].map((i) =>
          h("span", {
            key: i,
            class: `inline-block h-2 w-2 rounded-full ${i <= props.difficulty ? "bg-orange-400" : "bg-orange-100"}`,
          }),
        ),
      );
  },
};
