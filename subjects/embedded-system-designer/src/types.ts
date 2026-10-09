// 内容契约:与 content/ 下 JSON 一一对应。内容结构变更先改这里再改 JSON。
// 两层结构:章(chapter)= 官方教材的章;节(section)= 菜单里的可学习单元。
// 与 softcert 的内容契约同构(同一份内容从那里迁来,ADR 0090),但本应用
// 单课程:没有 courses.json 注册表层,course.json 就是根。

export type BlockType =
  | "lead"
  | "text"
  | "formula"
  | "compare"
  | "steps"
  | "table"
  | "code"
  | "callout"
  | "viz";

export interface Block {
  type: BlockType;
  text?: string;
  latex?: string;
  caption?: string;
  title?: string;
  left?: { title: string; body: string };
  right?: { title: string; body: string };
  items?: string[];
  headers?: string[];
  rows?: string[][];
  code?: string;
  lang?: string;
  kind?: "tip" | "warn" | "trap";
  component?: string;
  params?: Record<string, unknown>;
}

export interface ChapterLesson {
  section_id: string;
  blocks: Block[];
}

export type MasteryGoal = "proficient" | "understand" | "aware";
export type KnowledgeType = "concept" | "skill" | "strategy";

export interface KnowledgePoint {
  id: string;
  difficulty: number; // 1–5
  mastery_goal: MasteryGoal;
  knowledge_type: KnowledgeType;
  requires: string[];
  guide_line: string;
}

export type Grade = "S" | "A" | "B" | "C";

/** 节:可学习的最小单元,对应教材里的若干小节。 */
export interface Section {
  id: string;
  title: string;
  weight: 1 | 2 | 3;
  grade: Grade;
  /** 教学内容还没写的节不评级(TEACHING:评级只给已写出内容的章节)。 */
  kp?: KnowledgePoint;
  /** 知识点筛选正则:配置后随堂考核直接使用匹配的历年真题(verbatim)。 */
  past_exam_knowledge?: string;
}

export interface TextbookRef {
  sourceId: string;
  locator: string;
}

/** 章:官方教材的章,菜单分组层。sections 为空的章是「待建」占位。 */
export interface Chapter {
  id: string;
  no: number;
  title: string;
  textbook_ref: TextbookRef;
  note?: string;
  sections: Section[];
}

export interface Textbook {
  id: string;
  title: string;
  publisher: string;
  year: number;
  isbn?: string;
  chapters_total: number;
}

export interface Course {
  id: string;
  title: string;
  tagline: string;
  accent: string;
  track: string;
  textbook: Textbook;
  exam: { subject: string; score_range: string; grade: Grade; note: string };
  chapters: Chapter[];
}

export interface ChapterQuiz {
  section_id: string;
  questions: Question[];
}

export type SourceRef = {
  relation: "authored" | "verbatim" | "quoted" | "adapted";
  sourceId: string;
  why?: string;
  locator?: string;
};

export interface Question {
  id: string;
  stem: string;
  options: string[];
  answer: number;
  explanation: string;
  source: SourceRef;
}

export interface PastExamQuestion {
  id: string;
  no: number;
  stem: string;
  options: string[];
  answer: number;
  explanation: string;
  knowledge: string;
  source: SourceRef;
}

export interface PastPaperFile {
  id: string;
  title: string;
  year: number;
  session: string;
  subject: string;
  source_note: string;
  source_ref: SourceRef;
  questions: PastExamQuestion[];
}

export interface PastPaperRegistry {
  about: string;
  papers: { id: string; title: string; year: number; session: string; subject: string; source_note: string }[];
}

export interface KpSummary {
  kp_id: string;
  total: number;
  correct: number;
  last_at: number;
  streak: number;
}
