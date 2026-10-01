/*
 * Demo data for the home screen until the SQLite progress store and content packs exist.
 * The sentence of the day is a real, sourced sentence (ADR 0005); every number here is a placeholder.
 */

export type TodaySentence = {
  en: string;
  focus: string;
  cn: string;
  word: { text: string; ipa: string; pos: string; simpleEn: string; cn: string };
  grammar: string;
  source: string;
};

export const sentenceOfTheDay: TodaySentence = {
  en: "Your time is limited, so don't waste it living someone else's life.",
  focus: "waste",
  cn: "你的时间有限，所以不要浪费时间活在别人的生活里。",
  word: {
    text: "waste",
    ipa: "/weɪst/",
    pos: "v.",
    simpleEn: "to use something badly, or to use it for nothing useful",
    cn: "浪费",
  },
  grammar: "非谓语动词：waste it living …",
  source: "Steve Jobs，斯坦福大学毕业典礼演讲，2005",
};

export type Step = "read" | "write" | "listen" | "speak" | "review";

export type Task = {
  id: string;
  step: Step;
  title: string;
  detail: string;
  optional?: boolean;
  done: boolean;
};

export const initialTasks: Task[] = [
  {
    id: "read",
    step: "read",
    title: "读 · 今日句组",
    detail: "6 个真实句子，点不认识的词收进生词本",
    done: false,
  },
  { id: "write", step: "write", title: "写 · 仿写 2 句", detail: "用今天的句式写你自己的宿舍生活", done: false },
  { id: "listen", step: "listen", title: "听 · 逐句听写", detail: "听今天的 6 句，边听边写", done: false },
  { id: "review", step: "review", title: "复习 · 换句填空", detail: "12 个词，每个都换一个新的真实句子", done: false },
  {
    id: "speak",
    step: "speak",
    title: "说 · 跟读",
    detail: "鼓励项，可以小声跟读，也可以跳过",
    optional: true,
    done: false,
  },
];

export type UnitState = "lit" | "learning" | "locked";

/**
 * Demo mastery for the chapter-1 map until diagnosis + review cards write real progress.
 * States follow ADR 0017: diagnosis can light a unit; finishing a unit unlocks its review card.
 */
export const unitStates: Record<string, UnitState> = {
  tense: "lit",
  passive: "lit",
  nonfinite: "learning",
  relative: "locked",
  "noun-clause": "locked",
  adverbial: "locked",
  modal: "locked",
  subjunctive: "locked",
  inversion: "locked",
  emphasis: "locked",
};

/** Sample sentences she "wrote correctly" for lit units — UI placeholders until writing is live. */
export const demoMySentences: Record<string, string> = {
  tense: "I finish my homework before dinner every day.",
  passive: "Our dorm was cleaned by everyone last Sunday.",
};

export const weekMinutes = [
  { day: "四", minutes: 18 },
  { day: "五", minutes: 26 },
  { day: "六", minutes: 12 },
  { day: "日", minutes: 31 },
  { day: "一", minutes: 22 },
  { day: "二", minutes: 28 },
  { day: "今", minutes: 24 },
];

export const streakDays = 12;

export const bestSentence = {
  en: "My roommates and I spent the whole evening decorating our dorm.",
  note: "这是你本周写得最好的一句：spent … decorating 用对了非谓语。",
};
