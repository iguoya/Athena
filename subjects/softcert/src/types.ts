// 内容契约:与 content/ 下 JSON 一一对应。内容结构变更先改这里再改 JSON。
// 两层结构:章(chapter)= 官方教材的章;节(section)= 菜单里的可学习单元。

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
  section_id: string; // 与 Section.id 一致(旧字段名 chapter_id 仍兼容)
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

export interface ExamFacts {
  name: string;
  full_name: string;
  facts: string[];
  passing_score: number;
  full_score: number;
}

export interface CourseEntry {
  id: string;
  title: string;
  accent: string;
  track: string;
  textbook: Textbook;
}

export interface CourseRegistry {
  exam: ExamFacts;
  courses: CourseEntry[];
}

export interface ChapterQuiz {
  section_id: string; // 同上,旧字段名 chapter_id 兼容
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

export interface PastPaperMeta {
  id: string;
  title: string;
  year: number;
  session: string;
  subject: string;
  source_note: string;
}

export interface PastPaperRegistry {
  about: string;
  papers: PastPaperMeta[];
}
