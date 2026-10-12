import { create } from "zustand";
import { persist } from "zustand/middleware";

export type CollectedWord = {
  key: string;
  word: string;
  simpleEn?: string;
  cn?: string;
  sentenceId: string;
  sentence: string;
  addedAt: number;
};

/** One milestone the learner reached, e.g. finishing a vocab stage (ADR 0022). */
export type Milestone = { id: string; at: string };

type ProgressState = {
  words: CollectedWord[];
  /** date (YYYY-MM-DD) → ids of the sentence sets she finished reading that day. */
  readSets: Record<string, string[]>;
  /** date (YYYY-MM-DD) → words she studied that day (lower-case, deduplicated). ADR 0052: activity is recorded, mastery is not claimed. */
  seenWords: Record<string, string[]>;
  /** Milestones reached so far, e.g. "stage:hs-01". */
  milestones: Milestone[];
  toggleWord: (w: Omit<CollectedWord, "key" | "addedAt">) => void;
  hasWord: (word: string, sentenceId: string) => boolean;
  markSetRead: (setId: string) => void;
  markWordSeen: (word: string) => void;
  markStageComplete: (stageId: string) => void;
  hasMilestone: (id: string) => boolean;
};

export function dateKey(d = new Date()) {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

const wordKey = (word: string, sentenceId: string) => `${word.toLowerCase()}@${sentenceId}`;

// Interim store in localStorage; it moves into SQLite behind the same actions (ADR 0002 / 0010).
export const useProgress = create<ProgressState>()(
  persist(
    (set, get) => ({
      words: [],
      readSets: {},
      seenWords: {},
      milestones: [],
      toggleWord: (w) =>
        set((s) => {
          const key = wordKey(w.word, w.sentenceId);
          return s.words.some((x) => x.key === key)
            ? { words: s.words.filter((x) => x.key !== key) }
            : { words: [...s.words, { ...w, key, addedAt: Date.now() }] };
        }),
      hasWord: (word, sentenceId) => get().words.some((x) => x.key === wordKey(word, sentenceId)),
      markSetRead: (setId) =>
        set((s) => {
          const today = dateKey();
          const done = s.readSets[today] ?? [];
          return done.includes(setId) ? s : { readSets: { ...s.readSets, [today]: [...done, setId] } };
        }),
      markWordSeen: (word) =>
        set((s) => {
          const key = word.trim().toLowerCase();
          if (!key) return s;
          const today = dateKey();
          const list = s.seenWords[today] ?? [];
          return list.includes(key) ? s : { seenWords: { ...s.seenWords, [today]: [...list, key] } };
        }),
      markStageComplete: (stageId) =>
        set((s) => {
          const id = `stage:${stageId}`;
          return s.milestones.some((m) => m.id === id) ? s : { milestones: [...s.milestones, { id, at: dateKey() }] };
        }),
      hasMilestone: (id) => get().milestones.some((m) => m.id === id),
    }),
    { name: "lumi-progress" },
  ),
);

// ── 派生统计（ADR 0052：激励只展示由这些记录派生的量） ──

/** Every word she has ever studied, lower-cased. */
export function allSeenWords(words: Record<string, string[]>): Set<string> {
  const out = new Set<string>();
  for (const list of Object.values(words)) for (const w of list) out.add(w);
  return out;
}

function dayActive(p: { seenWords: Record<string, string[]>; readSets: Record<string, string[]> }, day: string) {
  return (p.seenWords[day]?.length ?? 0) > 0 || (p.readSets[day]?.length ?? 0) > 0;
}

/** Consecutive active days ending today (or yesterday, so a morning check-in keeps yesterday's streak). */
export function streakDays(p: { seenWords: Record<string, string[]>; readSets: Record<string, string[]> }): number {
  const day = (offset: number) => {
    const d = new Date();
    d.setDate(d.getDate() - offset);
    return dateKey(d);
  };
  const start = dayActive(p, day(0)) ? 0 : dayActive(p, day(1)) ? 1 : -1;
  if (start < 0) return 0;
  let n = 0;
  for (let offset = start; dayActive(p, day(offset)); offset++) n++;
  return n;
}

/** The last 7 days, oldest first, with the count of studied words per day. */
export function weekActivity(p: { seenWords: Record<string, string[]>; readSets: Record<string, string[]> }) {
  const out: { day: string; label: string; count: number; isToday: boolean }[] = [];
  const labels = ["日", "一", "二", "三", "四", "五", "六"];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const key = dateKey(d);
    out.push({
      day: key,
      label: i === 0 ? "今" : labels[d.getDay()],
      count: (p.seenWords[key]?.length ?? 0) + (p.readSets[key]?.length ?? 0) * 6,
      isToday: i === 0,
    });
  }
  return out;
}
