// 考研英语二（ADR 0025）：内容迁自磨砚，分两处存放——可公开的在 content/english2/，构建时
// 打进前端；引用了只能本机用的来源的在 content/private/english2/（ADR 0019），只能运行时向
// Rust 要。两边同一套相对路径，按 private-index 里记下的原始顺序合并回一份题库。

import { invoke, isTauri } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import { useEffect, useState } from "react";

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

interface PrivateIndex {
  files: Record<string, { private: string[]; order: string[] }>;
}

const PREFIX = "../../content/english2/";
const strip = (key: string) => key.slice(PREFIX.length);

const curriculumModule = import.meta.glob<Curriculum>("../../content/english2/curriculum.json", {
  eager: true,
  import: "default",
});
const indexModule = import.meta.glob<PrivateIndex>("../../content/english2/private-index.json", {
  eager: true,
  import: "default",
});
const deckModules = import.meta.glob<Deck>(
  ["../../content/english2/**/*.json", "!**/curriculum.json", "!**/private-index.json"],
  { eager: true, import: "default" },
);
const passageModules = import.meta.glob<string>("../../content/english2/**/*.md", {
  eager: true,
  query: "?raw",
  import: "default",
});

export const curriculum: Curriculum = Object.values(curriculumModule)[0];
export const privateIndex: PrivateIndex = Object.values(indexModule)[0] ?? { files: {} };
const publicDecks: Record<string, Deck> = Object.fromEntries(
  Object.entries(deckModules).map(([key, deck]) => [strip(key), deck]),
);
const publicPassages: Record<string, string> = Object.fromEntries(
  Object.entries(passageModules)
    .filter(([key]) => !key.endsWith("README.md"))
    .map(([key, text]) => [strip(key), text]),
);

/** 本机那份：路径 → 题库或短文正文。 */
export interface PrivateContent {
  decks: Record<string, Deck>;
  passages: Record<string, string>;
}

const EMPTY: PrivateContent = { decks: {}, passages: {} };

/**
 * 同一路径的公开与本机题库合并成一份：文件头取公开那份（两边一样），题目按拆分前的
 * 原始顺序排回去，不认识的 id 排在最后、保持各自原顺序。
 */
export function mergeDeck(path: string, pub: Deck | undefined, priv: Deck | undefined, index = privateIndex): Deck | undefined {
  if (!pub && !priv) return undefined;
  const items = [...(pub?.items ?? []), ...(priv?.items ?? [])];
  const order = index.files[path]?.order ?? [];
  const rank = new Map(order.map((id, i) => [id, i]));
  const sorted = items
    .map((item, i) => ({ item, key: rank.get(item.id) ?? order.length + i }))
    .sort((a, b) => a.key - b.key)
    .map(({ item }) => item);
  return { ...(pub ?? priv)!, items: sorted };
}

/** 本机缺了多少题：private-index 里登记了、本机那份里却没有的。 */
export function missingCount(priv: PrivateContent, index = privateIndex): number {
  let missing = 0;
  for (const [path, entry] of Object.entries(index.files)) {
    const have = new Set((priv.decks[path]?.items ?? []).map((item) => item.id));
    missing += entry.private.filter((id) => !have.has(id)).length;
  }
  return missing;
}

export interface English2 {
  curriculum: Curriculum;
  /** 按路径取合并后的题库；curriculum 里的 deck/decks/assessment 都是这里的键。 */
  deck: (path: string) => Deck | undefined;
  passage: (path: string) => string | undefined;
  /** 本机资料缺的题数；0 表示齐全。 */
  missing: number;
  loading: boolean;
  error?: string;
}

export function english2From(priv: PrivateContent, loading = false, error?: string): English2 {
  return {
    curriculum,
    deck: (path) => mergeDeck(path, publicDecks[path], priv.decks[path]),
    passage: (path) => publicPassages[path] ?? priv.passages[path],
    missing: missingCount(priv),
    loading,
    error,
  };
}

/** 一条轨上所有练习题（多单元的 decks 合并成一条）。 */
export function trackItems(content: English2, track: Track): DeckItem[] {
  const paths = track.decks ?? (track.deck ? [track.deck] : []);
  return paths.flatMap((path) => content.deck(path)?.items ?? []);
}

interface PrivateFile {
  path: string;
  text: string;
}

export async function loadPrivate(): Promise<PrivateContent> {
  if (!isTauri()) return EMPTY;
  const files = await invoke<PrivateFile[]>("read_private_english2");
  const out: PrivateContent = { decks: {}, passages: {} };
  for (const file of files) {
    if (file.path.endsWith(".md")) out.passages[file.path] = file.text;
    else if (file.path !== "private-index.json") out.decks[file.path] = JSON.parse(file.text) as Deck;
  }
  return out;
}

let pending: Promise<PrivateContent> | null = null;

/** 导入本地资料之后调用，让下次读取拿到新文件。 */
export function reloadPrivate() {
  pending = null;
}

export interface PrivateStatus {
  root: string;
  /** 开发版直接读仓库里的 content/private/，导入只影响安装版。 */
  dev: boolean;
  english2_files: number;
}

export async function privateStatus(): Promise<PrivateStatus | null> {
  return isTauri() ? invoke<PrivateStatus>("private_status") : null;
}

/**
 * 导入本地资料：选开发机拷来的 content/private（或它的上一层 content），复制进用户数据目录。
 * 返回复制的文件数；用户取消返回 null。
 */
export async function importPrivate(): Promise<number | null> {
  const picked = await open({ directory: true, title: "选择本机资料文件夹（content/private）" });
  if (typeof picked !== "string") return null;
  const copied = await invoke<number>("import_private", { from: picked });
  reloadPrivate();
  return copied;
}

export function useEnglish2(): English2 {
  const [state, setState] = useState<English2>(() => english2From(EMPTY, isTauri()));
  useEffect(() => {
    let alive = true;
    pending ??= loadPrivate();
    pending
      .then((priv) => alive && setState(english2From(priv)))
      .catch((error: unknown) => alive && setState(english2From(EMPTY, false, String(error))));
    return () => {
      alive = false;
    };
  }, []);
  return state;
}
