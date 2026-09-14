// 内容模型与后端返回类型。字段名对齐 content/ 下的 JSON 和 src-tauri 的 serde 结构，
// 前端不另造一套命名。

export interface Choice {
  label: string;
  ok: boolean;
  why?: string;
}

export type SourceRelation = "selection_basis" | "quoted" | "adapted" | "exam_alignment";

/** 内容不是只写一个链接：还要说明它与来源是什么关系。 */
export interface SourceReference {
  source_id: string;
  relation: SourceRelation;
  note: string;
  /** 具体到句子、篇目或习题页的定位；缺省时使用来源目录中的网址。 */
  locator_url?: string;
  locator?: string;
}

export interface ContentSource {
  id: string;
  kind: "corpus" | "course" | "article" | "framework" | "exam_specification";
  title: string;
  publisher: string;
  url: string;
  license: string;
  license_url?: string;
  checked_on: string;
  usage_note: string;
  /** 仓库内对照副本，写题时离线打开（ADR 0008）。 */
  local_path?: string;
}

export interface SourceCatalog {
  sources: ContentSource[];
}

export interface MediaAsset {
  kind: "audio" | "video";
  title: string;
  url: string;
  source_id: string;
  transcript?: string;
}

export interface Sense {
  pos: string;
  gloss: string;
}

/** 变式：同一知识点换一句话再问一次，用于把错题清出错题本。 */
export interface Variant {
  sentence?: string;
  text?: string;
  prompt: string;
  choices: Choice[];
}

export interface DeckItem {
  id: string;
  kind?: string;
  error_tag?: string;
  prompt: string;

  /** 词卡 */
  word?: string;
  senses?: Sense[];
  sentence?: string;

  /** 句子 / 短文题 */
  text?: string;
  vocab?: string[];

  choices?: Choice[];
  variants?: Variant[];

  /** 写作 */
  starter?: string;
  min_words?: number;
  required_any?: string[];
  reference?: string;
  checklist?: string[];

  /** 题目自身直接引用或改写的材料；没有时继承题库的选材依据。 */
  source_refs?: SourceReference[];
  /** 只有授权和来源都清楚的真人原声/视频才允许进入。 */
  media?: MediaAsset[];
}

export interface Deck {
  /** 只有独立考核题库使用。 */
  assessment_id?: string;
  topic_id: string;
  kind: string;
  title?: string;
  vocab?: string[];
  source_refs: SourceReference[];
  media?: MediaAsset[];
  items: DeckItem[];
}

export interface Track {
  id: string;
  title: string;
  kind: string;
  goal: string;
  skills: Array<"listen" | "speak" | "read" | "write">;
  deck: string;
  /** 与练习题物理分离的平行题，只负责阶段考核。 */
  assessment: string;
  passage?: string;
}

export interface Stage {
  id: string;
  title: string;
  subtitle: string;
  goal: string;
  requires: string[];
  tracks: Track[];
}

export interface Curriculum {
  title: string;
  tagline: string;
  lead: string;
  /** 三级都通过之后往哪走，显示在能力路线底部 */
  endpoint?: string;
  description: string;
  stages: Stage[];
}

export interface AppInfo {
  title: string;
  content_root: string;
  store_path: string;
}

export interface ReviewState {
  item_id: string;
  reps: number;
  ease: number;
  interval_days: number;
  /** unix 秒的十进制字符串，由 Rust 侧写成文本 */
  due_at: string;
  last_rating: number | null;
}

export interface MasteryState {
  mastery: number;
  last_correct: number;
  last_total: number;
}

export interface Mistake {
  item_id: string;
  topic_id: string;
  kind: string;
  error_tag: string;
  wrong_count: number;
  correct_days: number;
  variant_correct: boolean;
  selected_answer: string;
  correct_answer: string;
  explanation: string;
}

/** save_answer 的入参，字段必须与 Rust 的 ReviewInput 完全一致。 */
export interface ReviewInput {
  item_id: string;
  topic_id: string;
  kind: string;
  correct: boolean;
  deck_total: number;
  selected_answer: string;
  correct_answer: string;
  explanation: string;
  error_tag: string;
  is_variant: boolean;
}

export interface AssessmentInput {
  assessment_id: string;
  topic_id: string;
  correct: number;
  total: number;
}

/** 本机作答流水汇总，供首页连续天数和累计次数使用。 */
export interface AttemptStats {
  attempts: number;
  correct: number;
  active_days: number;
  streak: number;
}
