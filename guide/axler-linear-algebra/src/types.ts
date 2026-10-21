// 内容文件的类型。本书是中文书，讲解文字是纯字符串；题源与出处规则见 AGENTS.md。

export type Block =
  | { k: "p"; t: string }
  | { k: "heading"; level?: number; t: string }
  | { k: "math"; tex: string }
  | { k: "box"; env: string; title: string | null; blocks: Block[] }
  | { k: "solution" | "proof" | "proofof" | "outcome"; title: string | null; blocks: Block[] }
  | { k: "list"; ordered: boolean; items: Block[][] }
  | { k: "code"; text: string }
  | { k: "figure"; id: string; caption: string | null; stage?: number }
  | { k: "def"; name: string; sigs: string[]; stage?: number; blocks: Block[] }
  | { k: "dl"; items: Array<{ term: string; blocks: Block[] }> }
  | { k: "table"; spec: string; rows: string[][] };

export interface SectionData {
  id: string;
  title: string;
  blocks: Block[];
}

export interface CurriculumItem {
  id: string;
  level: number;
  title: string;
  page: boolean;
  /** 该章入库的题目数，由构建脚本生成 */
  exercises?: number;
}

export interface CurriculumChapter {
  id: string;
  title: string;
  items: CurriculumItem[];
}

export interface Curriculum {
  chapters: CurriculumChapter[];
}

/**
 * 原书题目（content/exercises/<章>.json）：题源必须有所本——verbatim（原书原样）或
 * adapted（以原书题为底，注明改动）；locator 给原书印刷页码与题号；authored 默认不入库。
 * 判分只做 choice：证明对错无法机判，判分动作是思路选择与概念辨析，证明本身对照 sol 自评。
 */
export interface Exercise {
  id: string;
  /** 题面：中文，可含 $公式$、`代码`、```围栏代码块``` */
  stem: string;
  /** 参考解答：先自己证明，再展开对照 */
  sol: string;
  check: Check;
  source_refs?: Array<{ relation: string; locator?: string; note?: string }>;
}

/** 一道题的判分动作。 */
export type Check =
  | { kind: "choice"; ask?: string; options: Array<{ text: string; ok?: boolean; why: string }>; hint?: string };

export interface AttemptRow {
  knowledge_id: string;
  item_id: string;
  correct: boolean;
  answered_at: number;
}
