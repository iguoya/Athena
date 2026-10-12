// 考研英语二（ADR 0025）：内容迁自磨砚，全部在 content/english2/，构建时打进前端
// （自用软件不分流，ADR 0026）。课表里的 deck / decks / assessment / passage 都是这里的相对路径。

export interface Choice {
  label: string;
  ok: boolean;
  why?: string;
}

/** 出处：定位到具体例句、篇目或习题；relation 说明内容和来源的关系。 */
export interface SourceRef {
  source_id: string;
  relation: "verbatim" | "quoted" | "adapted" | "authored" | "selection_basis" | "exam_alignment" | "see_also";
  note?: string;
  locator?: string;
  locator_url?: string;
}

export interface Sense {
  pos: string;
  gloss: string;
}

/** 变式：同一个点换一句话再问一次，错题出库要做对一条（ADR 0024）。 */
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
  /** 单词题 */
  word?: string;
  senses?: Sense[];
  sentence?: string;
  /** 句子与短文题 */
  text?: string;
  choices?: Choice[];
  variants?: Variant[];
  /** 作文 */
  starter?: string;
  min_words?: number;
  required_any?: string[];
  reference?: string;
  checklist?: string[];
  source?: SourceRef[];
  /** 只有授权与来源都清楚的真人原声才有（如 VOA 公有领域录音）。 */
  media?: Media[];
}

export interface Media {
  kind: "audio" | "video";
  title: string;
  url: string;
  source_id: string;
}

export interface Deck {
  /** 只有独立考核题库有。 */
  assessment_id?: string;
  topic_id: string;
  kind: string;
  title?: string;
  source?: SourceRef[];
  items: DeckItem[];
}

export interface Track {
  id: string;
  title: string;
  kind: "vocab" | "sentence" | "writing";
  goal: string;
  skills: Array<"listen" | "speak" | "read" | "write">;
  deck?: string;
  decks?: string[];
  /** 与练习物理分离的平行题，只负责阶段考核（ADR 0024）。 */
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
  endpoint?: string;
  description: string;
  stages: Stage[];
}

const PREFIX = "../../content/english2/";
const strip = (key: string) => key.slice(PREFIX.length);

const curriculumModule = import.meta.glob<Curriculum>("../../content/english2/curriculum.json", {
  eager: true,
  import: "default",
});
const deckModules = import.meta.glob<Deck>(["../../content/english2/**/*.json", "!**/curriculum.json"], {
  eager: true,
  import: "default",
});
const passageModules = import.meta.glob<string>(["../../content/english2/**/*.md", "!**/README.md"], {
  eager: true,
  query: "?raw",
  import: "default",
});

export const curriculum: Curriculum = Object.values(curriculumModule)[0];
const decks: Record<string, Deck> = Object.fromEntries(
  Object.entries(deckModules).map(([key, deck]) => [strip(key), deck]),
);
const passages: Record<string, string> = Object.fromEntries(
  Object.entries(passageModules).map(([key, text]) => [strip(key), text]),
);

export interface English2 {
  curriculum: Curriculum;
  /** 按路径取题库；curriculum 里的 deck/decks/assessment 都是这里的键。 */
  deck: (path: string) => Deck | undefined;
  passage: (path: string) => string | undefined;
}

export const english2: English2 = {
  curriculum,
  deck: (path) => decks[path],
  passage: (path) => passages[path],
};

/** 一条轨上所有练习题（多单元的 decks 合并成一条）。 */
export function trackItems(content: English2, track: Track): DeckItem[] {
  const paths = track.decks ?? (track.deck ? [track.deck] : []);
  return paths.flatMap((path) => content.deck(path)?.items ?? []);
}
