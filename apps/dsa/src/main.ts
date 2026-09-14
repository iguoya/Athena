import { invoke as tauriInvoke } from "@tauri-apps/api/core";
import curriculumFallback from "../content/curriculum.json";
import {
  destroyLabEditor,
  getLabSource,
  hasLabEditor,
  formatCppFallback,
  mountLabEditor,
  setLabSource,
} from "./lab-editor";
import {
  mountTracePlayer,
  parseTrace,
  stopTracePlayback,
} from "./trace-player";
import "./styles.css";

/** Vite 打包进前端的案例原文：浏览器预览时可读；保存/编译仍需 Tauri。 */
const bundledCases = import.meta.glob("../content/cases/**/*.cpp", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

function hasTauri(): boolean {
  return typeof window !== "undefined" && !!(window as Window & {
    __TAURI_INTERNALS__?: unknown;
  }).__TAURI_INTERNALS__;
}

async function invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (!hasTauri()) {
    throw new Error(
      "当前不在 Athena DSA 窗口里（缺少 Tauri）。请用 `npm run tauri:dev` 或 `./scripts/dev.sh` 启动，不要只开浏览器里的 Vite 页。",
    );
  }
  return tauriInvoke<T>(cmd, args);
}

function bundledCaseSource(caseId: string, entrypoint: string): string | null {
  const needle = `/content/cases/${caseId}/${entrypoint}`;
  const hit = Object.entries(bundledCases).find(([path]) =>
    path.replace(/\\/g, "/").endsWith(needle),
  );
  return hit ? hit[1] : null;
}

type QuizChoice = { label: string; ok: boolean; why: string };

type QuizItem = {
  stem: string;
  choices: QuizChoice[];
  /** 章末题可标注覆盖的知识点 id */
  covers?: string;
  /** 有明确大纲/院校来源才写；没有就不标 */
  source?: string;
};

type Block =
  | { type: "lead" | "prose"; text: string }
  | { type: "callout"; tone?: string; title?: string; text: string }
  | {
      type: "compare";
      title?: string;
      left: { title: string; body: string };
      right: { title: string; body: string };
    }
  | { type: "steps"; title?: string; items: string[] }
  | {
      type: "predict";
      question: string;
      expect: string;
      explain: string;
      open_lab?: string;
    }
  | {
      type: "scenario";
      situation: string;
      options: { label: string; ok: boolean; why: string }[];
      open_lab?: string;
    }
  | { type: "practice"; prompt: string; hint?: string; open_lab?: string }
  | { type: "quiz"; title?: string; items: QuizItem[] }
  | { type: "summary"; title?: string; text: string };

type Outline = {
  promise: string;
  pain: string;
  model: string;
  scope: string;
  judgment: string;
  landing: string;
};

/** 一节课下的一个可独立改跑的小实验。 */
type LabSpec = {
  id: string;
  title: string;
  case: string;
  entrypoint: string;
  /** 题干：要验证/解决什么问题（读者第一眼该读的） */
  prompt?: string;
  /** 动手：补哪个符号、对照什么输出 */
  goal?: string;
  hint?: string;
  /** 运行输出须全部包含这些子串才算「已完成」 */
  pass?: { includes?: string[] };
};

/** 进度：未开始 / 已开始 / 未完成（已作答或已跑但未达标） / 已完成 */
type LabStatus = "none" | "started" | "tried" | "done";

type Topic = {
  id: string;
  title: string;
  difficulty: number;
  mastery_goal: string;
  knowledge_type: string;
  requires: string[];
  track?: string;
  guide_line: string;
  weight: string;
  outline: Outline;
  lesson: { blocks: Block[] };
  labs: LabSpec[];
};

type ChapterAssessment = {
  title?: string;
  intro?: string;
  items: QuizItem[];
};

type Chapter = {
  id: string;
  title: string;
  summary: string;
  track?: string;
  topics: Topic[];
  /** 章节下随堂考核：用于评判各知识点完成度 */
  checkpoint?: ChapterAssessment | null;
  /** 可选章末综合卷 */
  assessment?: ChapterAssessment | null;
};

type Track = { id: string; title: string; color: string };

type Curriculum = {
  id: string;
  title: string;
  tagline: string;
  description: string;
  spine: string[];
  tracks?: Track[];
  chapters: Chapter[];
};

type AppInfo = {
  title: string;
  content_root: string;
  store_path: string;
  compiler: string;
};

type RunResult = {
  ok: boolean;
  compile_log: string;
  stdout: string;
  stderr: string;
  duration_ms: number;
};

type TabId = "brief" | "lesson" | "exam";
type ViewId = "map" | "topic";
type StageMode = "topic" | "lab" | "checkpoint" | "finale";

const state = {
  curriculum: null as Curriculum | null,
  info: null as AppInfo | null,
  mastery: {} as Record<string, number>,
  /** topicId::labId → tried | done；缺省为未开始 */
  labStatus: {} as Record<string, LabStatus>,
  view: "map" as ViewId,
  stageMode: "topic" as StageMode,
  chapterId: "",
  topicId: "",
  tab: "brief" as TabId,
  labId: "",
  /** 按 topicId::labId 缓存编辑器内容，切换案例不丢未保存草稿。 */
  sourceByKey: {} as Record<string, string>,
  /** quiz_key → 各题所选选项下标；未答为 null。默认保留，不自动清空。 */
  quizPicks: {} as Record<string, Array<number | null>>,
};

let draftSaveTimer: number | null = null;

function persistLabDraft(topicId: string, labId: string, source: string) {
  const key = sourceKey(topicId, labId);
  state.sourceByKey[key] = source;
  if (!hasTauri()) return;
  if (draftSaveTimer != null) window.clearTimeout(draftSaveTimer);
  draftSaveTimer = window.setTimeout(() => {
    draftSaveTimer = null;
    void invoke("save_lab_draft", { labKey: key, source }).catch(() => undefined);
  }, 400);
}

function persistLabDraftNow(topicId: string, labId: string, source: string) {
  const key = sourceKey(topicId, labId);
  state.sourceByKey[key] = source;
  if (!hasTauri()) return;
  if (draftSaveTimer != null) {
    window.clearTimeout(draftSaveTimer);
    draftSaveTimer = null;
  }
  void invoke("save_lab_draft", { labKey: key, source }).catch(() => undefined);
}

function quizStoreKey(kind: string, id: string): string {
  return `${kind}:${id}`;
}

function persistQuizPicks(key: string, picks: Array<number | null>) {
  state.quizPicks[key] = picks;
  if (!hasTauri()) return;
  void invoke("save_quiz_picks", { quizKey: key, picks: JSON.stringify(picks) }).catch(
    () => undefined,
  );
}

function readQuizPicks(root: HTMLElement, itemCount: number): Array<number | null> {
  const picks: Array<number | null> = [];
  for (let qi = 0; qi < itemCount; qi += 1) {
    const row = root.querySelector(`[data-quiz-item$="-${qi}"]`);
    const opts = row
      ? Array.from(row.querySelectorAll<HTMLButtonElement>(".quiz-opt"))
      : [];
    const idx = opts.findIndex((b) => b.classList.contains("is-picked"));
    picks.push(idx >= 0 ? idx : null);
  }
  return picks;
}

function restoreQuizPicks(root: HTMLElement, picks: Array<number | null> | undefined) {
  if (!picks?.length) return;
  picks.forEach((ci, qi) => {
    if (ci == null) return;
    const row = root.querySelector(`[data-quiz-item$="-${qi}"]`);
    const btn = row?.querySelectorAll<HTMLButtonElement>(".quiz-opt")[ci];
    btn?.click();
  });
}

