// 内容快照的类型（scripts/sync_upstream.py 的输出）。

export interface Unit {
  en: string;
  sha: string;
  zh: string;
  stale_zh?: string;
}

export type Block =
  | { k: "p"; t: Unit }
  | { k: "heading"; t: Unit }
  | { k: "math"; tex: string }
  | { k: "box"; env: string; title: Unit | null; blocks: Block[] }
  | { k: "solution" | "proof" | "proofof" | "outcome"; title: Unit | null; blocks: Block[] }
  | { k: "list"; ordered: boolean; items: Block[][] }
  | { k: "code"; text: string }
  | { k: "table"; spec: string; rows: Array<Array<Unit | string>> };

export interface SectionData {
  id: string;
  title_en: string;
  title_zh: string;
  blocks: Block[];
}

export interface CurriculumItem {
  id: string;
  level: number;
  title_zh: string;
  title_en: string;
  page: boolean;
  units?: number;
  translated?: number;
  exercises?: number;
}

export interface CurriculumChapter {
  id: string;
  title_en: string;
  title_zh: string;
  items: CurriculumItem[];
}

export interface Curriculum {
  chapters: CurriculumChapter[];
}

/** 自编练习（content/exercises/<节>.json，手写）：题面、一个可机器判的最终答案、参考做法。 */
export interface Exercise {
  id: string;
  /** 题面：中文，可含 $公式$、`代码`、```围栏代码块``` */
  stem: string;
  /** 参考做法：先自己在工具里做，再展开 */
  sol: string;
  check: Check;
  source_refs?: Array<{ relation: string; locator?: string; note?: string }>;
}

/** 一道题的最终答案，可机器判。 */
export type Check =
  | { kind: "numbers"; ask: string; answer: number[]; hint?: string }
  | { kind: "choice"; ask?: string; options: Array<{ text: string; ok?: boolean; why: string }>; hint?: string };

export interface AttemptRow {
  knowledge_id: string;
  item_id: string;
  correct: boolean;
  answered_at: number;
}
