/** 与 content/curriculum.json、content/demos.json 的结构对应。 */

export interface TranslationRef {
  chapter?: number;
  appendix?: string;
  title: string;
  url?: string;
}

export interface SourceRef {
  relation: "verbatim" | "quoted" | "adapted" | "authored";
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
}

export interface ExperimentEntity extends ManifestEntity {
  skeleton_dir: string;
  acceptance: string;
}

export type Block =
  | { type: "text"; text: string }
  | { type: "code"; lang: string; source: string; caption?: string }
  | { type: "callout"; variant: "note" | "warning" | "tip"; text: string }
  | { type: "simulation"; sim: string; demo_ref?: string; note?: string }
  | { type: "demo"; demo_ref: string; caption?: string }
  | { type: "experiment"; demo_ref: string }
  | ({ type: "observation_quiz"; demo_ref: string } & QuizItem)
  | ({ type: "quiz" } & QuizItem);

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
}

export interface DemoEvent {
  demo_id: string;
  method: string;
  params: Record<string, unknown>;
}