function $(id: string): HTMLElement {
  const el = document.getElementById(id);
  if (!el) throw new Error(`missing #${id}`);
  return el;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function goalClass(goal: string): string {
  if (goal === "master") return "badge badge-master";
  if (goal === "required") return "badge badge-required";
  return "badge badge-familiar";
}

function goalLabel(goal: string): string {
  if (goal === "master") return "精通";
  if (goal === "required") return "掌握";
  return "了解";
}

function allTopics(cur: Curriculum): Topic[] {
  return cur.chapters.flatMap((c) => c.topics);
}

function findTopic(id: string): Topic | null {
  const cur = state.curriculum;
  if (!cur) return null;
  return allTopics(cur).find((t) => t.id === id) ?? null;
}

function findChapterForTopic(topicId: string): Chapter | null {
  const cur = state.curriculum;
  if (!cur) return null;
  return cur.chapters.find((c) => c.topics.some((t) => t.id === topicId)) ?? null;
}

function topicLabs(topic: Topic): LabSpec[] {
  return Array.isArray(topic.labs) ? topic.labs : [];
}

function sourceKey(topicId: string, labId: string): string {
  return `${topicId}::${labId}`;
}

function getLabStatus(topicId: string, labId: string): LabStatus {
  const st = state.labStatus[sourceKey(topicId, labId)];
  if (st === "done" || st === "tried" || st === "started") return st;
  return "none";
}

function labStatusLabel(st: LabStatus): string {
  if (st === "done") return "已完成";
  if (st === "tried") return "未完成";
  if (st === "started") return "已开始";
  return "未开始";
}

function labStatusClass(st: LabStatus): string {
  if (st === "done") return "is-done";
  if (st === "tried") return "is-tried";
  if (st === "started") return "is-started";
  return "is-todo";
}

function labStatusBadgeClass(st: LabStatus): string {
  if (st === "done") return "badge-lab-done";
  if (st === "tried") return "badge-lab-tried";
  if (st === "started") return "badge-lab-started";
  return "badge-lab-todo";
}

function statusRank(st: LabStatus): number {
  if (st === "done") return 3;
  if (st === "tried") return 2;
  if (st === "started") return 1;
  return 0;
}

/** 输出是否达到课表 pass.includes 约定。 */
function labOutputPasses(lab: LabSpec, stdout: string): boolean {
  const needles = lab.pass?.includes;
  if (!needles?.length) return false;
  return needles.every((s) => stdout.includes(s));
}

async function persistStatusKey(key: string, status: LabStatus) {
  if (status === "none") return;
  const prev = state.labStatus[key];
  const prevSt: LabStatus =
    prev === "done" || prev === "tried" || prev === "started" ? prev : "none";
  if (statusRank(status) < statusRank(prevSt)) return;
  state.labStatus[key] = status;
  try {
    await invoke("save_lab_status", { labKey: key, status });
  } catch {
    /* 本地状态已更新 */
  }
}

async function persistLabStatus(topicId: string, labId: string, status: LabStatus) {
  await persistStatusKey(sourceKey(topicId, labId), status);
}

function topicOpenedKey(topicId: string): string {
  return `topic::${topicId}`;
}

/** 知识点在图谱上的进度：完成度满星=已完成；有进度未满=黄；未动=默认。 */
function getTopicProgressStatus(topic: Topic): LabStatus {
  const mastery = state.mastery[topic.id] ?? 0;
  if (mastery >= 5) return "done";

  if (mastery > 0) return "tried";

  const labs = topicLabs(topic);
  let bestLab: LabStatus = "none";
  for (const lab of labs) {
    const st = getLabStatus(topic.id, lab.id);
    if (statusRank(st) > statusRank(bestLab)) bestLab = st;
  }
  if (bestLab === "done" || bestLab === "tried") return "tried";
  if (bestLab === "started") return "started";

  const ch = findChapterForTopic(topic.id);
  if (ch) {
    const cp = getCheckpointStatus(ch);
    if (cp === "done" || cp === "tried") return "tried";
    if (cp === "started") return "started";
  }

  const opened = state.labStatus[topicOpenedKey(topic.id)];
  if (opened === "started" || opened === "tried" || opened === "done") {
    return opened === "done" ? "tried" : opened;
  }
  return "none";
}

function getChapterProgressStatus(chapter: Chapter): LabStatus {
  if (!chapter.topics.length) return "none";
  const statuses = chapter.topics.map((t) => getTopicProgressStatus(t));
  if (statuses.every((s) => s === "done")) return "done";
  let best: LabStatus = "none";
  for (const s of statuses) {
    if (statusRank(s) > statusRank(best)) best = s;
  }
  const cp = getCheckpointStatus(chapter);
  if (statusRank(cp) > statusRank(best)) best = cp;
  return best;
}

async function markTopicStarted(topicId: string) {
  await persistStatusKey(topicOpenedKey(topicId), "started");
}

function currentLab(topic: Topic): LabSpec | null {
  const labs = topicLabs(topic);
  if (!labs.length) return null;
  return labs.find((l) => l.id === state.labId) ?? labs[0];
}

function stashEditorSource() {
  const topic = findTopic(state.topicId);
  const lab = topic ? currentLab(topic) : null;
  if (!topic || !lab || !hasLabEditor()) return;
  persistLabDraftNow(topic.id, lab.id, getLabSource());
}

function openLab(labId: string) {
  const topic = findTopic(state.topicId);
  if (!topic) return;
  const labs = topicLabs(topic);
  if (!labs.some((l) => l.id === labId)) return;
  stashEditorSource();
  state.stageMode = "lab";
  state.labId = labId;
  state.tab = "brief";
  showView("topic");
  void markTopicStarted(state.topicId);
  void persistLabStatus(state.topicId, labId, "started");
  void refreshTopic();
}

/** 从任意处打开某知识点下的指定实验（独立入口，不走导读/讲解 Tab）。 */
function openTopicLab(topicId: string, labId: string) {
  const topic = findTopic(topicId);
  const chapter = findChapterForTopic(topicId);
  if (!topic || !chapter) return;
  if (!topicLabs(topic).some((l) => l.id === labId)) return;
  stashEditorSource();
  state.stageMode = "lab";
  state.topicId = topicId;
  state.chapterId = chapter.id;
  state.labId = labId;
  state.tab = "brief";
  showView("topic");
  void markTopicStarted(topicId);
  void persistLabStatus(topicId, labId, "started");
  void refreshTopic();
}

function labJumpButton(topic: Topic, labId: string | undefined): string {
  if (!labId) return "";
  const lab = topicLabs(topic).find((l) => l.id === labId);
  const label = lab ? `去实验 · ${lab.title}` : "去实验";
  return `<button type="button" class="lab-jump" data-open-lab="${escapeHtml(labId)}">${escapeHtml(label)}</button>`;
}

/** 按 requires 拓扑分层；同层按先修在课表中的平均位置排，减少交叉边。 */
function layoutLayers(topics: Topic[]): Topic[][] {
  const byId = new Map(topics.map((t) => [t.id, t]));
  const order = new Map(topics.map((t, i) => [t.id, i]));
  const depth = new Map<string, number>();

  const depthOf = (id: string, stack: Set<string>): number => {
    if (depth.has(id)) return depth.get(id)!;
    if (stack.has(id)) return 0;
    stack.add(id);
    const t = byId.get(id);
    let d = 0;
    if (t) {
      for (const r of t.requires) {
        if (byId.has(r)) d = Math.max(d, depthOf(r, stack) + 1);
      }
    }
    stack.delete(id);
    depth.set(id, d);
    return d;
  };

  for (const t of topics) depthOf(t.id, new Set());
  const max = Math.max(0, ...[...depth.values()]);
  const layers: Topic[][] = Array.from({ length: max + 1 }, () => []);
  for (const t of topics) layers[depth.get(t.id) ?? 0].push(t);

  const parentAvg = (t: Topic): number => {
    const reqs = t.requires.filter((id) => byId.has(id));
    if (!reqs.length) return order.get(t.id) ?? 0;
    return reqs.reduce((sum, id) => sum + (order.get(id) ?? 0), 0) / reqs.length;
  };
  for (const layer of layers) {
    layer.sort((a, b) => {
      const d = parentAvg(a) - parentAvg(b);
      if (d !== 0) return d;
      return (order.get(a.id) ?? 0) - (order.get(b.id) ?? 0);
    });
  }
  return layers;
}

function showView(view: ViewId) {
  state.view = view;
  $("view-map").classList.toggle("is-hidden", view !== "map");
  $("view-topic").classList.toggle("is-hidden", view !== "topic");
}

/** 估算文本像素宽：CJK 按一个字宽算，ASCII 折半。SVG 没有自动换行，只能自己排。 */
function textWidth(text: string, fontPx: number): number {
  let units = 0;
  for (const ch of text) units += /[\x00-\xff]/.test(ch) ? 0.55 : 1;
  return units * fontPx;
}

function wrapText(
  text: string,
  maxPx: number,
  fontPx: number,
  maxLines: number,
): string[] {
  const lines: string[] = [];
  let line = "";
  for (const ch of text) {
    const next = line + ch;
    if (line && textWidth(next, fontPx) > maxPx) {
      lines.push(line);
      if (lines.length === maxLines) return lines;
      line = ch;
    } else {
      line = next;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function elide(text: string, maxPx: number, fontPx: number, maxLines: number): string[] {
  const lines = wrapText(text, maxPx, fontPx, maxLines);
  if (textWidth(text, fontPx) > maxPx * maxLines && lines.length === maxLines) {
    lines[maxLines - 1] = lines[maxLines - 1].slice(0, -1) + "…";
  }
  return lines;
}

type BadgeStyle = { fill: string; stroke: string; ink: string };

// 与详情页的 .badge-* 同色，图上图下说的是同一件事就不该换一套颜色。
const GOAL_STYLE: Record<string, BadgeStyle> = {
  master: { fill: "#eef8f3", stroke: "#9ad0bc", ink: "#198754" },
  required: { fill: "#eef2fb", stroke: "#b7c7ef", ink: "#2f4f9b" },
  familiar: { fill: "#fbf6e8", stroke: "#e0d2a8", ink: "#7a5b12" },
};
const TYPE_STYLE: Record<string, BadgeStyle> = {
  concept: { fill: "#eef8f3", stroke: "#9ad0bc", ink: "#146c43" },
  skill: { fill: "#eef2fb", stroke: "#b7c7ef", ink: "#2f4f9b" },
  strategy: { fill: "#fff4e8", stroke: "#e0c4a8", ink: "#9a5a00" },
};
// 难度不配彩色：颜色这一通道已经让给「所属主线」了，难度只用灰阶深浅。
const DIFFICULTY_STYLE: BadgeStyle[] = [
  { fill: "#f6f8fa", stroke: "#e1e6ec", ink: "#6c757d" },
  { fill: "#f1f4f7", stroke: "#dae1e9", ink: "#5b6470" },
  { fill: "#e9eef4", stroke: "#ccd6e1", ink: "#48525e" },
  { fill: "#dde5ee", stroke: "#bcc9d7", ink: "#37424e" },
  { fill: "#cfdae7", stroke: "#a9b9cb", ink: "#2b3540" },
];

const TRACK_FALLBACK = "#0a58ca";

/** 相对根字号（20pt）的布局单位，图谱节点随基准缩放。 */
function emPx(em: number): number {
  const root = parseFloat(getComputedStyle(document.documentElement).fontSize);
  return (Number.isFinite(root) ? root : 26.67) * em;
}

function svgBadge(x: number, y: number, label: string, st: BadgeStyle): {
  svg: string;
  width: number;
} {
  const fontPx = emPx(0.52);
  const padX = emPx(0.55);
  const height = emPx(0.95);
  const width = Math.round(textWidth(label, fontPx)) + padX * 2;
  const svg = `<g transform="translate(${x}, ${y})">
      <rect width="${width}" height="${height}" rx="${height / 2}" ry="${height / 2}" fill="${st.fill}" stroke="${st.stroke}" stroke-width="1"></rect>
      <text class="badge-text" x="${width / 2}" y="${height * 0.72}" text-anchor="middle" font-size="${fontPx}" fill="${st.ink}">${escapeHtml(label)}</text>
    </g>`;
  return { svg, width };
}

function renderMap() {
  const cur = state.curriculum;
  if (!cur) return;

  $("hero-lead").textContent = cur.tagline;
  $("hero-desc").textContent = cur.description;
  $("spine-list").innerHTML = cur.spine
    .map((s) => `<li>${escapeHtml(s)}</li>`)
    .join("");

  const tracks = new Map((cur.tracks ?? []).map((t) => [t.id, t]));
  const chapterOf = new Map<string, Chapter>();
  for (const ch of cur.chapters) {
    for (const t of ch.topics) chapterOf.set(t.id, ch);
  }
  const trackIdOf = (t: Topic): string =>
    t.track || chapterOf.get(t.id)?.track || "";
  const colorOf = (t: Topic): string =>
    tracks.get(trackIdOf(t))?.color ?? TRACK_FALLBACK;

  const topics = allTopics(cur);
  const layers = layoutLayers(topics);
  const NODE_W = emPx(14.2);
  const NODE_H = emPx(7.6);
  const gapX = emPx(1.3);
  const gapY = emPx(4.4);
  const padX = emPx(3);
  const padY = emPx(1.7);
  const maxCount = Math.max(1, ...layers.map((l) => l.length));
  const width = padX * 2 + maxCount * NODE_W + (maxCount - 1) * gapX;
  const height = padY * 2 + layers.length * NODE_H + (layers.length - 1) * gapY;

  type Pos = { x: number; y: number; t: Topic };
  const pos = new Map<string, Pos>();
  layers.forEach((layer, li) => {
    const span = layer.length * NODE_W + Math.max(0, layer.length - 1) * gapX;
    const startX = (width - span) / 2;
    layer.forEach((t, i) => {
      pos.set(t.id, {
        x: startX + i * (NODE_W + gapX),
        y: padY + li * (NODE_H + gapY),
        t,
      });
    });
  });

  // 先修边染成**源节点**的主线色：顺着颜色就能看出一条知识是从哪条线上长出来的。
  const markers = new Map<string, string>();
  const edges: string[] = [];
  for (const t of topics) {
    const to = pos.get(t.id);
    if (!to) continue;
    for (const r of t.requires) {
      const from = pos.get(r);
      if (!from) continue;
      const color = colorOf(from.t);
      const markerId = `arrow-${color.replace("#", "")}`;
      markers.set(markerId, color);
      const x0 = from.x + NODE_W / 2;
      const y0 = from.y + NODE_H;
      const x1 = to.x + NODE_W / 2;
      const y1 = to.y;
      const mid = (y0 + y1) / 2;
      const strong = t.mastery_goal === "master" || t.weight === "先拿下";
      const tipGap = emPx(0.35);
      edges.push(
        `<path class="graph-edge${strong ? " strong" : ""}" stroke="${color}" d="M${x0} ${y0} C${x0} ${mid}, ${x1} ${mid}, ${x1} ${y1 - tipGap}" marker-end="url(#${markerId})" />`,
      );
    }
  }

  const textX = emPx(1.4);
  const textPadR = emPx(0.8);
  const textW = NODE_W - textX - textPadR;
  const fontGuide = emPx(0.55);
  const fontChapter = emPx(0.5);
  const guideLineH = emPx(0.72);
  const guideY0 = emPx(3.7);
  const badgeY = NODE_H - emPx(2.35);
  const badgeGap = emPx(0.25);
  const barY = NODE_H - emPx(0.55);
  const barH = emPx(0.28);
  const barPad = emPx(0.55);
  const nodes = [...pos.values()]
    .map(({ x, y, t }) => {
      const color = colorOf(t);
      const chapter = chapterOf.get(t.id);
      const mastery = state.mastery[t.id] ?? 0;
      const labs = topicLabs(t);
      const reqTitles = t.requires
        .map((id) => findTopic(id)?.title ?? id)
        .join("、");

      const pipW = emPx(0.32);
      const pipGap = emPx(0.08);
      const pipH = emPx(0.52);
      const pipsX = NODE_W - textPadR - (pipW * 5 + pipGap * 4);
      const pips = Array.from({ length: 5 }, (_, i) =>
        `<rect class="pip${i < mastery ? "" : " pip-off"}" x="${pipsX + i * (pipW + pipGap)}" y="${emPx(0.85)}" width="${pipW}" height="${pipH}" rx="${emPx(0.08)}"${i < mastery ? ` fill="${color}"` : ""}></rect>`,
      ).join("");

      const guideLines = elide(t.guide_line, textW, fontGuide, 2)
        .map((line, i) => `<text class="guide" x="${textX}" y="${guideY0 + i * guideLineH}" font-size="${fontGuide}">${escapeHtml(line)}</text>`)
        .join("");

      const level = Math.min(5, Math.max(1, t.difficulty || 1));
      let bx = textX;
      const badges = [
        svgBadge(bx, badgeY, `D${t.difficulty}`, DIFFICULTY_STYLE[level - 1]),
      ];
      bx += badges[0].width + badgeGap;
      const goal = svgBadge(
        bx, badgeY, goalLabel(t.mastery_goal),
        GOAL_STYLE[t.mastery_goal] ?? DIFFICULTY_STYLE[0],
      );
      badges.push(goal);
      bx += goal.width + badgeGap;
      badges.push(
        svgBadge(
          bx, badgeY, typeLabel(t.knowledge_type),
          TYPE_STYLE[t.knowledge_type] ?? DIFFICULTY_STYLE[0],
        ),
      );
      if (t.weight) {
        bx += badges[badges.length - 1].width + badgeGap;
        badges.push(
          svgBadge(bx, badgeY, t.weight, {
            fill: "#fff4e8",
            stroke: "#e0c4a8",
            ink: "#9a5a00",
          }),
        );
      }
      if (labs.length) {
        bx += badges[badges.length - 1].width + badgeGap;
        badges.push(
          svgBadge(bx, badgeY, `实验${labs.length}`, {
            fill: "#eef2fb",
            stroke: "#b7c7ef",
            ink: "#2f4f9b",
          }),
        );
      }

      const chapterTitle = elide(chapter?.title ?? "", textW - emPx(3), fontChapter, 1)[0] ?? "";
      const rx = emPx(0.7);
      const accentX = emPx(0.65);
      const accentW = emPx(0.2);
      const fontTitle = emPx(0.7);
      const barW = NODE_W - barPad * 2;
      const fillW = (barW * mastery) / 5;
      const progress = getTopicProgressStatus(t);
      const progressCls = labStatusClass(progress);
      const accentFill =
        progress === "done" ? "#198754" : progress === "tried" || progress === "started" ? "#d97706" : color;
      const chapterFill = accentFill;
      const tip = [
        t.title,
        t.guide_line,
        `章：${chapter?.title ?? "?"}`,
        `状态：${labStatusLabel(progress)}`,
        `难度 D${t.difficulty} · ${goalLabel(t.mastery_goal)} · ${typeLabel(t.knowledge_type)}${t.weight ? ` · ${t.weight}` : ""}`,
        `完成度 ${mastery}/5（随堂考核）`,
        labs.length ? `实验 ${labs.length}：${labs.map((l) => l.title).join("、")}` : "暂无实验",
        reqTitles ? `先修：${reqTitles}` : "先修：无",
        chapter?.checkpoint?.items?.length
          ? `本章有随堂考核（${chapter.checkpoint.items.length} 题）`
          : "本章暂无随堂考核",
      ].join("\n");

      return `<g class="graph-node ${progressCls}" data-topic="${escapeHtml(t.id)}" transform="translate(${x}, ${y})">
        <title>${escapeHtml(tip)}</title>
        <rect class="node-card" width="${NODE_W}" height="${NODE_H}" rx="${rx}" ry="${rx}"></rect>
        <rect x="${accentX}" y="${emPx(0.8)}" width="${accentW}" height="${NODE_H - emPx(1.6)}" rx="${emPx(0.1)}" fill="${accentFill}"></rect>
        <text class="chapter" x="${textX}" y="${emPx(1.3)}" font-size="${fontChapter}" fill="${chapterFill}">${escapeHtml(chapterTitle)}</text>
        ${pips}
        <text class="title" x="${textX}" y="${emPx(2.55)}" font-size="${fontTitle}">${escapeHtml(t.title)}</text>
        ${guideLines}
        ${badges.map((b) => b.svg).join("")}
        <rect x="${barPad}" y="${barY}" width="${barW}" height="${barH}" rx="${barH / 2}" fill="#e4e8ed"></rect>
        <rect x="${barPad}" y="${barY}" width="${fillW}" height="${barH}" rx="${barH / 2}" fill="${accentFill}"></rect>
      </g>`;
    })
    .join("");

  // 交替的浅色横带，让"同一层没有先后"一眼看得出来。
  const bandPad = emPx(0.7);
  const bands = layers
    .map((_, li) =>
      li % 2 === 1
        ? `<rect class="layer-band" x="0" y="${padY + li * (NODE_H + gapY) - bandPad}" width="${width}" height="${NODE_H + bandPad * 2}" rx="${emPx(0.8)}"></rect>`
        : "",
    )
    .join("");

  const layerLabels = layers
    .map((layer, li) => {
      const y = padY + li * (NODE_H + gapY) + emPx(1);
      return `<text class="layer-label" x="${emPx(0.8)}" y="${y}" font-size="${emPx(0.55)}">L${li} · ${layer.length}</text>`;
    })
    .join("");

  const defs = [...markers.entries()]
    .map(([id, color]) =>
      `<marker id="${id}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="${color}"></path></marker>`,
    )
    .join("");

  $("graph").innerHTML = `<svg viewBox="0 0 ${width} ${height}" style="width:100%;max-width:${width}px" role="img">
    <defs>${defs}</defs>
    ${bands}
    ${layerLabels}
    ${edges.join("")}
    ${nodes}
  </svg>`;

  $("graph").querySelectorAll<SVGGElement>("[data-topic]").forEach((g) => {
    const id = g.dataset.topic;
    if (!id) return;
    g.addEventListener("mouseenter", () => showNodeDetail(id));
    g.addEventListener("click", () => {
      openTopic(id);
    });
  });

  renderTrackLegend(cur, tracks);
  renderProgressPanel(cur, tracks);
  renderNodeLegend();
}

function showNodeDetail(topicId: string) {
  const t = findTopic(topicId);
  const el = document.getElementById("node-detail");
  if (!el || !t) return;
  const ch = findChapterForTopic(topicId);
  const mastery = state.mastery[t.id] ?? 0;
  const labs = topicLabs(t);
  const reqs = t.requires.length
    ? t.requires
        .map((id) => escapeHtml(findTopic(id)?.title ?? id))
        .join("、")
    : "无";
  const pct = Math.round((mastery / 5) * 100);
  el.classList.remove("muted");
  el.innerHTML = `
    <div class="nd-title">${escapeHtml(t.title)}</div>
    <p class="nd-line">${escapeHtml(t.guide_line)}</p>
    <div class="nd-meta">
      <span class="badge">D${t.difficulty}</span>
      <span class="${goalClass(t.mastery_goal)}">${goalLabel(t.mastery_goal)}</span>
      <span class="${typeClass(t.knowledge_type)}">${typeLabel(t.knowledge_type)}</span>
      ${t.weight ? `<span class="badge">${escapeHtml(t.weight)}</span>` : ""}
    </div>
    <p class="nd-kv"><b>所属章</b> ${escapeHtml(ch?.title ?? "—")}</p>
    <p class="nd-kv"><b>先修</b> ${reqs}</p>
    <p class="nd-kv"><b>完成度</b> ${mastery}/5（${pct}%）· 随堂考核评定</p>
    <p class="nd-kv"><b>实验</b> ${
      labs.length
        ? labs.map((l) => escapeHtml(l.title)).join("、")
        : "暂无"
    }</p>
    <p class="nd-kv"><b>随堂考核</b> ${
      ch?.checkpoint?.items?.length
        ? `${ch.checkpoint.items.length} 题 · 左侧章节下入口`
        : "尚未配置"
    }</p>
    <p class="nd-kv"><b>实验入口</b> 左侧「本章实验」各题独立打开（非顶栏 Tab）</p>
    <button type="button" class="lab-jump" data-open-topic="${escapeHtml(t.id)}">进入导读</button>`;
  el.querySelector<HTMLButtonElement>("[data-open-topic]")?.addEventListener(
    "click",
    () => openTopic(t.id),
  );
}

function renderTrackLegend(cur: Curriculum, tracks: Map<string, Track>) {
  $("track-legend").innerHTML = (cur.tracks ?? [])
    .map(
      (t) =>
        `<span><i style="background:${t.color}"></i>${escapeHtml(t.title)}</span>`,
    )
    .join("");
  void tracks;
}

function renderProgressPanel(cur: Curriculum, tracks: Map<string, Track>) {
  const topics = allTopics(cur);
  const mastered = topics.filter((t) => (state.mastery[t.id] ?? 0) >= 5).length;
  const doing = topics.filter((t) => {
    const m = state.mastery[t.id] ?? 0;
    return m > 0 && m < 5;
  }).length;
  const untouched = topics.length - mastered - doing;
  const sum = topics.reduce((a, t) => a + (state.mastery[t.id] ?? 0), 0);
  const pct = topics.length ? Math.round((sum / (topics.length * 5)) * 100) : 0;

  $("stat-row").innerHTML = [
    { n: topics.length, label: "知识点总数", cls: "stat-total" },
    { n: mastered, label: "已完成（5）", cls: "stat-mastered" },
    { n: doing, label: "学习中（1–4）", cls: "stat-doing" },
    { n: untouched, label: "未涉及（0）", cls: "stat-none" },
  ]
    .map(
      (s) =>
        `<div class="stat ${s.cls}"><b>${s.n}</b><span>${s.label}</span></div>`,
    )
    .join("");

  // 三色环 + 星级分布 + 已动过的知识点条（对齐 C++ progress_overview）
  const hist = [0, 0, 0, 0, 0, 0];
  for (const t of topics) hist[state.mastery[t.id] ?? 0] += 1;
  const maxH = Math.max(1, ...hist);
  const r = 36;
  const circ = 2 * Math.PI * r;
  const totalN = Math.max(1, topics.length);
  const masteredPct = Math.round((mastered / totalN) * 100);
  let dashOff = 0;
  const donutSegs = (
    [
      [mastered, "#198754"],
      [doing, "#fd7e14"],
      [untouched, "#9ea6ad"],
    ] as const
  )
    .map(([n, color]) => {
      const len = (n / totalN) * circ;
      const el = `<circle cx="48" cy="48" r="${r}" fill="none" stroke="${color}" stroke-width="11"
        stroke-dasharray="${len} ${circ - len}" stroke-dashoffset="${-dashOff}"
        transform="rotate(-90 48 48)"/>`;
      dashOff += len;
      return el;
    })
    .join("");

  const started = topics
    .map((t) => ({ t, m: state.mastery[t.id] ?? 0 }))
    .filter((x) => x.m > 0)
    .sort((a, b) => b.m - a.m || a.t.title.localeCompare(b.t.title, "zh"));

  const viz = document.getElementById("progress-viz");
  if (viz) {
    viz.innerHTML = `
      <div class="pv-row">
        <svg class="pv-ring" viewBox="0 0 96 96" aria-label="已完成占比 ${masteredPct}%">
          <circle cx="48" cy="48" r="${r}" fill="none" stroke="#e9edf2" stroke-width="11"/>
          ${donutSegs}
          <text x="48" y="46" text-anchor="middle" class="pv-pct">${masteredPct}%</text>
          <text x="48" y="60" text-anchor="middle" class="pv-pct-sub">已完成</text>
        </svg>
        <div class="pv-ring-cap">
          <div class="pv-ring-title">整体完成度</div>
          <p class="muted">环心 = 已满星占比；加权完成度（完成合计÷知识点×5）为 ${pct}%。</p>
          <div class="pv-swatches">
            <span><i class="sw mastery-all"></i>已完成</span>
            <span><i class="sw mastery-some"></i>学习中</span>
            <span><i class="sw mastery-none"></i>未涉及</span>
          </div>
        </div>
      </div>
      <div class="pv-hist" aria-label="完成度分布">
        ${hist
          .map((n, star) => {
            const mix = star / 5;
            const fill =
              star === 0
                ? "#9ea6ad"
                : `color-mix(in srgb, #fd7e14 ${Math.round((1 - mix) * 100)}%, #198754)`;
            return `<div class="pv-bar" title="${star}★ × ${n}">
                <b style="height:${Math.round((n / maxH) * 100)}%;background:${fill}"></b>
                <em>${n}</em>
                <span>${star}</span>
              </div>`;
          })
          .join("")}
      </div>
      <p class="muted pv-hist-cap">横轴完成度 0–5，柱高为知识点个数</p>
      ${
        started.length
          ? `<div class="pv-points">
              <div class="pv-points-title">各知识点完成度</div>
              <ul>${started
                .map(({ t, m }) => {
                  const color =
                    tracks.get(
                      t.track ||
                        findChapterForTopic(t.id)?.track ||
                        "",
                    )?.color ?? TRACK_FALLBACK;
                  return `<li data-topic="${escapeHtml(t.id)}">
                    <span class="pp-name" style="border-left-color:${color}">${escapeHtml(t.title)}</span>
                    <span class="pp-bar"><b style="width:${(m / 5) * 100}%;background:${color}"></b></span>
                    <span class="pp-n">${m}/5</span>
                  </li>`;
                })
                .join("")}</ul>
            </div>`
          : `<p class="muted pv-empty">完成任意章的「随堂考核」后，这里会列出已考核知识点。</p>`
      }`;
    viz.querySelectorAll<HTMLElement>("[data-topic]").forEach((li) => {
      const id = li.dataset.topic;
      if (!id) return;
      li.addEventListener("mouseenter", () => showNodeDetail(id));
      li.addEventListener("click", () => openTopic(id));
    });
  }

  $("chapter-stats").innerHTML = cur.chapters
    .map((ch) => {
      const color = tracks.get(ch.track ?? "")?.color ?? TRACK_FALLBACK;
      const total = ch.topics.length;
      const chSum = ch.topics.reduce((acc, t) => acc + (state.mastery[t.id] ?? 0), 0);
      const done = ch.topics.filter((t) => (state.mastery[t.id] ?? 0) >= 5).length;
      const mid = ch.topics.filter((t) => {
        const m = state.mastery[t.id] ?? 0;
        return m > 0 && m < 5;
      }).length;
      const zero = total - done - mid;
      const chPct = total > 0 ? Math.round((chSum / (total * 5)) * 100) : 0;
      const avgDiff =
        total > 0
          ? (ch.topics.reduce((a, t) => a + (t.difficulty || 0), 0) / total).toFixed(1)
          : "—";
      const hasCp = !!ch.checkpoint?.items?.length;
      const chSt = getChapterProgressStatus(ch);
      const band =
        chSt === "done" ? "ch-all" : chSt === "none" ? "ch-none" : "ch-some";
      const status = labStatusLabel(chSt);
      const barColor =
        chSt === "done" ? "#198754" : chSt === "none" ? color : "#d97706";
      return `<li class="${band}" title="${escapeHtml(ch.summary)}">
        <i style="background:${barColor}"></i>
        <span class="name">${escapeHtml(ch.title)}</span>
        <span class="num">D̄${avgDiff} · ${done}/${total} · ${chPct}%</span>
        <span class="bar"><b style="width:${chPct}%;background:${barColor}"></b></span>
        <span class="ch-extra muted">${
          hasCp
            ? `随堂考核 ${ch.checkpoint!.items.length} 题`
            : "缺随堂考核"
        } · ${status}${
          mid + zero && chSt !== "done" && chSt !== "none"
            ? `（满星 ${done} · 进行中 ${mid} · 未涉 ${zero}）`
            : ""
        }</span>
      </li>`;
    })
    .join("");
}

function renderNodeLegend() {
  const pips = (on: number) =>
    Array.from({ length: 5 }, (_, i) => `<i class="${i < on ? "on" : ""}"></i>`).join("");
  const diffScale = [1, 2, 3, 4, 5]
    .map((d) => `<i class="diff-pip d${d}">${d}</i>`)
    .join("");
  $("legend-list").innerHTML = [
    ["<b class=\"lg-h\">连接关系</b>", ""],
    ["箭头颜色", "取自先修（源）节点的主线色，顺着颜色能摸回主线"],
    ["粗箭头", "后继掌握目标为精通，或标了「先拿下」"],
    ["细箭头", "普通先修依赖；纵向层级 = 先修深度"],
    ["<b class=\"lg-h\">节点编码</b>", ""],
    ["左侧色条", "所属主线（见图谱上方色点）"],
    [`<span class="pips">${pips(3)}</span> + 底条`, "完成度 0–5，随堂考核答完后自动写入"],
    [
      `<span class="diff-scale">${diffScale}</span>`,
      "难度 D1–D5（灰阶；彩色留给主线）",
    ],
    ["精通 / 掌握 / 了解", "掌握目标：要投入到什么程度"],
    ["概念 / 技能 / 策略", "知识类型：决定怎么学"],
    ["先拿下 / …", "学习权重（若有）"],
    ["<b class=\"lg-h\">完成程度（章节）</b>", ""],
    [
      `<span class="lg-sw"><i class="sw mastery-none"></i><i class="sw mastery-some"></i><i class="sw mastery-all"></i></span>`,
      "本章尚无满星 / 部分满星 / 全部满星",
    ],
    ["悬停详情", "先修、实验、本章是否有随堂考核；点击进入导读"],
  ]
    .map(([key, text]) =>
      text
        ? `<li><span class="key">${key}</span><span>${text}</span></li>`
        : `<li class="lg-section">${key}</li>`,
    )
    .join("");
}

function findChapter(id: string): Chapter | null {
  return state.curriculum?.chapters.find((c) => c.id === id) ?? null;
}

function openTopic(topicId: string, opts?: { tab?: TabId; labId?: string }) {
  const topic = findTopic(topicId);
  const chapter = findChapterForTopic(topicId);
  if (!topic || !chapter) return;
  stashEditorSource();
  if (opts?.labId && topicLabs(topic).some((l) => l.id === opts.labId)) {
    openTopicLab(topicId, opts.labId);
    return;
  }
  state.stageMode = "topic";
  state.topicId = topicId;
  state.chapterId = chapter.id;
  state.tab = opts?.tab === "lesson" ? "lesson" : "brief";
  const labs = topicLabs(topic);
  state.labId = labs[0]?.id ?? "";
  showView("topic");
  void refreshTopic();
}

function openChapterExam(chapterId: string, kind: "checkpoint" | "finale") {
  const chapter = findChapter(chapterId);
  if (!chapter) return;
  const pack = kind === "checkpoint" ? chapter.checkpoint : chapter.assessment;
  if (!pack?.items?.length) return;
  stashEditorSource();
  state.stageMode = kind === "checkpoint" ? "checkpoint" : "finale";
  state.chapterId = chapterId;
  state.topicId = chapter.topics[0]?.id ?? "";
  state.tab = "exam";
  showView("topic");
  void refreshTopic();
}

function checkpointCoverIds(chapter: Chapter): string[] {
  const items = chapter.checkpoint?.items ?? [];
  const covers = [
    ...new Set(items.map((i) => i.covers).filter((x): x is string => !!x)),
  ];
  if (covers.length) return covers;
  return chapter.topics.map((t) => t.id);
}

/** 随堂考核是否已完成过：覆盖知识点均已写入完成度（含 0 分）。 */
function isCheckpointDone(chapter: Chapter): boolean {
  if (!chapter.checkpoint?.items?.length) return false;
  return checkpointCoverIds(chapter).every((id) =>
    Object.prototype.hasOwnProperty.call(state.mastery, id),
  );
}

function checkpointStatusKey(chapterId: string): string {
  return `checkpoint::${chapterId}`;
}

/** 未开始 / 已开始 / 未完成 / 已完成 */
function getCheckpointStatus(chapter: Chapter): LabStatus {
  if (isCheckpointDone(chapter)) {
    // 考核交卷后：各 covers 满星才算章知识点「已完成」，否则仍是未完成（黄）
    const covers = checkpointCoverIds(chapter);
    if (covers.length && covers.every((id) => (state.mastery[id] ?? 0) >= 5)) {
      return "done";
    }
    return "tried";
  }
  const st = state.labStatus[checkpointStatusKey(chapter.id)];
  if (st === "done" || st === "tried" || st === "started") return st;
  return "none";
}

async function markCheckpointTried(chapter: Chapter) {
  await persistStatusKey(checkpointStatusKey(chapter.id), "started");
  renderNav();
}

function renderNav() {
  const cur = state.curriculum;
  if (!cur) return;
  const current =
    findChapter(state.chapterId) ?? findChapterForTopic(state.topicId);
  if (!current) {
    $("nav").innerHTML = "";
    return;
  }
  $("nav").innerHTML = [current]
    .map((ch) => {
      const topics = ch.topics
        .map((t) => {
          const active =
            state.stageMode === "topic" && t.id === state.topicId ? " is-active" : "";
          const stars = "★".repeat(state.mastery[t.id] ?? 0);
          return `<button type="button" class="topic-btn${active}" data-topic="${escapeHtml(t.id)}">
            <span class="name">${escapeHtml(t.title)}</span>
            <span class="meta-row">
              <span class="badge">D${t.difficulty}</span>
              <span class="${goalClass(t.mastery_goal)}">${goalLabel(t.mastery_goal)}</span>
              ${stars ? `<span class="stars">${stars}</span>` : ""}
            </span>
          </button>`;
        })
        .join("");

      // 本章实验：与知识点平级的独立入口（不走导读/讲解 Tab）
      const chapterLabs = ch.topics.flatMap((t) =>
        topicLabs(t).map((lab) => ({ topic: t, lab })),
      );
      const labBlock = chapterLabs.length
        ? `<div class="nav-subhead">本章实验</div>
           <div class="nav-labs">${chapterLabs
             .map(({ topic: t, lab }) => {
               const active =
                 state.stageMode === "lab" &&
                 state.topicId === t.id &&
                 state.labId === lab.id
                   ? " is-active"
                   : "";
               const st = getLabStatus(t.id, lab.id);
               return `<button type="button" class="topic-btn lab-nav-btn${active} ${labStatusClass(st)}" data-lab-topic="${escapeHtml(t.id)}" data-lab-id="${escapeHtml(lab.id)}">
                 <span class="name">${escapeHtml(lab.title)}</span>
                 <span class="meta-row">
                   <span class="badge ${labStatusBadgeClass(st)}">${labStatusLabel(st)}</span>
                 </span>
               </button>`;
             })
             .join("")}</div>`
        : "";

      const cpActive =
        state.stageMode === "checkpoint" && state.chapterId === ch.id ? " is-active" : "";
      const finActive =
        state.stageMode === "finale" && state.chapterId === ch.id ? " is-active" : "";
      const cpStatus = getCheckpointStatus(ch);
      const checkpointBtn = ch.checkpoint?.items?.length
        ? `<button type="button" class="topic-btn exam-btn${cpActive} ${labStatusClass(cpStatus)}" data-checkpoint="${escapeHtml(ch.id)}">
            <span class="name">随堂考核</span>
            <span class="meta-row"><span class="badge ${
              cpStatus === "done"
                ? "badge-exam-done"
                : cpStatus === "tried"
                  ? "badge-lab-tried"
                  : "badge-exam-todo"
            }">${labStatusLabel(cpStatus)}</span></span>
          </button>`
        : "";
      const finaleBtn = ch.assessment?.items?.length
        ? `<button type="button" class="topic-btn exam-btn${finActive}" data-finale="${escapeHtml(ch.id)}">
            <span class="name">章末考核</span>
            <span class="meta-row"><span class="badge">综合</span></span>
          </button>`
        : "";

      // 知识点 → 随堂考核（紧挨知识点）→ 本章实验 → 章末
      return `<div class="chapter">
        <div class="chapter-title">${escapeHtml(ch.title)}</div>
        <p class="chapter-summary">${escapeHtml(ch.summary)}</p>
        ${topics}
        ${checkpointBtn}
        ${labBlock}
        ${finaleBtn}
      </div>`;
    })
    .join("");

  $("nav").querySelectorAll<HTMLButtonElement>("[data-topic]").forEach((btn) => {
    btn.addEventListener("click", () => {
      openTopic(btn.dataset.topic ?? "");
    });
  });
  $("nav").querySelectorAll<HTMLButtonElement>("[data-lab-topic]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const topicId = btn.dataset.labTopic ?? "";
      const labId = btn.dataset.labId ?? "";
      if (topicId && labId) openTopicLab(topicId, labId);
    });
  });
  $("nav").querySelectorAll<HTMLButtonElement>("[data-checkpoint]").forEach((btn) => {
    btn.addEventListener("click", () => {
      openChapterExam(btn.dataset.checkpoint ?? "", "checkpoint");
    });
  });
  $("nav").querySelectorAll<HTMLButtonElement>("[data-finale]").forEach((btn) => {
    btn.addEventListener("click", () => {
      openChapterExam(btn.dataset.finale ?? "", "finale");
    });
  });
}

function syncTabs() {
  const showTabs = state.stageMode === "topic";
  const tabs = document.getElementById("tabs");
  if (tabs) tabs.classList.toggle("is-hidden", !showTabs);
  document.querySelectorAll<HTMLButtonElement>(".tab").forEach((tab) => {
    tab.classList.toggle("is-active", showTabs && tab.dataset.tab === state.tab);
  });
}

function renderBrief(chapter: Chapter, topic: Topic, cur: Curriculum) {
  const o = topic.outline;
  const siblings = chapter.topics
    .map((t) => {
      const here = t.id === topic.id ? " is-here" : "";
      return `<button type="button" class="brief-node${here}" data-topic="${escapeHtml(t.id)}">
        <span class="brief-node-title">${escapeHtml(t.title)}</span>
        <span class="meta-row">
          <span class="badge">D${t.difficulty}</span>
          <span class="${goalClass(t.mastery_goal)}">${goalLabel(t.mastery_goal)}</span>
        </span>
        <span class="brief-node-line">${escapeHtml(t.guide_line)}</span>
      </button>`;
    })
    .join("");

  const visual = briefVisual(topic);

  const sections: [string, string][] = [
    ["这一节要解决什么", o.promise],
    ["痛点与来历", o.pain],
    ["心智模型", o.model],
    ["讲什么与边界", o.scope],
    ["判断与代价", o.judgment],
    ["落点", o.landing],
  ];

  const outlineHtml = sections
    .map(
      ([title, body]) =>
        `<div class="brief-section"><h3>${escapeHtml(title)}</h3><p class="prose">${escapeHtml(body)}</p></div>`,
    )
    .join("");

  return `
    <div class="card brief-hero">
      <p class="lead">${escapeHtml(topic.guide_line)}</p>
      <p class="prose muted stack-gap">章 · ${escapeHtml(chapter.title)}：${escapeHtml(chapter.summary)}</p>
      <p class="prose muted">先修：${
        topic.requires.length
          ? topic.requires
              .map((id) => escapeHtml(findTopic(id)?.title ?? id))
              .join("、")
          : "无（本课入口工具）"
      }</p>
    </div>
    <div class="card">
      <div class="pane-title">本章知识点</div>
      <div class="brief-map">${siblings}</div>
      <p class="prose muted stack-gap">${escapeHtml(cur.tagline)}</p>
    </div>
    ${visual}
    <div class="card">
      <div class="pane-title">方向与边界</div>
      ${outlineHtml}
    </div>`;
}

/** 导读层的可视块：能画的不堆同样的长文（ADR 0001）。 */
function briefVisual(topic: Topic): string {
  if (topic.id === "dsa.complexity.measure") {
    return `
    <div class="card">
      <div class="pane-title">量级锚点（同一把尺子）</div>
      <div class="viz-scroll">
        <svg class="viz-growth" viewBox="0 0 420 160" role="img" aria-label="常见复杂度随 n 增长示意">
          <text x="8" y="14" class="viz-label">步数随 n（示意，非计时）</text>
          <path d="M40 130 H400" stroke="#ced4da" stroke-width="1"/>
          <path d="M40 20 V130" stroke="#ced4da" stroke-width="1"/>
          <path d="M40 120 H400" fill="none" stroke="#9aa4af" stroke-width="2" stroke-dasharray="4 3"/>
          <text x="404" y="124" class="viz-anno">O(1)</text>
          <path d="M40 125 Q220 110 400 70" fill="none" stroke="#198754" stroke-width="2.5"/>
          <text x="404" y="74" class="viz-anno" fill="#198754">O(log n)</text>
          <path d="M40 125 L400 55" fill="none" stroke="#0a58ca" stroke-width="2.5"/>
          <text x="404" y="58" class="viz-anno" fill="#0a58ca">O(n)</text>
          <path d="M40 125 Q180 100 400 18" fill="none" stroke="#6f42c1" stroke-width="2.5"/>
          <text x="330" y="22" class="viz-anno" fill="#6f42c1">O(n log n)</text>
          <path d="M40 125 Q120 120 220 70 Q300 30 360 8" fill="none" stroke="#dc3545" stroke-width="2.5"/>
          <text x="250" y="48" class="viz-anno" fill="#dc3545">O(n²)</text>
          <text x="200" y="148" class="viz-label">n →</text>
        </svg>
      </div>
      <table class="viz-table">
        <thead><tr><th>形态</th><th>代码直觉</th><th>n→2n</th></tr></thead>
        <tbody>
          <tr><td>O(1)</td><td>下标访问</td><td>×1</td></tr>
          <tr><td>O(log n)</td><td>每次砍半</td><td>+约 1 步</td></tr>
          <tr><td>O(n)</td><td>扫一遍</td><td>×2</td></tr>
          <tr><td>O(n log n)</td><td>分治排序级</td><td>×2 多一点</td></tr>
          <tr><td>O(n²)</td><td>两层各扫 n</td><td>×4</td></tr>
        </tbody>
      </table>
      <p class="prose muted stack-gap">时间与空间共用这套记号；空间要问的是「额外借了多少」，递归栈也算。</p>
    </div>`;
  }
  const tables: Record<string, string> = {
    "dsa.linear.list": vizTable("找 vs 改", ["操作", "数组", "链表"], [
      ["取第 k 个", "O(1)", "O(k)"],
      ["已知结点后插", "要搬移", "O(1) 改指针"],
      ["按序号扫全表", "缓存友好", "跳指针"],
    ], "考试先问：结点找到了没有。没找到就谈不上 O(1)。"),
    "dsa.linear.stack_queue": vizTable("约定", ["", "栈", "队列"], [
      ["纪律", "LIFO", "FIFO"],
      ["典型", "括号 / 调用 / DFS", "BFS / 一层一层"],
      ["实现", "数组或链表", "数组、链、循环队列"],
    ], "出栈序列可不可能、循环队列空满，是加一档的手算题。"),
    "dsa.hash.table": vizTable("按键查找怎么选", ["", "哈希", "BST"], [
      ["平均查找", "O(1) 期望", "O(log n) 期望"],
      ["顺序", "不保持", "中序有序"],
      ["最坏", "可退化成链", "无平衡则变链"],
    ], "先会算 key % m；装载因子高则冲突多。"),
    "dsa.tree.basics": vizTable("四种遍历", ["走法", "顺序", "常用来"], [
      ["先序", "根左右", "复制 / 序列化"],
      ["中序", "左根右", "BST 得到有序"],
      ["后序", "左右根", "删树 / 求值"],
      ["层序", "按层", "宽度、一层一层"],
    ], "先序第一个是根；再结合中序可还原小树。"),
    "dsa.sort.advanced": vizTable("n log n 三问", ["", "归并", "快排", "堆排"], [
      ["稳定", "是", "通常否", "否"],
      ["额外空间", "Θ(n)", "O(log n) 栈", "O(1)"],
      ["最坏", "n log n", "n²", "n log n"],
    ], "先问稳定、空间、最坏，再选题。"),
    "dsa.graph.basics": vizTable("怎么存图", ["", "邻接表", "邻接矩阵"], [
      ["空间", "Θ(V+E)", "Θ(V²)"],
      ["问是否相邻", "可能扫链", "O(1)"],
      ["适用", "稀疏", "点少或边密"],
    ], "第一问往往是表示，不是最短路算法名。"),
    "dsa.paradigm.dp": vizTable("策略怎么分", ["", "分治", "DP", "贪心", "回溯"], [
      ["子问题", "独立", "重叠", "每步局部", "枚举构造"],
      ["先问", "怎么合", "状态是什么", "有无反例", "怎么撤销"],
    ], "408 少考范式；自主命题常出大题。"),
  };
  return tables[topic.id] ?? "";
}

function vizTable(title: string, head: string[], rows: string[][], note: string): string {
  const th = head.map((h) => `<th>${escapeHtml(h)}</th>`).join("");
  const body = rows
    .map((r) => `<tr>${r.map((c) => `<td>${escapeHtml(c)}</td>`).join("")}</tr>`)
    .join("");
  return `
    <div class="card">
      <div class="pane-title">${escapeHtml(title)}</div>
      <table class="viz-table">
        <thead><tr>${th}</tr></thead>
        <tbody>${body}</tbody>
      </table>
      <p class="prose muted stack-gap">${escapeHtml(note)}</p>
    </div>`;
}

function renderQuizItems(items: QuizItem[], idPrefix: string): string {
  return items
    .map((item, qi) => {
      const cover = item.covers
        ? `<p class="prose muted">覆盖：${escapeHtml(findTopic(item.covers)?.title ?? item.covers)}</p>`
        : "";
      const source = item.source?.trim()
        ? `<p class="quiz-source">来源：${escapeHtml(item.source.trim())}</p>`
        : "";
      const letters = "ABCDEFGH";
      const choices = item.choices
        .map(
          (c, ci) =>
            `<button type="button" class="quiz-opt" data-quiz="${idPrefix}-${qi}" data-ok="${c.ok ? "1" : "0"}" data-why="${escapeHtml(c.why)}">${letters[ci] ?? ci + 1}. ${escapeHtml(c.label)}</button>`,
        )
        .join("");
      return `<div class="quiz-item" data-quiz-item="${idPrefix}-${qi}">
        <div class="quiz-stem">
          <p class="quiz-stem-text"><strong>${qi + 1}.</strong> ${escapeHtml(item.stem)}</p>
          <span class="quiz-mark is-hidden" aria-hidden="true"></span>
        </div>
        ${cover}
        ${source}
        <div class="quiz-opts">${choices}</div>
        <p class="quiz-feedback muted">选一项查看解析。</p>
      </div>`;
    })
    .join("");
}

function wireQuiz(panel: HTMLElement, onPicked?: () => void) {
  panel.querySelectorAll<HTMLButtonElement>(".quiz-opt").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = btn.closest(".quiz-item");
      if (!item) return;
      const ok = btn.dataset.ok === "1";
      const why = btn.dataset.why ?? "";
      const box = item.querySelector(".quiz-feedback");
      if (box) {
        box.className = `quiz-feedback ${ok ? "is-ok" : "is-bad"}`;
        box.textContent = `${ok ? "答对。" : "答错。"} ${why}`;
      }

      item.classList.remove("is-correct", "is-wrong", "is-unanswered");
      item.classList.add(ok ? "is-correct" : "is-wrong");

      const stem = item.querySelector(".quiz-stem");
      if (stem) {
        let mark = stem.querySelector(".quiz-mark");
        if (!mark) {
          mark = document.createElement("span");
          mark.className = "quiz-mark";
          stem.appendChild(mark);
        }
        mark.className = `quiz-mark ${ok ? "is-ok" : "is-bad"}`;
        mark.textContent = ok ? "答对" : "答错";
        mark.removeAttribute("aria-hidden");
      }

      const group = btn.dataset.quiz;
      if (group) {
        panel.querySelectorAll<HTMLButtonElement>(`.quiz-opt[data-quiz="${group}"]`).forEach((b) => {
          b.classList.remove("is-picked", "is-correct", "is-wrong", "is-key");
          if (b === btn) {
            b.classList.add("is-picked", ok ? "is-correct" : "is-wrong");
          } else if (!ok && b.dataset.ok === "1") {
            // 答错时标出正解，便于对照
            b.classList.add("is-key");
          }
        });
      }
      onPicked?.();
      const store = (item.closest("[data-quiz-store]") as HTMLElement | null)?.dataset.quizStore;
      if (store) {
        const count = Number(
          (item.closest("[data-quiz-store]") as HTMLElement | null)?.dataset.quizCount ?? "0",
        );
        const host = item.closest("[data-quiz-store]") as HTMLElement;
        if (host && count > 0) persistQuizPicks(store, readQuizPicks(host, count));
      }
    });
  });
}

function examAnsweredCount(root: HTMLElement, itemCount: number): number {
  let n = 0;
  for (let qi = 0; qi < itemCount; qi += 1) {
    const row = root.querySelector(`[data-quiz-item$="-${qi}"]`);
    if (row?.querySelector(".quiz-opt.is-picked")) n += 1;
  }
  return n;
}

function updateCheckpointProgress(chapter: Chapter) {
  const pack = chapter.checkpoint;
  const root = document.getElementById("exam-quiz-root");
  const prog = document.getElementById("grade-progress");
  if (!pack?.items?.length || !root || !prog) return;
  const total = pack.items.length;
  const done = examAnsweredCount(root, total);
  if (done >= total) {
    prog.textContent = "已全部作答。";
  } else {
    prog.textContent = `已答 ${done}/${total}`;
  }
}

function masteryFromRatio(correct: number, total: number): number {
  if (total <= 0) return 0;
  const r = correct / total;
  if (r >= 1) return 5;
  if (r >= 0.8) return 4;
  if (r >= 0.6) return 3;
  if (r >= 0.4) return 2;
  if (r > 0) return 1;
  return 0;
}

function renderChapterExam(chapter: Chapter, kind: "checkpoint" | "finale"): string {
  const pack = kind === "checkpoint" ? chapter.checkpoint : chapter.assessment;
  if (!pack?.items?.length) {
    return `<div class="empty">本章暂无${kind === "checkpoint" ? "随堂" : "章末"}考核。</div>`;
  }
  const defaultTitle =
    kind === "checkpoint"
      ? `${chapter.title} · 随堂考核`
      : `${chapter.title} · 章末考核`;
  const covers = new Set(
    pack.items.map((it) => it.covers).filter((x): x is string => !!x),
  );
  const coverNote = covers.size
    ? `<p class="prose muted">覆盖知识点：${[...covers]
        .map((id) => escapeHtml(findTopic(id)?.title ?? id))
        .join("、")}</p>`
    : `<p class="prose muted">请为每题标注 covers（知识点 id），以便按题评判完成度。</p>`;

  const gradeBar =
    kind === "checkpoint"
      ? `<div class="lab-toolbar stack-gap">
          <span class="hint" id="grade-progress">逐题作答即可。</span>
        </div>
        <div id="grade-report" class="grade-report is-hidden"></div>`
      : `<p class="prose muted stack-gap">章末卷用于综合自检，不改完成度；完成度以左侧「随堂考核」为准。</p>`;

  const done = kind === "checkpoint" && isCheckpointDone(chapter);

  return `
    <div class="card${done ? " exam-card-done" : ""}">
      <h3>${escapeHtml(pack.title ?? defaultTitle)}${
        done ? ` <span class="badge badge-exam-done">已完成</span>` : ""
      }</h3>
      <p class="prose">${escapeHtml(
        pack.intro ??
          (kind === "checkpoint"
            ? "逐题作答；全部选完后自动按覆盖知识点的正确率更新完成度。"
            : "综合自检，不替代随堂考核的完成度评判。"),
      )}</p>
      ${coverNote}
      ${gradeBar}
    </div>
    <div class="quiz-set" id="exam-quiz-root" data-quiz-store="${escapeHtml(quizStoreKey(kind, chapter.id))}" data-quiz-count="${pack.items.length}">
      ${renderQuizItems(pack.items, `${kind}-${chapter.id}`)}
    </div>`;
}

let gradeInFlight = false;
let gradeAgain: Chapter | null = null;

async function gradeCheckpoint(chapter: Chapter, opts?: { requireComplete?: boolean }) {
  const pack = chapter.checkpoint;
  const report = document.getElementById("grade-report");
  const root = document.getElementById("exam-quiz-root");
  if (!pack?.items?.length || !root || !report) return;

  const requireComplete = opts?.requireComplete !== false;
  const byTopic = new Map<string, { correct: number; total: number }>();
  let answered = 0;
  let missing = 0;

  pack.items.forEach((item, qi) => {
    const topicId = item.covers ?? "";
    const row = root.querySelector(`[data-quiz-item$="-${qi}"]`);
    const picked = row?.querySelector<HTMLButtonElement>(".quiz-opt.is-picked");
    if (!picked) {
      missing += 1;
      return;
    }
    answered += 1;
    const ok = picked.dataset.ok === "1";
    if (!topicId) return;
    const slot = byTopic.get(topicId) ?? { correct: 0, total: 0 };
    slot.total += 1;
    if (ok) slot.correct += 1;
    byTopic.set(topicId, slot);
  });

  if (missing > 0) {
    if (requireComplete) {
      report.classList.add("is-hidden");
      report.textContent = "";
    }
    return;
  }

  if (gradeInFlight) {
    gradeAgain = chapter;
    return;
  }
  gradeInFlight = true;
  try {
    const lines: string[] = [];
    for (const [topicId, { correct, total }] of byTopic) {
      const level = masteryFromRatio(correct, total);
      try {
        await invoke("save_mastery", { topicId, mastery: level });
      } catch {
        /* 本地仍更新 */
      }
      state.mastery[topicId] = level;
      const title = findTopic(topicId)?.title ?? topicId;
      lines.push(`${title}：${correct}/${total} → 完成度 ${level}/5`);
    }

    // 无 covers 的题：按全章各知识点均摊一次总分（少见）
    if (byTopic.size === 0 && answered > 0) {
      let correctAll = 0;
      pack.items.forEach((_, qi) => {
        const row = root.querySelector(`[data-quiz-item$="-${qi}"]`);
        const picked = row?.querySelector<HTMLButtonElement>(".quiz-opt.is-picked");
        if (picked?.dataset.ok === "1") correctAll += 1;
      });
      const level = masteryFromRatio(correctAll, pack.items.length);
      for (const t of chapter.topics) {
        try {
          await invoke("save_mastery", { topicId: t.id, mastery: level });
        } catch {
          /* ignore */
        }
        state.mastery[t.id] = level;
        lines.push(
          `${t.title}：整卷 ${correctAll}/${pack.items.length} → 完成度 ${level}/5`,
        );
      }
    }

    report.classList.remove("is-hidden");
    report.className = "grade-report is-ok";
    report.innerHTML = `<strong>已自动评判</strong><ul>${lines.map((l) => `<li>${escapeHtml(l)}</li>`).join("")}</ul>`;
    const prog = document.getElementById("grade-progress");
    if (prog) {
      prog.textContent = "已全部作答。";
    }
    renderNav();
    renderMap();
  } finally {
    gradeInFlight = false;
    const again = gradeAgain;
    gradeAgain = null;
    if (again) void gradeCheckpoint(again);
  }
}

function typeLabel(t: string): string {
  if (t === "concept") return "概念";
  if (t === "skill") return "技能";
  if (t === "strategy") return "策略";
  return t;
}

function typeClass(t: string): string {
  return `badge badge-type badge-type-${t}`;
}

function renderLesson(topic: Topic) {
  const methodHint =
    topic.knowledge_type === "concept"
      ? "学法：看正反例边界，能自己举一个「是」和一个「不是」。"
      : topic.knowledge_type === "skill"
        ? "学法：先跟示范走一遍，再改条件做变式。"
        : topic.knowledge_type === "strategy"
          ? "学法：在情境里做选择，并说出判据——不选「听起来对」的项。"
          : "";

  const head = methodHint
    ? `<div class="callout"><div class="title">本知识点类型 · ${escapeHtml(typeLabel(topic.knowledge_type))}</div><div>${escapeHtml(methodHint)}</div></div>`
    : "";

  const body = topic.lesson.blocks
    .map((b, bi) => {
      if (b.type === "lead") {
        return `<div class="card"><p class="lead">${escapeHtml(b.text)}</p></div>`;
      }
      if (b.type === "callout") {
        const tone = b.tone === "warn" ? " warn" : "";
        return `<div class="callout${tone}"><div class="title">${escapeHtml(b.title ?? "提示")}</div><div>${escapeHtml(b.text)}</div></div>`;
      }
      if (b.type === "compare") {
        return `<div class="card">
          ${b.title ? `<h3>${escapeHtml(b.title)}</h3>` : ""}
          <div class="compare">
            <div class="compare-pane is-yes"><div class="compare-label">${escapeHtml(b.left.title)}</div><p class="prose">${escapeHtml(b.left.body)}</p></div>
            <div class="compare-pane is-no"><div class="compare-label">${escapeHtml(b.right.title)}</div><p class="prose">${escapeHtml(b.right.body)}</p></div>
          </div>
        </div>`;
      }
      if (b.type === "steps") {
        return `<div class="card">
          ${b.title ? `<h3>${escapeHtml(b.title)}</h3>` : ""}
          <ol class="steps">${b.items.map((it) => `<li>${escapeHtml(it)}</li>`).join("")}</ol>
        </div>`;
      }
      if (b.type === "predict") {
        const id = `pred-${Math.random().toString(36).slice(2, 8)}`;
        return `<div class="card predict" data-predict>
          <h3>先预测</h3>
          <p class="prose">${escapeHtml(b.question)}</p>
          <p class="prose muted">你心里的答案：<strong>${escapeHtml(b.expect)}</strong>（先想再点开）</p>
          <button type="button" class="reveal-btn" data-reveal="${id}">显示说明</button>
          <div id="${id}" class="reveal is-hidden"><p class="prose">${escapeHtml(b.explain)}</p></div>
          ${labJumpButton(topic, b.open_lab)}
        </div>`;
      }
      if (b.type === "scenario") {
        const opts = b.options
          .map(
            (o, i) =>
              `<button type="button" class="scenario-opt" data-ok="${o.ok ? "1" : "0"}" data-why="${escapeHtml(o.why)}">${i + 1}. ${escapeHtml(o.label)}</button>`,
          )
          .join("");
        return `<div class="card scenario">
          <h3>情境选择</h3>
          <p class="prose">${escapeHtml(b.situation)}</p>
          <div class="scenario-opts">${opts}</div>
          <p class="scenario-feedback muted">点一个选项，看判据是否站得住。</p>
          ${labJumpButton(topic, b.open_lab)}
        </div>`;
      }
      if (b.type === "practice") {
        return `<div class="card practice">
          <h3>变式练习</h3>
          <p class="prose">${escapeHtml(b.prompt)}</p>
          ${b.hint ? `<p class="prose muted">提示：${escapeHtml(b.hint)}</p>` : ""}
          ${labJumpButton(topic, b.open_lab)}
        </div>`;
      }
      if (b.type === "quiz") {
        const store = quizStoreKey("lesson", `${topic.id}:${bi}`);
        return `<div class="card quiz-set" data-quiz-store="${escapeHtml(store)}" data-quiz-count="${b.items.length}">
          <h3>${escapeHtml(b.title ?? "随堂测验")}</h3>
          ${renderQuizItems(b.items, `lesson-${topic.id}-${bi}`)}
        </div>`;
      }
      if (b.type === "summary") {
        return `<div class="card summary">
          <h3>${escapeHtml(b.title ?? "总结")}</h3>
          <p class="prose">${escapeHtml(b.text)}</p>
        </div>`;
      }
      return `<div class="card"><p class="prose">${escapeHtml(b.text)}</p></div>`;
    })
    .join("");

  return head + body;
}

function renderObserveBody(stdout: string): string {
  const lines = stdout
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  const keyed = lines.filter((l) => /^[\w.]+[=：]/.test(l) || /moves|n=|Θ|O\(|≈/.test(l));
  if (!keyed.length) {
    return `<div class="body muted">运行后，带 <code>key=value</code> 的输出行或案例打印的逐步状态会出现在这里，便于对照预期。</div>`;
  }
  const items = keyed
    .map((l) => `<li><code>${escapeHtml(l)}</code></li>`)
    .join("");
  return `<ul class="observe-kv">${items}</ul>`;
}

function renderLab(topic: Topic) {
  const labs = topicLabs(topic);
  if (!labs.length) {
    return `<div class="empty">本节尚未挂实验。</div>`;
  }
  const lab = currentLab(topic)!;
  state.labId = lab.id;

  // 标题已在 topic-head；此处只放「要做什么」——有 goal 用 goal，否则用 prompt，避免标题/题目重复。
  const task =
    lab.goal?.trim() ||
    lab.prompt?.trim() ||
    "在骨架里按 TODO 补全，用运行输出验证本节概念。";
  const hint = lab.hint?.trim() ?? "";
  const st = getLabStatus(topic.id, lab.id);

  return `
    <div class="lab-workspace">
      <div class="lab-brief ${labStatusClass(st)}">
        <div class="lab-brief-text">
          <p class="lab-brief-task"><span class="badge ${labStatusBadgeClass(st)}">${labStatusLabel(st)}</span> ${escapeHtml(task)}</p>
          ${hint ? `<p class="lab-brief-hint">${escapeHtml(hint)}</p>` : ""}
        </div>
        <button type="button" class="lab-reload" id="reload-btn" title="丢弃编辑器改动，重新读磁盘上的原文件">恢复原文</button>
      </div>
      <div class="lab-toolbar">
        <button type="button" class="primary lab-run" id="run-btn">运行</button>
        <button type="button" class="lab-format" id="format-btn">格式化</button>
        <span class="run-status" id="run-status" aria-live="polite"></span>
        <span class="hint">自动补括号 · Tab 缩进 · Ctrl-/ 注释</span>
      </div>
      <div class="lab-main">
        <div class="editor">
          <div class="code-host" id="source"></div>
        </div>
        <div class="side-stack">
          <div class="output" id="output">
            <div class="pane-title">编译 / 输出</div>
            <pre id="output-body">尚未运行</pre>
          </div>
          <div class="observe" id="observe">
            <div class="pane-title">观察区</div>
            ${renderObserveBody("")}
          </div>
        </div>
      </div>
    </div>`;
}

async function ensureLabSource(topic: Topic, lab: LabSpec): Promise<string> {
  const key = sourceKey(topic.id, lab.id);
  if (state.sourceByKey[key] != null) return state.sourceByKey[key];
  try {
    const src = hasTauri()
      ? await invoke<string>("load_case_source", {
          caseId: lab.case,
          entrypoint: lab.entrypoint,
        })
      : bundledCaseSource(lab.case, lab.entrypoint) ??
        (() => {
          throw new Error(
            `浏览器预览找不到打包案例 ${lab.case}/${lab.entrypoint}；请用 npm run tauri:dev 启动以读写磁盘并编译。`,
          );
        })();
    state.sourceByKey[key] = src;
    return src;
  } catch (err) {
    const fallback = `// 无法加载案例：${String(err)}\n`;
    state.sourceByKey[key] = fallback;
    return fallback;
  }
}

function wireLabWorkspace(topic: Topic) {
  document.getElementById("back-topic")?.addEventListener("click", () => {
    openTopic(topic.id, { tab: "brief" });
  });
  document.getElementById("back-lesson")?.addEventListener("click", () => {
    openTopic(topic.id, { tab: "lesson" });
  });
  document.getElementById("run-btn")?.addEventListener("click", (ev) => {
    ev.preventDefault();
    void runLab();
  });
  document.getElementById("format-btn")?.addEventListener("click", (ev) => {
    ev.preventDefault();
    void formatLabOnly();
  });
  document.getElementById("reload-btn")?.addEventListener("click", () => {
    const ok = window.confirm(
      "只在你点这一下时才恢复课程骨架。\n默认会保留你写过的代码；恢复后，本题草稿会被这份原文替换。",
    );
    if (!ok) return;
    void reloadSource();
  });
}

function setRunStatus(msg: string, kind: "idle" | "busy" | "ok" | "bad" = "idle") {
  const status = document.getElementById("run-status");
  const out = document.getElementById("output");
  if (status) {
    status.textContent = msg;
    status.className = `run-status is-${kind}`;
  }
  if (out) out.classList.toggle("is-error", kind === "bad");
}

function setOutputBody(text: string) {
  const body = document.getElementById("output-body");
  if (body) body.textContent = text;
}

/** 工具栏状态；只有还没有程序输出时，才把同一句话写进「编译 / 输出」。 */
function setRunFeedback(msg: string, kind: "idle" | "busy" | "ok" | "bad" = "idle") {
  setRunStatus(msg, kind);
  const body = document.getElementById("output-body");
  const empty = !body?.textContent?.trim() || body.textContent === "尚未运行";
  if (empty || kind === "busy") setOutputBody(msg);
}

async function refreshTopic() {
  const cur = state.curriculum;
  const chapter =
    state.stageMode === "topic"
      ? findChapterForTopic(state.topicId)
      : findChapter(state.chapterId);
  const topic = findTopic(state.topicId);

  if (!cur || !chapter) {
    $("panel").innerHTML = `<div class="empty">未找到章节。</div>`;
    return;
  }

  if (state.stageMode === "checkpoint" || state.stageMode === "finale") {
    const kind = state.stageMode === "checkpoint" ? "checkpoint" : "finale";
    const label = kind === "checkpoint" ? "随堂考核" : "章末考核";
    $("topic-head").innerHTML = `
      <h2>${escapeHtml(chapter.title)} · ${label}</h2>
      <p class="muted">${
        kind === "checkpoint"
          ? "逐题作答，全部选完后按正确率更新本章完成度。"
          : "综合自检；完成度以左侧「随堂考核」为准。"
      }</p>`;
    renderNav();
    syncTabs();
    const panel = $("panel");
    panel.classList.remove("is-lab");
    destroyLabEditor();
    panel.innerHTML = renderChapterExam(chapter, kind);
    if (kind === "checkpoint") {
      updateCheckpointProgress(chapter);
      wireQuiz(panel, () => {
        updateCheckpointProgress(chapter);
        void markCheckpointTried(chapter);
        void gradeCheckpoint(chapter);
      });
    } else {
      wireQuiz(panel);
    }
    const examRoot = document.getElementById("exam-quiz-root");
    if (examRoot) {
      restoreQuizPicks(examRoot, state.quizPicks[quizStoreKey(kind, chapter.id)]);
    }
    return;
  }

  if (state.stageMode === "lab") {
    if (!topic) {
      $("panel").innerHTML = `<div class="empty">未找到知识点。</div>`;
      return;
    }
    const lab = currentLab(topic);
    if (!lab) {
      $("panel").innerHTML = `<div class="empty">未找到实验。</div>`;
      return;
    }
    const labId = lab.id;
    $("topic-head").innerHTML = `
      <div class="topic-head-row">
        <h2>${escapeHtml(lab.title)}</h2>
        <div class="lab-head-actions">
          <button type="button" id="back-topic">回导读</button>
          <button type="button" id="back-lesson">回讲解</button>
        </div>
      </div>`;
    renderNav();
    syncTabs();
    const panel = $("panel");
    panel.classList.add("is-lab");
    // 先取源码再挂 DOM，避免 await 期间面板被重建导致按钮未绑定 / 编辑器挂到游离节点
    const source = await ensureLabSource(topic, lab);
    if (state.stageMode !== "lab" || state.labId !== labId) return;
    panel.innerHTML = renderLab(topic);
    const host = document.getElementById("source");
    if (host) {
      mountLabEditor(host, source, (text) => persistLabDraft(topic.id, lab.id, text));
    }
    wireLabWorkspace(topic);
    if (!hasTauri()) {
      setRunFeedback(
        "当前是浏览器预览，无法编译。请用 npm run tauri:dev 打开应用窗口后再点「运行」。",
        "bad",
      );
    }
    return;
  }

  if (!topic) {
    $("panel").innerHTML = `<div class="empty">未找到知识点。</div>`;
    return;
  }

  $("topic-head").innerHTML = `
    <h2>${escapeHtml(topic.title)}</h2>
    <p><span class="${typeClass(topic.knowledge_type)}">${typeLabel(topic.knowledge_type)}</span>
    ${escapeHtml(topic.guide_line)} · 完成度 ${state.mastery[topic.id] ?? 0}/5（随堂考核评定）</p>`;

  renderNav();
  syncTabs();

  const panel = $("panel");
  panel.classList.remove("is-lab");
  destroyLabEditor();
  if (state.tab === "lesson") {
    panel.innerHTML = renderLesson(topic);
    panel.querySelectorAll<HTMLButtonElement>("[data-reveal]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.reveal;
        if (!id) return;
        document.getElementById(id)?.classList.remove("is-hidden");
      });
    });
    panel.querySelectorAll<HTMLButtonElement>(".scenario-opt").forEach((btn) => {
      btn.addEventListener("click", () => {
        const card = btn.closest(".scenario");
        if (!card) return;
        const ok = btn.dataset.ok === "1";
        const why = btn.dataset.why ?? "";
        const box = card.querySelector(".scenario-feedback");
        if (box) {
          box.className = `scenario-feedback ${ok ? "is-ok" : "is-bad"}`;
          box.textContent = `${ok ? "答对。" : "答错。"} ${why}`;
        }
        card.classList.remove("is-correct", "is-wrong");
        card.classList.add(ok ? "is-correct" : "is-wrong");
        card.querySelectorAll<HTMLButtonElement>(".scenario-opt").forEach((b) => {
          b.classList.remove("is-picked", "is-correct", "is-wrong", "is-key");
          if (b === btn) {
            b.classList.add("is-picked", ok ? "is-correct" : "is-wrong");
          } else if (!ok && b.dataset.ok === "1") {
            b.classList.add("is-key");
          }
        });
      });
    });
    panel.querySelectorAll<HTMLButtonElement>("[data-open-lab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.openLab;
        if (id) openLab(id);
      });
    });
    wireQuiz(panel);
    panel.querySelectorAll<HTMLElement>("[data-quiz-store]").forEach((box) => {
      const key = box.dataset.quizStore;
      if (key) restoreQuizPicks(box, state.quizPicks[key]);
    });
  } else {
    panel.innerHTML = renderBrief(chapter, topic, cur);
    panel.querySelectorAll<HTMLButtonElement>("[data-topic]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.topic;
        if (id) openTopic(id, { tab: "brief" });
      });
    });
  }
}

