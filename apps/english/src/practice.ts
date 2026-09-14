// 出题与判定：不碰 DOM，只把内容和进度换算成“这一轮该做什么、这次算不算对”。

import type { AttemptStats, Choice, DeckItem, ReviewState, Variant } from "./types";

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
  writing_choice: "写作判断",
  condition: "条件",
  translation: "英译汉",
  listening: "听辨",
  attitude: "态度",
  inference: "推断",
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

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** 句中目标词及其常见屈折（provides / resulted）。 */
export function wordFormPattern(word: string): RegExp {
  return new RegExp(`\\b(${escapeRegExp(word)}[a-z']*)\\b`, "i");
}

export function surfaceForm(word: string, stem?: string): string {
  if (!stem) {
    return word;
  }
  return stem.match(wordFormPattern(word))?.[1] ?? word;
}

export function shuffled<T>(items: T[]): T[] {
  const next = [...items];
  for (let index = next.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(Math.random() * (index + 1));
    [next[index], next[swap]] = [next[swap]!, next[index]!];
  }
  return next;
}

export interface FormProbe {
  sentence: string;
  prompt: string;
  choices: Choice[];
}

/**
 * 单词第二步：用未见（或同一）句子挖空，逼出词形，而不是再认中文。
 * 干扰项取本课其他词在各自例句里的真实屈折，避免原形和第三人称混在一起送分。
 */
