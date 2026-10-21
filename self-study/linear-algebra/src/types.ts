// 内容数据的类型：与 content/ 下的 JSON 一一对应。出处字段名与 content-contract.json
// 声明的一致（source_refs / relation / locator / url / note），跨应用检查器按契约扫描。

export type SourceRef = {
  /** 与原材料的关系：verbatim 真题原题；adapted 改编（note 写明改了什么）；authored 自造（note 写明理由） */
  relation: "verbatim" | "adapted" | "authored";
  /** 定位：真题写「全国 YYYY 年 MM 卷 第 N 题」，教材例题写「教材 §x.x 例 N」 */
  locator?: string;
  url?: string;
  note?: string;
};

export type ChoiceAnswer = { type: "choice"; options: string[]; correct: number };
export type NumericAnswer = { type: "numeric"; value: number; tolerance?: number };
export type Answer = ChoiceAnswer | NumericAnswer;

export type KnowledgeId = string;

export type ExerciseBlock = {
  kind: "exercise";
  id: string;
  knowledge: KnowledgeId[];
  stem: string;
  answer: Answer;
  solution: string;
  source_refs: SourceRef[];
  /** 这道题换了什么角度（同一知识点的多道题各指一处理解） */
  varies?: string;
};

/** 节首提取动作：先作答再讲解，出现在一切揭示性内容之前 */
export type RetrievalBlock = {
  kind: "retrieval";
  id: string;
  prompt: string;
  options: string[];
  correct: number;
  explain: string;
  knowledge?: KnowledgeId[];
  source_refs: SourceRef[];
};

export type ProseBlock = { kind: "prose"; text: string };

export type ExampleBlock = {
  kind: "example";
  title: string;
  problem: string;
  steps: { text: string; why?: string }[];
  source_refs?: SourceRef[];
};

export type PitfallBlock = {
  kind: "pitfall";
  wrong: string;
  why_wrong: string;
  right: string;
};

export type FigureBlock = {
  kind: "figure";
  /** content/sections/assets/ 下的文件名 */
  file: string;
  caption: string;
};

export type Block =
  | RetrievalBlock
  | ProseBlock
  | ExampleBlock
  | PitfallBlock
  | ExerciseBlock
  | FigureBlock;

export type SectionMeta = { id: string; no: string; title: string; knowledge: KnowledgeId[] };
export type Chapter = { id: string; no: string; title: string; sections: SectionMeta[] };

export type CourseInfo = {
  id: string;
  title: string;
  /** 课程代码，课改过渡期新旧并记，如「13175 / 02198」 */
  code: string;
  textbook: {
    title: string;
    authors: string;
    press: string;
    year: string;
    note?: string;
  };
  method: { primary: string; secondary: string };
};

export type Curriculum = { course: CourseInfo; chapters: Chapter[] };

export type KnowledgePoint = {
  id: KnowledgeId;
  title: string;
  type: "概念" | "技能" | "策略";
  difficulty: number;
  /** 掌握目标，用考纲动词：了解 / 掌握 / 熟练掌握 */
  target: string;
  requires: KnowledgeId[];
  textbook_ref: string;
  syllabus_ref: string;
};

export type SectionContent = { id: string; blocks: Block[] };
