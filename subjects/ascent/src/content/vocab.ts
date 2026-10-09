import type { ExamFreqEntry, VocabStages, VocabWord } from "./types";

// 词库与分阶数据（ADR 0022）。stages.json 和词频都很小，随包加载；
// words.json 三个加起来 2.7MB，按档懒加载，进哪个词库才载哪份。

export type BankMeta = { id: string; name: string; blurb: string };

export const VOCAB_BANKS: BankMeta[] = [
  { id: "hs", name: "高中基石", blurb: "高考课标词 · 单词关的上限" },
  { id: "cet4", name: "大学四级", blurb: "四级新增词（不含高中已学的）" },
  { id: "cet6", name: "大学六级", blurb: "六级新增词（不含高中和四级已学的）" },
];

const stageModules = import.meta.glob<VocabStages>("../../content/vocab/*/stages.json", {
  eager: true,
  import: "default",
});
const freqModules = import.meta.glob<{ words: ExamFreqEntry[] }>("../../content/vocab/*/exam-frequency.json", {
  eager: true,
  import: "default",
});
const wordModules = import.meta.glob<{ words: VocabWord[] }>("../../content/vocab/*/words.json", {
  import: "default",
});

function examOf(path: string): string {
  const m = path.match(/vocab\/([\w-]+)\//);
  return m?.[1] ?? "";
}

function pick<T>(modules: Record<string, T>, exam: string): T | undefined {
  return Object.entries(modules).find(([path]) => examOf(path) === exam)?.[1];
}

export function bankStages(exam: string): VocabStages | undefined {
  return pick(stageModules, exam);
}

/** word → { hits, sentences } from the local CET-4 past-paper corpus. */
export function bankFreq(exam: string): Record<string, ExamFreqEntry> {
  const raw = pick(freqModules, exam)?.words ?? [];
  return Object.fromEntries(raw.map((f) => [f.word, f]));
}

const wordCache = new Map<string, Record<string, VocabWord>>();

/** Load one bank's word details (word → entry). Cached after the first call. */
export async function loadWords(exam: string): Promise<Record<string, VocabWord>> {
  const hit = wordCache.get(exam);
  if (hit) return hit;
  const loader = Object.entries(wordModules).find(([path]) => examOf(path) === exam)?.[1];
  if (!loader) throw new Error(`没有找到词库 ${exam}`);
  const raw = await loader();
  const map = Object.fromEntries(raw.words.map((w) => [w.word, w]));
  wordCache.set(exam, map);
  return map;
}