async function reloadSource() {
  const topic = findTopic(state.topicId);
  const lab = topic ? currentLab(topic) : null;
  if (!topic || !lab) return;
  try {
    const src = hasTauri()
      ? await invoke<string>("load_case_source", {
          caseId: lab.case,
          entrypoint: lab.entrypoint,
        })
      : bundledCaseSource(lab.case, lab.entrypoint);
    if (src == null) {
      throw new Error(
        `找不到案例 ${lab.case}/${lab.entrypoint}。完整读写请用 npm run tauri:dev。`,
      );
    }
    state.sourceByKey[sourceKey(topic.id, lab.id)] = src;
    if (hasTauri()) {
      await invoke("clear_lab_draft", { labKey: sourceKey(topic.id, lab.id) }).catch(
        () => undefined,
      );
    }
    if (hasLabEditor()) setLabSource(src);
    else {
      const host = document.getElementById("source");
      if (host) mountLabEditor(host, src);
    }
  } catch (err) {
    const msg = `// 无法恢复磁盘原文：${String(err)}\n`;
    if (hasLabEditor()) setLabSource(msg);
  }
}

async function formatLabSource(): Promise<string> {
  let source = getLabSource();
  try {
    const formatted = hasTauri()
      ? await invoke<string>("format_cpp", { source })
      : formatCppFallback(source);
    if (formatted && formatted !== source) {
      source = formatted;
    } else if (!hasTauri()) {
      source = formatCppFallback(source);
    } else if (formatted === source) {
      const fallback = formatCppFallback(source);
      if (fallback !== source) source = fallback;
    }
  } catch {
    source = formatCppFallback(source);
  }
  if (source !== getLabSource()) setLabSource(source);
  return source;
}

