/** 与 content/curriculum.json、content/demos.json 的结构对应。 */

export interface TranslationRef {
  chapter?: number;
  appendix?: string;
  title: string;
  url?: string;
}

export interface SourceRef {
  relation: "verbatim" | "quoted" | "adapted" | "authored" | "upstream";
  source_id?: string;
  url?: string;
  locator?: string;
  note?: string;
}

export interface QuizItem {
  id?: string;
  stem: string;
  options: string[];
  answer: number;
  source_refs: SourceRef[];
  /** 题干附带的代码（读代码预测/找错题），按 lang 高亮；缺省 cpp */
  code?: string;
  lang?: string;
  /** 答后显示的解析：为什么对、为什么另几项不对，并指向原文节（应用 ADR 0011） */
  explanation?: string;
}

export interface ExperimentEntity extends ManifestEntity {
  skeleton_dir: string;
  acceptance: string;
}

/** 官方示例（exercise/ 的原样镜像，应用 ADR 0006）：锚定教程章与节。 */
export interface ExampleEntity {
  id: string;
  title: string;
  purpose: string;
  source_dir: string;
  build_target: string;
  /** 所属教程章（章级过滤用；正文链接的示例再由 page_ref 锚到节） */
  translation_ref: TranslationRef;
  /** 锚定的官方节页 id；缺省 = 章级示例，显示在本章各节尾部 */
  page_ref?: string;
  note?: string;
  source_refs: SourceRef[];
}

export type Block =
  | { type: "text"; text: string }
  | { type: "code"; lang: string; source: string; caption?: string }
  | { type: "callout"; variant: "note" | "warning" | "tip"; text: string }
  | { type: "simulation"; sim: string; demo_ref?: string; note?: string }
  | { type: "demo"; demo_ref: string; caption?: string }
  | { type: "experiment"; demo_ref: string }
  | ({ type: "observation_quiz"; demo_ref: string; page_ref?: string } & QuizItem)
  | ({ type: "quiz"; page_ref?: string } & QuizItem);

export interface KnowledgePoint {
  id: string;
  title: string;
  type: "concept" | "skill" | "strategy";
  difficulty: number;
  mastery_goal: "master" | "required" | "familiar" | "";
  requires: string[];
  blocks: Block[];
}

export interface SectionPage {
  id: string;
  title: string;
  /** 英文原名（正文页头显示；侧栏菜单保持中文） */
  title_en?: string;
  status: "pending" | "translated";
}

export interface Section {
  id: string;
  order: number;
  title: string;
  status: "pending" | "translated";
  translation_ref: TranslationRef;
  /** 官方分页（严格跟随上游 DocBook 的节划分，应用 ADR 0002）。 */
  pages: SectionPage[];
  knowledge_points: KnowledgePoint[];
  checkpoint: QuizItem[];
  /** 测验标准版本；2 = 已按 ADR 0011 重做（check 强制解析、答案位与代码题配比） */
  quiz_standard?: number;
}

export interface ReferenceEntry {
  id: string;
  title: string;
  kind: string;
  status: "pending" | "translated";
  translation_ref: TranslationRef;
  note?: string;
}

export interface LabGroup {
  id: string;
  title: string;
  experiments: string[];
}

export interface Labs {
  groups: LabGroup[];
}

export interface Curriculum {
  version: number;
  title: string;
  book: { title: string; author: string; url: string; license: string };
  sections: Section[];
  reference: ReferenceEntry[];
  labs?: Labs;
}

export interface ManifestEntity {
  id: string;
  title: string;
  purpose: string;
  theory_refs: string[];
  source_dir: string;
  build_target: string;
  translation_ref: TranslationRef;
  source_refs: SourceRef[];
}

export interface Manifest {
  version: number;
  demos: ManifestEntity[];
  experiments: ExperimentEntity[];
  examples?: ExampleEntity[];
}

export interface DemoEvent {
  demo_id: string;
  method: string;
  params: Record<string, unknown>;
}

export interface AttemptRow {
  knowledge_id: string;
  item_id: string;
  correct: boolean;
  answered_at: number;
}
