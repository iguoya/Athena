// 内容文件的类型。底本是一门中文视频课（课件 + 程序集为文本底本），讲解文字是纯字符串；题源与出处规则见 AGENTS.md。

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
  | { k: "table"; spec: string; rows: string[][] }
  /** 看前提示：看到 at 处先暂停想一想（播放档位 ① 的手动版暂停点，不判分、不进掌握度） */
  | { k: "prewatch"; at?: string; t: string }
  /** 课件段落：一页（或几页）课件的精读，locator = 课件文件 + 页码；start/end 是该段在视频里的起止秒 */
  | { k: "slide"; deck: string; page: string; start?: number; end?: number; title?: string; blocks: Block[] }
  /** 看完不回看、先自答再展开参考答案（教学动作，不判分） */
  | { k: "recall"; q: string; a: string };

/** 一节课（对应课程页大纲里的一小节）。video 只是外链，应用不内嵌、不下载视频（ADR 0180 档位 ①）。 */
export interface Lesson {
  week: number;
  no: number;
  /** 课程页大纲里这一节的原标题 */
  outline_title: string;
  /** 该节在视频平台的外链；拿不到就省略 */
  video_url?: string;
  /** 视频时长（秒），未核对就省略 */
  duration?: number;
}

export interface SectionData {
  id: string;
  title: string;
  lesson?: Lesson;
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
 * adapted（以原书题为底，注明改动）；locator 给页码与题号/例题号；authored 默认不入库。
 */
export interface Exercise {
  id: string;
  /** 题面：中文，可含 $公式$、`代码`、```围栏代码块``` */
  stem: string;
  /** 参考解答：先自己在 Octave 里做，再展开 */
  sol: string;
  check: Check;
  /** Octave 复算代码：把答案算进 result，check.py 在装有 Octave 时复跑核对 answer */
  verify?: string;
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

/** 作答记录里 knowledge_id 的前缀（ADR 0180）：knowledge_id = 前缀 + 节 id，如 chenmooc.w1s1。 */
export const KID_PREFIX = "chenmooc.";