function labActionButtons() {
  return {
    run: document.getElementById("run-btn") as HTMLButtonElement | null,
    format: document.getElementById("format-btn") as HTMLButtonElement | null,
  };
}

function setLabActionsDisabled(disabled: boolean) {
  const { run, format } = labActionButtons();
  if (run) run.disabled = disabled;
  if (format) format.disabled = disabled;
}

async function formatLabOnly() {
  const topic = findTopic(state.topicId);
  const lab = topic ? currentLab(topic) : null;
  if (!topic || !lab || !hasLabEditor()) {
    setRunStatus("编辑器未就绪，请从左侧再点一次该实验。", "bad");
    return;
  }
  setLabActionsDisabled(true);
  setRunStatus("格式化…", "busy");
  try {
    const source = await formatLabSource();
    persistLabDraftNow(topic.id, lab.id, source);
    setRunStatus("已格式化", "ok");
  } catch (err) {
    setRunStatus(`格式化失败：${String(err)}`, "bad");
  } finally {
    setLabActionsDisabled(false);
  }
}

async function runLab() {
  const topic = findTopic(state.topicId);
  const lab = topic ? currentLab(topic) : null;
  const observe = document.getElementById("observe");

  if (!topic || !lab) {
    setRunFeedback("未找到当前实验，请从左侧「本章实验」重新进入。", "bad");
    return;
  }
  if (!hasLabEditor()) {
    setRunFeedback("编辑器未就绪，请从左侧再点一次该实验。", "bad");
    return;
  }
  if (!hasTauri()) {
    const msg =
      "无法在浏览器里编译运行。请关闭本页，改用终端执行：\nnpm run tauri:dev\n在弹出的「数据结构与算法」窗口里点「运行」。";
    setRunFeedback(msg, "bad");
    window.alert(msg);
    return;
  }

  setLabActionsDisabled(true);
  setRunFeedback("格式化…", "busy");
  const source = await formatLabSource();
  persistLabDraftNow(topic.id, lab.id, source);
  setRunFeedback("编译中…", "busy");

  try {
    // 不写回 content/cases：否则 Vite 监听到改动会整页刷新，boot 又回到图谱。
    const result = await invoke<RunResult>("compile_and_run", {
      caseId: lab.case,
      entrypoint: lab.entrypoint,
      source,
    });
    const parts = [
      result.compile_log.trim() ? `【编译】\n${result.compile_log.trim()}` : "【编译】成功",
      result.stdout.trim() ? `【标准输出】\n${result.stdout.trim()}` : "",
      result.stderr.trim() ? `【标准错误】\n${result.stderr.trim()}` : "",
      `（${result.duration_ms} ms）`,
    ].filter(Boolean);
    const text = parts.join("\n\n");
    setOutputBody(text);
    if (observe) {
      // 有 #dsa-trace 快照走步进回放器（ADR 0004）；否则保持 key=value 文本模式。
      stopTracePlayback();
      const title = `<div class="pane-title">观察区</div>`;
      const frames = result.ok ? parseTrace(result.stdout) : [];
      if (frames.length) {
        observe.innerHTML = title;
        mountTracePlayer(observe, frames);
      } else {
        observe.innerHTML = title + renderObserveBody(result.ok ? result.stdout : "");
      }
    }

    if (!result.ok) {
      setRunStatus("编译或运行失败，见右侧输出", "bad");
      await persistLabStatus(topic.id, lab.id, "tried");
      renderNav();
      document.querySelector(".lab-brief")?.classList.remove("is-done", "is-tried", "is-todo");
      document.querySelector(".lab-brief")?.classList.add("is-tried");
      return;
    }

    const passed = labOutputPasses(lab, result.stdout);
    if (passed) {
      setRunStatus("已完成", "ok");
      await persistLabStatus(topic.id, lab.id, "done");
    } else {
      setRunStatus("未完成：输出尚未符合本题预期", "bad");
      await persistLabStatus(topic.id, lab.id, "tried");
    }
    renderNav();
    const brief = document.querySelector(".lab-brief");
    if (brief) {
      brief.classList.remove("is-done", "is-tried", "is-todo");
      brief.classList.add(passed ? "is-done" : "is-tried");
      const badge = brief.querySelector(".lab-brief-task .badge");
      if (badge) {
        badge.className = `badge ${labStatusBadgeClass(passed ? "done" : "tried")}`;
        badge.textContent = labStatusLabel(passed ? "done" : "tried");
      }
    }
  } catch (err) {
    const msg = String(err);
    setRunStatus(msg, "bad");
    setOutputBody(msg);
    window.alert(`运行失败：\n${msg}`);
  } finally {
    setLabActionsDisabled(false);
  }
}

