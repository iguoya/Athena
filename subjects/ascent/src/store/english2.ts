import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { DeckItem } from "@/content/english2";
import { schedule, updateMistake, type AssessmentResult, type ItemRecord, type Mistake } from "@/content/english2-practice";
import { dateKey } from "./progress";

export interface AssessmentRecord {
  best: number;
  /** 一旦通过就不撤销（ADR 0024）：之后考差了也不收回。 */
  passed: boolean;
  attempts: number;
  at: string;
}

type English2State = {
  /** 题目 id → 复习排期。掌握度只由作答写入，没有「标记熟练」（主仓库 ADR 0052）。 */
  records: Record<string, ItemRecord>;
  mistakes: Record<string, Mistake>;
  /** 考核题库路径 → 成绩。 */
  assessments: Record<string, AssessmentRecord>;
  /** 日期 → 当天作答题数（首页与本页的统计都由记录派生）。 */
  answered: Record<string, number>;
  /** 写过的开放作文：只记写过、写了多少词，不进掌握度（磨砚 ADR 0004）。 */
  writings: Record<string, { at: string; words: number }>;
  answer: (item: DeckItem, trackId: string, ok: boolean) => void;
  answerVariant: (item: DeckItem, trackId: string, ok: boolean) => void;
  submitAssessment: (path: string, result: AssessmentResult) => void;
  saveWriting: (itemId: string, words: number) => void;
};

function withMistake(mistakes: Record<string, Mistake>, id: string, next: Mistake | undefined) {
  const out = { ...mistakes };
  if (next) out[id] = next;
  else delete out[id];
  return out;
}

const bump = (answered: Record<string, number>, today: string) => ({ ...answered, [today]: (answered[today] ?? 0) + 1 });

// 与 progress.ts 同一个过渡做法：先存 localStorage，以后随学习记录一起搬进 SQLite。
export const useEnglish2Progress = create<English2State>()(
  persist(
    (set) => ({
      records: {},
      mistakes: {},
      assessments: {},
      answered: {},
      writings: {},
      answer: (item, trackId, ok) =>
        set((s) => {
          const today = dateKey();
          return {
            records: { ...s.records, [item.id]: schedule(s.records[item.id], ok, today) },
            mistakes: withMistake(s.mistakes, item.id, updateMistake(s.mistakes[item.id], { item, trackId }, "item", ok, today)),
            answered: bump(s.answered, today),
          };
        }),
      answerVariant: (item, trackId, ok) =>
        set((s) => {
          const today = dateKey();
          return {
            mistakes: withMistake(
              s.mistakes,
              item.id,
              updateMistake(s.mistakes[item.id], { item, trackId }, "variant", ok, today),
            ),
            answered: bump(s.answered, today),
          };
        }),
      submitAssessment: (path, result) =>
        set((s) => {
          const prev = s.assessments[path];
          return {
            assessments: {
              ...s.assessments,
              [path]: {
                best: Math.max(prev?.best ?? 0, result.rate),
                passed: (prev?.passed ?? false) || result.passed,
                attempts: (prev?.attempts ?? 0) + 1,
                at: dateKey(),
              },
            },
          };
        }),
      saveWriting: (itemId, words) =>
        set((s) => ({ writings: { ...s.writings, [itemId]: { at: dateKey(), words } } })),
    }),
    { name: "ascent-english2" },
  ),
);
