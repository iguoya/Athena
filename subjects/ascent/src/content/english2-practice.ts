// 考研英语二的练习规则（ADR 0024、0025）：纯函数，界面与存储都只调这里，规则有测试守住。

import type { DeckItem, Stage, Track } from "./english2";

/** 一轮练习的题量上限：短回合、有结束页（磨砚 ADR 0010；主仓库 ADR 0113 P6）。 */
export const ROUND_SIZE = 10;
/** 开放作文一轮几篇：一篇要写几分钟，十篇就不是一轮了。 */
export const WRITING_ROUND_SIZE = 3;
/** 考核单轨正确率达到这个比例记通过，通过资格不撤销（ADR 0024）。 */
export const PASS_RATE = 0.8;
/**
 * 连对 n 次后隔几天再复习。本应用的地基是 FSRS（ADR 0014），但 ts-fsrs 还没接进来；
 * 先用连对次数阶梯，FSRS 落地时只换 schedule 一个函数。
 */
export const INTERVALS = [1, 2, 4, 8, 16, 30];

export interface ItemRecord {
  /** 连续答对次数，答错归零。 */
  streak: number;
  /** 下次到期的日期（YYYY-MM-DD）。 */
  due: string;
  seen: number;
  wrong: number;
  last: string;
}

/** 错题：出库要「隔天答对一次」且「做对一条变式」，缺一不出（ADR 0024 第 2 条）。 */
export interface Mistake {
  itemId: string;
  trackId: string;
  opened: string;
  laterDayOk: boolean;
  variantOk: boolean;
}

export function addDays(date: string, days: number): string {
  const d = new Date(`${date}T00:00:00`);
  d.setDate(d.getDate() + days);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export function schedule(rec: ItemRecord | undefined, ok: boolean, today: string): ItemRecord {
  const streak = ok ? (rec?.streak ?? 0) + 1 : 0;
  const gap = ok ? INTERVALS[Math.min(streak, INTERVALS.length) - 1] : 1;
  return {
    streak,
    due: addDays(today, gap),
    seen: (rec?.seen ?? 0) + 1,
    wrong: (rec?.wrong ?? 0) + (ok ? 0 : 1),
    last: today,
  };
}

export const isDue = (rec: ItemRecord | undefined, today: string) => rec !== undefined && rec.due <= today;

/** 一轮：先到期的复习（越早到期越先），再按课表顺序补新题，总数不超过 size。 */
export function buildRound(
  items: DeckItem[],
  records: Record<string, ItemRecord>,
  today: string,
  size = ROUND_SIZE,
): DeckItem[] {
  const due = items
    .filter((item) => isDue(records[item.id], today))
    .sort((a, b) => records[a.id].due.localeCompare(records[b.id].due));
  const fresh = items.filter((item) => !records[item.id]);
  return [...due, ...fresh].slice(0, size);
}

/**
 * 更新一条错题。答错（母题或变式）都会把两个条件清零重来——又错了说明还没稳；
 * 返回 undefined 表示这道题不在（或已出）错题本。
 * 没有变式的题，「做对一条变式」无从谈起，打开时就记为已满足，只看隔天答对。
 */
export function updateMistake(
  current: Mistake | undefined,
  target: { item: DeckItem; trackId: string },
  kind: "item" | "variant",
  ok: boolean,
  today: string,
): Mistake | undefined {
  const noVariant = !target.item.variants?.length;
  if (!ok) {
    return { itemId: target.item.id, trackId: target.trackId, opened: today, laterDayOk: false, variantOk: noVariant };
  }
  if (!current) return undefined;
  const next: Mistake = {
    ...current,
    laterDayOk: current.laterDayOk || (kind === "item" && today > current.opened),
    variantOk: current.variantOk || kind === "variant",
  };
  return next.laterDayOk && next.variantOk ? undefined : next;
}

export interface AssessmentResult {
  correct: number;
  total: number;
  rate: number;
  passed: boolean;
}

/** answers：题目 id → 选中的选项下标；没答的算错。 */
export function scoreAssessment(items: DeckItem[], answers: Record<string, number>): AssessmentResult {
  const correct = items.filter((item) => item.choices?.[answers[item.id]]?.ok).length;
  const rate = items.length ? correct / items.length : 0;
  return { correct, total: items.length, rate, passed: rate >= PASS_RATE };
}

export const wordCount = (text: string) => (text.match(/[A-Za-z]+(?:['’-][A-Za-z]+)*/g) ?? []).length;

export interface WritingCheck {
  words: number;
  enoughWords: boolean;
  /** 用上了 required_any 里的哪一个；没要求时为 null。 */
  connector: string | null;
  connectorOk: boolean;
}

/** 作文只机检字数下限与指定的衔接方式；组织和用词对照范文和清单自查，不进掌握度（磨砚 ADR 0004）。 */
export function checkWriting(text: string, item: DeckItem): WritingCheck {
  const words = wordCount(text);
  const lower = ` ${text.toLowerCase().replace(/\s+/g, " ")} `;
  const required = item.required_any ?? [];
  const hit = required.find((c) => new RegExp(`(^|[^a-z])${c.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}([^a-z]|$)`).test(lower));
  return {
    words,
    enoughWords: words >= (item.min_words ?? 0),
    connector: hit ?? null,
    connectorOk: required.length === 0 || hit !== undefined,
  };
}

/**
 * 单词题答对后用新句挖空写词形（磨砚的「语境先行、答后提取词形」）：取变式里含这个词
 * （含屈折形式）的第一句，把它挖掉；找不到合适的句子返回 null，界面就跳过这一步。
 */
export function clozeFor(item: DeckItem): { before: string; after: string; answer: string } | null {
  if (!item.word) return null;
  const pattern = new RegExp(`\\b(${item.word.replace(/e$/, "")}[a-z]*)\\b`, "i");
  for (const v of item.variants ?? []) {
    const sentence = v.sentence ?? v.text;
    const match = sentence?.match(pattern);
    if (sentence && match?.index !== undefined) {
      return { before: sentence.slice(0, match.index), after: sentence.slice(match.index + match[0].length), answer: match[0] };
    }
  }
  return null;
}

/** 一个等级的三条轨考核都通过，这一级才算通过。 */
export function stagePassed(stage: Stage, passed: (assessment: string) => boolean): boolean {
  return stage.tracks.every((track) => passed(track.assessment));
}

export const isChoiceTrack = (track: Track) => track.kind !== "writing";
