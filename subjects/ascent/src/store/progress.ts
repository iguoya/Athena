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

type ProgressState = {
  words: CollectedWord[];
  /** date (YYYY-MM-DD) → ids of the sentence sets she finished reading that day. */
  readSets: Record<string, string[]>;
  toggleWord: (w: Omit<CollectedWord, "key" | "addedAt">) => void;
  hasWord: (word: string, sentenceId: string) => boolean;
  markSetRead: (setId: string) => void;
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
    }),
    { name: "lumi-progress" },
  ),
);