async function boot() {
  $("home-btn").addEventListener("click", () => {
    stashEditorSource();
    showView("map");
    renderMap();
  });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") stashEditorSource();
  });

  document.querySelectorAll<HTMLButtonElement>(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      stashEditorSource();
      state.tab = (tab.dataset.tab as TabId) ?? "brief";
      void refreshTopic();
    });
  });

  try {
    state.info = await invoke<AppInfo>("get_app_info");
  } catch {
    state.info = null;
  }

  try {
    state.curriculum = await invoke<Curriculum>("load_curriculum");
  } catch {
    state.curriculum = curriculumFallback as Curriculum;
  }

  try {
    state.mastery = await invoke<Record<string, number>>("load_all_mastery");
  } catch {
    state.mastery = {};
  }

  try {
    const raw = await invoke<Record<string, string>>("load_all_lab_status");
    state.labStatus = {};
    for (const [k, v] of Object.entries(raw ?? {})) {
      state.labStatus[k] =
        v === "done" ? "done" : v === "started" ? "started" : "tried";
    }
  } catch {
    state.labStatus = {};
  }

  try {
    const drafts = await invoke<Record<string, string>>("load_all_lab_drafts");
    state.sourceByKey = { ...state.sourceByKey, ...(drafts ?? {}) };
  } catch {
    /* 无草稿就用课程骨架 */
  }

  try {
    const rawPicks = await invoke<Record<string, string>>("load_all_quiz_picks");
    state.quizPicks = {};
    for (const [k, json] of Object.entries(rawPicks ?? {})) {
      try {
        const arr = JSON.parse(json) as Array<number | null>;
        if (Array.isArray(arr)) state.quizPicks[k] = arr;
      } catch {
        /* 跳过坏数据 */
      }
    }
  } catch {
    state.quizPicks = {};
  }

  const cur = state.curriculum!;
  $("app-title").textContent = cur.title;
  $("app-tagline").textContent = cur.tagline;
  const info = state.info;
  $("app-meta").textContent = info
    ? [
        "独立进度库",
        info.compiler ? `编译器 ${info.compiler}` : "未检测到 C++ 编译器",
      ].join(" · ")
    : hasTauri()
      ? "进度库未就绪"
      : "浏览器预览模式 · 实验保存/编译请用 npm run tauri:dev";

  showView("map");
  renderMap();
}

void boot();