export function vocabFormProbe(item: DeckItem, deckItems: DeckItem[]): FormProbe | null {
  const word = item.word;
  if (!word) {
    return null;
  }
  const sentence = item.variants?.[0]?.sentence ?? item.sentence;
  if (!sentence || !wordFormPattern(word).test(sentence)) {
    return null;
  }
  const answer = surfaceForm(word, sentence);
  const seen = new Set([answer.toLowerCase()]);
  const distractors: string[] = [];
  for (const other of shuffled(deckItems)) {
    if (!other.word || other.word === word) {
      continue;
    }
    const label = surfaceForm(other.word, other.sentence);
    if (seen.has(label.toLowerCase())) {
      continue;
    }
    seen.add(label.toLowerCase());
    distractors.push(label);
    if (distractors.length === 3) {
      break;
    }
  }
  if (distractors.length < 2) {
    return null;
  }
  return {
    sentence,
    prompt: "根据句意，空格里应填哪个词？",
    choices: shuffled([
      {
        label: answer,
        ok: true,
        why: `新句仍需要 ${word} 的这个形式。`,
      },
      ...distractors.map((label) => ({
        label,
        ok: false,
        why: `把 ${label} 放进这个空格，搭配或句意对不上。`,
      })),
    ]),
  };
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
 * 组织和用词好不好由作者对照 reference 和 checklist 自己看；这些形式指标只进入
 * 练习记录，不决定阶段资格（ADR 0006）。
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
 * 一条轨的练习现状。passed 来自独立考核；覆盖率、正确率和到期数只描述练习，
 * 两者不能互相冒充（ADR 0006）。
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

/* ------------------------------------------------ 学习成果 */

/** 至少成功复习过一次，不只是见过。 */
export function isHeld(state: ReviewState | undefined): boolean {
  return Boolean(state && state.last_rating !== null && state.last_rating >= 3 && state.reps >= 2);
}

export interface OutcomeTrackInput {
  kind: string;
  stageId: string;
  items: DeckItem[];
  passed: boolean;
}

export interface KindCoverage {
  kind: string;
  title: string;
  total: number;
  seen: number;
  held: number;
  tracksPassed: number;
  tracksTotal: number;
}

export interface OutcomeBadge {
  id: string;
  title: string;
  hint: string;
  earned: boolean;
}

export interface LearningOutcomes {
  attempts: number;
  correct: number;
  accuracy: number | null;
  streak: number;
  activeDays: number;
  seenItems: number;
  heldItems: number;
  practiceTotal: number;
  tracksPassed: number;
  tracksTotal: number;
  stagesPassed: number;
  stagesTotal: number;
  dueToday: number;
  mistakes: number;
  byKind: KindCoverage[];
  badges: OutcomeBadge[];
  cheer: string;
}

const KIND_ORDER = ["vocab", "sentence", "writing"] as const;

export function computeOutcomes(input: {
  stages: Array<{ id: string }>;
  tracks: OutcomeTrackInput[];
  review: Map<string, ReviewState>;
  mistakeCount: number;
  attempts: AttemptStats;
  nowSeconds: number;
}): LearningOutcomes {
  const items = input.tracks.flatMap((track) => track.items);
  const seenItems = items.filter((item) => input.review.has(item.id)).length;
  const heldItems = items.filter((item) => isHeld(input.review.get(item.id))).length;
  const dueToday = items.filter((item) => {
    const state = input.review.get(item.id);
    return state !== undefined && isDue(state, input.nowSeconds);
  }).length;
  const tracksPassed = input.tracks.filter((track) => track.passed).length;
  const tracksByStage = new Map<string, OutcomeTrackInput[]>();
  for (const track of input.tracks) {
    const bucket = tracksByStage.get(track.stageId) ?? [];
    bucket.push(track);
    tracksByStage.set(track.stageId, bucket);
  }
  const stagesPassed = input.stages.filter((stage) => {
    const tracks = tracksByStage.get(stage.id) ?? [];
    return tracks.length > 0 && tracks.every((track) => track.passed);
  }).length;
  const beginnerClear = (tracksByStage.get("en.stage.beginner") ?? []).every(
    (track) => track.passed,
  ) && (tracksByStage.get("en.stage.beginner") ?? []).length > 0;

  const byKind: KindCoverage[] = KIND_ORDER.map((kind) => {
    const tracks = input.tracks.filter((track) => track.kind === kind);
    const kindItems = tracks.flatMap((track) => track.items);
    return {
      kind,
      title: trackKindLabel(kind),
      total: kindItems.length,
      seen: kindItems.filter((item) => input.review.has(item.id)).length,
      held: kindItems.filter((item) => isHeld(input.review.get(item.id))).length,
      tracksPassed: tracks.filter((track) => track.passed).length,
      tracksTotal: tracks.length,
    };
  });

  const badges: OutcomeBadge[] = [
    {
      id: "first-step",
      title: "开了个头",
      hint: "见过第一条练习",
      earned: seenItems >= 1,
    },
    {
      id: "streak-3",
      title: "连练 3 天",
      hint: "连续三天回来做题",
      earned: input.attempts.streak >= 3,
    },
    {
      id: "streak-7",
      title: "连练一周",
      hint: "连续七天回来做题",
      earned: input.attempts.streak >= 7,
    },
    {
      id: "hold-10",
      title: "稳住 10 条",
      hint: "至少成功复习过一次的条目",
      earned: heldItems >= 10,
    },
    {
      id: "hold-30",
      title: "稳住 30 条",
      hint: "间隔复习已经开始起作用",
      earned: heldItems >= 30,
    },
    {
      id: "beginner-clear",
      title: "初级过关",
      hint: "单词、例句、作文考核都过了",
      earned: beginnerClear,
    },
    {
      id: "no-due",
      title: "今日到期清完",
      hint: "练过的条目里没有还在到期的",
      earned: seenItems > 0 && dueToday === 0,
    },
    {
      id: "mistake-tamer",
      title: "错题清仓",
      hint: "见过若干条之后，错题本是空的",
      earned: seenItems >= 5 && input.mistakeCount === 0,
    },
  ];

  return {
    attempts: input.attempts.attempts,
    correct: input.attempts.correct,
    accuracy: input.attempts.attempts === 0 ? null : input.attempts.correct / input.attempts.attempts,
    streak: input.attempts.streak,
    activeDays: input.attempts.active_days,
    seenItems,
    heldItems,
    practiceTotal: items.length,
    tracksPassed,
    tracksTotal: input.tracks.length,
    stagesPassed,
    stagesTotal: input.stages.length,
    dueToday,
    mistakes: input.mistakeCount,
    byKind,
    badges,
    cheer: cheerFor({
      seenItems,
      heldItems,
      dueToday,
      streak: input.attempts.streak,
      stagesPassed,
      beginnerClear,
      mistakes: input.mistakeCount,
    }),
  };
}

function cheerFor(state: {
  seenItems: number;
  heldItems: number;
  dueToday: number;
  streak: number;
  stagesPassed: number;
  beginnerClear: boolean;
  mistakes: number;
}): string {
  if (state.seenItems === 0) {
    return "从今天这一小步开始就行。做对第一题，成果就会出现在这里。";
  }
  if (state.streak >= 7) {
    return `已经连续 ${state.streak} 天回来了。这比一次刷完更值钱。`;
  }
  if (state.streak >= 3) {
    return `已经连续 ${state.streak} 天在练。稳住的条目会留在这里。`;
  }
  if (state.beginnerClear && state.stagesPassed === 1) {
    return "初级三条线都过了。中级可以按同样节奏推进。";
  }
  if (state.stagesPassed >= 2) {
    return `已经过了 ${state.stagesPassed} 个阶段。高级那条线是给英语二任务用的。`;
  }
  if (state.heldItems > 0 && state.dueToday === 0) {
    return `到期的都清完了。已经稳住 ${state.heldItems} 条，继续往前走就行。`;
  }
  if (state.mistakes === 0 && state.seenItems >= 5) {
    return "错题清完了。现有条目都站得住，可以安心推进新的。";
  }
  if (state.dueToday > 0) {
    return `有 ${state.dueToday} 条到期。先把它们清掉，稳住的数字就会再长一点。`;
  }
  return `已经见过 ${state.seenItems} 条。稳住的会留在这里，到期清掉就会继续长。`;
}
