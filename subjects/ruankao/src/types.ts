// 内容契约:与 content/ 下 JSON 一一对应。内容结构变更先改这里再改 JSON。

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
  // lead / text
  text?: string;
  // formula
  latex?: string;
  caption?: string;
  // compare
  title?: string;
  left?: { title: string; body: string };
  right?: { title: string; body: string };
  // steps
  items?: string[];
  // table
  headers?: string[];
  rows?: string[][];
  // code
  code?: string;
  lang?: string;
  // callout
  kind?: "tip" | "warn" | "trap";
  // viz
  component?: string;
  params?: Record<string, unknown>;
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

export interface Chapter {
  id: string;
  title: string;
  weight: 1 | 2 | 3;
  grade: Grade;
  kp: KnowledgePoint;
}

export interface Course {
  id: string;
  title: string;
  tagline: string;
  accent: string;
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

export interface CourseRegistry {
  exam: ExamFacts;
  courses: { id: string; title: string; accent: string }[];
}

export interface ChapterLesson {
  chapter_id: string;
  blocks: Block[];
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

export interface ChapterQuiz {
  chapter_id: string;
  questions: Question[];
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
