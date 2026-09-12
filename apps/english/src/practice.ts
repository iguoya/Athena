// 出题与判定：不碰 DOM，只把内容和进度换算成“这一轮该做什么、这次算不算对”。

import type { Deck, DeckItem, ReviewState, Variant } from "./types";

const TRACK_KIND_LABEL: Record<string, string> = {
  vocab: "词",
  sentence: "句子",
  passage: "短文",
  writing: "作文",
};

const ITEM_KIND_LABEL: Record<string, string> = {
  cause: "因果",
  contrast: "转折",
  reference: "指代",
  clause_split: "切分",
  main_idea: "主旨",
  detail: "细节",
  vocab_in_passage: "文中词",
  guided_writing: "写作",
};

export function trackKindLabel(kind: string): string {
  return TRACK_KIND_LABEL[kind] ?? kind;
}

export function itemKindLabel(kind: string | undefined): string {
  if (!kind) {
    return "";
  }
  return ITEM_KIND_LABEL[kind] ?? kind;
}

/** 词卡给例句，句子和短文题给原句；写作题没有例句。 */
export function itemStem(source: DeckItem | Variant): string | undefined {
  return source.sentence ?? source.text;
}

/** 错题本的归类标签：内容没写 error_tag 就退回题型，再退回这一轨的类型。 */
export function errorTagOf(item: DeckItem, deckKind: string): string {
  return item.error_tag || itemKindLabel(item.kind) || trackKindLabel(deckKind);
}

/** 侧栏一行摘要：词看词形，句子看原句，写作看题干。 */
export function itemSummary(item: DeckItem): string {
  const text = item.word ?? itemStem(item) ?? item.prompt;
  return text.length > 42 ? `${text.slice(0, 42)}…` : text;
}

export function dueAtOf(review: ReviewState | undefined): number | null {
  if (!review) {
    return null;
  }
  const seconds = Number(review.due_at);
  return Number.isFinite(seconds) ? seconds : null;
}

/** 没做过的和已到期的都算“今天该练”。 */
export function isDue(review: ReviewState | undefined, nowSeconds: number): boolean {
  const due = dueAtOf(review);
  return due === null || due <= nowSeconds;
}

/**
 * 到期检索排在推进新内容之前（课表 lead 的要求），同一组内保持作者写的顺序：
 * 先答错待清的，再没做过的，最后已经做对且没到期的。
 */
export function orderItems(
  items: DeckItem[],
  review: Map<string, ReviewState>,
  nowSeconds: number,
): DeckItem[] {
  const rank = (item: DeckItem): number => {
    const state = review.get(item.id);
    if (!state) {
      return 1;
    }
    if (state.last_rating !== null && state.last_rating < 3) {
      return 0;
    }
    return isDue(state, nowSeconds) ? 1 : 2;
  };
  return items
    .map((item, index) => ({ item, index, rank: rank(item) }))
    .sort((a, b) => a.rank - b.rank || a.index - b.index)
    .map((entry) => entry.item);
}

export interface WritingGrade {
  correct: boolean;
  words: number;
  minWords: number;
  required: string[];
  usedRequired: string[];
  lengthOk: boolean;
  keywordOk: boolean;
}

function countWords(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

function usesWord(text: string, keyword: string): boolean {
  const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(^|[^a-z])${escaped}([^a-z]|$)`, "i").test(text);
}

/**
 * 写作只判可机检的两件事：够不够长、有没有用上要求的连接方式。
 * 组织和用词好不好由作者对照 reference 和 checklist 自己看，不进掌握度（ADR 0001 第 5 条）。
 */
export function gradeWriting(item: DeckItem, text: string): WritingGrade {
  const minWords = item.min_words ?? 0;
  const required = item.required_any ?? [];
  const words = countWords(text);
  const usedRequired = required.filter((keyword) => usesWord(text, keyword));
  const lengthOk = words >= minWords;
  const keywordOk = required.length === 0 || usedRequired.length > 0;
  return {
    correct: lengthOk && keywordOk,
    words,
    minWords,
    required,
    usedRequired,
    lengthOk,
    keywordOk,
  };
}

export function writingVerdict(grade: WritingGrade): string {
  const parts: string[] = [];
  parts.push(
    grade.lengthOk
      ? `字数 ${grade.words}，达到 ${grade.minWords} 词的下限。`
      : `字数 ${grade.words}，还差 ${grade.minWords - grade.words} 词。`,
  );
  if (grade.required.length > 0) {
    parts.push(
      grade.keywordOk
        ? `用上了要求的 ${grade.usedRequired.join(" / ")}。`
        : `还没用上 ${grade.required.join(" / ")} 中的任何一个。`,
    );
  }
  return parts.join("");
}

/* ------------------------------------------------ 轨道状态与组卷 */

export interface TrackStats {
  total: number;
  done: number;
  fresh: number;
  coverage: number;
  accuracy: number | null;
  /** 只数练过又到期的，没做过的算新内容不算复习 */
  due: number;
  weakTag: string | null;
  passed: boolean;
}

/**
 * 一条轨的现状。达标沿用 Rust 侧按 topic 算出的 mastery——它本来就是每条轨
 * 单独判定（做全 + 近期正确率 ≥ 80%），不是三轨平均，不会用总分掩盖短板。
 */
export function trackStats(
  items: DeckItem[],
  review: Map<string, ReviewState>,
  mistakes: Array<{ topic_id: string; error_tag: string }>,
  topicId: string,
  passed: boolean,
  nowSeconds: number,
): TrackStats {
  const states = items.map((item) => review.get(item.id));
  const done = states.filter((state) => state !== undefined).length;
  const good = states.filter((state) => state && state.last_rating !== null && state.last_rating >= 3).length;
  const due = states.filter((state) => state !== undefined && isDue(state, nowSeconds)).length;

  const tally = new Map<string, number>();
  for (const mistake of mistakes) {
    if (mistake.topic_id === topicId) {
      tally.set(mistake.error_tag, (tally.get(mistake.error_tag) ?? 0) + 1);
    }
  }
  let weakTag: string | null = null;
  let best = 0;
  for (const [tag, count] of tally) {
    if (count > best) {
      weakTag = tag;
      best = count;
    }
  }

  return {
    total: items.length,
    done,
    fresh: items.length - done,
    coverage: items.length === 0 ? 0 : done / items.length,
    accuracy: done === 0 ? null : good / done,
    due,
    weakTag,
    passed,
  };
}

/** 只挑还没做对的：答错过的排最前，其次没做过的，再次到期的。 */
export function weakItems(
  items: DeckItem[],
  review: Map<string, ReviewState>,
  nowSeconds: number,
): DeckItem[] {
  return orderItems(items, review, nowSeconds).filter((item) => {
    const state = review.get(item.id);
    return !state || (state.last_rating !== null && state.last_rating < 3) || isDue(state, nowSeconds);
  });
}

/**
 * 组一套考核题。写作一次只考一题（写一段就够长了），其余轨最多八题。
 * 优先没做过或上次答错的，凑不满再按原序补——用的是同一份题库，
 * 所以界面上要说清楚这是成套作答、交卷后统一反馈，不是独立的未见题库。
 */
export function examItems(deck: Deck, review: Map<string, ReviewState>, nowSeconds: number): DeckItem[] {
  const cap = deck.kind === "writing" ? 1 : Math.min(8, deck.items.length);
  const priority = weakItems(deck.items, review, nowSeconds);
  const rest = deck.items.filter((item) => !priority.includes(item));
  return [...priority, ...rest].slice(0, cap);
}
