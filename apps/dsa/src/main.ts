import { invoke } from "@tauri-apps/api/core";
import curriculumFallback from "../content/curriculum.json";
import "./styles.css";

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
    }
  | {
      type: "scenario";
      situation: string;
      options: { label: string; ok: boolean; why: string }[];
    }
  | { type: "practice"; prompt: string; hint?: string };

type Outline = {
  promise: string;
  pain: string;
  model: string;
  scope: string;
  judgment: string;
  landing: string;
};

type Lab = { case: string; entrypoint: string; hint?: string } | null;

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
  lab: Lab;
};

type Chapter = {
  id: string;
  title: string;
  summary: string;
  track?: string;
  topics: Topic[];
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

type TabId = "guide" | "outline" | "lesson" | "lab";
type ViewId = "map" | "topic";

const state = {
  curriculum: null as Curriculum | null,
  info: null as AppInfo | null,
  mastery: {} as Record<string, number>,
  view: "map" as ViewId,
  chapterId: "",
  topicId: "",
  tab: "guide" as TabId,
  source: "",
};

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

/** 按 requires 拓扑分层，同层再按课表顺序。 */
function layoutLayers(topics: Topic[]): Topic[][] {
  const byId = new Map(topics.map((t) => [t.id, t]));
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

function svgBadge(x: number, y: number, label: string, st: BadgeStyle): {
  svg: string;
  width: number;
} {
  const fontPx = 10.5;
  const width = Math.round(textWidth(label, fontPx)) + 15;
  const height = 19;
  const svg = `<g transform="translate(${x}, ${y})">
      <rect width="${width}" height="${height}" rx="9.5" ry="9.5" fill="${st.fill}" stroke="${st.stroke}" stroke-width="1"></rect>
      <text class="badge-text" x="${width / 2}" y="13.5" text-anchor="middle" fill="${st.ink}">${escapeHtml(label)}</text>
    </g>`;
  return { svg, width };
}

const NODE_W = 272;
const NODE_H = 132;
const TRACK_FALLBACK = "#0a58ca";

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
  const gapX = 26;
  const gapY = 86;
  const padX = 60;
  const padY = 34;
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
      edges.push(
        `<path class="graph-edge${strong ? " strong" : ""}" stroke="${color}" d="M${x0} ${y0} C${x0} ${mid}, ${x1} ${mid}, ${x1} ${y1 - 7}" marker-end="url(#${markerId})" />`,
      );
    }
  }

  const textX = 28;
  const textW = NODE_W - textX - 16;
  const nodes = [...pos.values()]
    .map(({ x, y, t }) => {
      const color = colorOf(t);
      const chapter = chapterOf.get(t.id);
      const mastery = state.mastery[t.id] ?? 0;

      const pipW = 7;
      const pipGap = 2;
      const pipsX = NODE_W - 16 - (pipW * 5 + pipGap * 4);
      const pips = Array.from({ length: 5 }, (_, i) =>
        `<rect class="pip${i < mastery ? "" : " pip-off"}" x="${pipsX + i * (pipW + pipGap)}" y="17" width="${pipW}" height="12" rx="2"${i < mastery ? ` fill="${color}"` : ""}></rect>`,
      ).join("");

      const guideLines = elide(t.guide_line, textW, 11.5, 2)
        .map((line, i) => `<text class="guide" x="${textX}" y="${78 + i * 16}">${escapeHtml(line)}</text>`)
        .join("");

      const level = Math.min(5, Math.max(1, t.difficulty || 1));
      let bx = textX;
      const badges = [
        svgBadge(bx, NODE_H - 31, `D${t.difficulty}`, DIFFICULTY_STYLE[level - 1]),
      ];
      bx += badges[0].width + 6;
      const goal = svgBadge(
        bx, NODE_H - 31, goalLabel(t.mastery_goal),
        GOAL_STYLE[t.mastery_goal] ?? DIFFICULTY_STYLE[0],
      );
      badges.push(goal);
      bx += goal.width + 6;
      badges.push(
        svgBadge(
          bx, NODE_H - 31, typeLabel(t.knowledge_type),
          TYPE_STYLE[t.knowledge_type] ?? DIFFICULTY_STYLE[0],
        ),
      );

      const chapterTitle = elide(chapter?.title ?? "", textW - 60, 10.5, 1)[0] ?? "";

      return `<g class="graph-node" data-topic="${escapeHtml(t.id)}" transform="translate(${x}, ${y})">
        <title>${escapeHtml(`${t.title} — ${t.guide_line}`)}</title>
        <rect class="node-card" width="${NODE_W}" height="${NODE_H}" rx="14" ry="14" stroke="${mastery > 0 ? color : ""}"></rect>
        <rect x="13" y="16" width="4" height="${NODE_H - 32}" rx="2" fill="${color}"></rect>
        <text class="chapter" x="${textX}" y="27" fill="${color}">${escapeHtml(chapterTitle)}</text>
        ${pips}
        <text class="title" x="${textX}" y="54">${escapeHtml(t.title)}</text>
        ${guideLines}
        ${badges.map((b) => b.svg).join("")}
      </g>`;
    })
    .join("");

  // 交替的浅色横带，让"同一层没有先后"一眼看得出来。
  const bands = layers
    .map((_, li) =>
      li % 2 === 1
        ? `<rect class="layer-band" x="0" y="${padY + li * (NODE_H + gapY) - 14}" width="${width}" height="${NODE_H + 28}" rx="16"></rect>`
        : "",
    )
    .join("");

  const layerLabels = layers
    .map((layer, li) => {
      const y = padY + li * (NODE_H + gapY) + 20;
      return `<text class="layer-label" x="16" y="${y}">L${li} · ${layer.length}</text>`;
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
    g.addEventListener("click", () => {
      const id = g.dataset.topic;
      if (!id) return;
      openTopic(id);
    });
  });

  renderTrackLegend(cur, tracks);
  renderProgressPanel(cur, tracks);
  renderNodeLegend();
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

  $("stat-row").innerHTML = [
    { n: topics.length, label: "知识点" },
    { n: mastered, label: "已掌握（5）" },
    { n: doing, label: "学习中（1-4）" },
  ]
    .map((s) => `<div class="stat"><b>${s.n}</b><span>${s.label}</span></div>`)
    .join("");
  void untouched;

  $("chapter-stats").innerHTML = cur.chapters
    .map((ch) => {
      const color = tracks.get(ch.track ?? "")?.color ?? TRACK_FALLBACK;
      const total = ch.topics.length;
      const sum = ch.topics.reduce((acc, t) => acc + (state.mastery[t.id] ?? 0), 0);
      const done = ch.topics.filter((t) => (state.mastery[t.id] ?? 0) >= 5).length;
      const pct = total > 0 ? Math.round((sum / (total * 5)) * 100) : 0;
      return `<li title="${escapeHtml(ch.summary)}">
        <i style="background:${color}"></i>
        <span class="name">${escapeHtml(ch.title)}</span>
        <span class="num">${done}/${total} · ${pct}%</span>
        <span class="bar"><b style="width:${pct}%;background:${color}"></b></span>
      </li>`;
    })
    .join("");
}

function renderNodeLegend() {
  const pips = (on: number) =>
    Array.from({ length: 5 }, (_, i) => `<i class="${i < on ? "on" : ""}"></i>`).join("");
  $("legend-list").innerHTML = [
    ["左侧色条", "这个知识点属于哪条主线（见上方图例）"],
    [`<span class="pips">${pips(3)}</span>`, "熟练度 0–5，学完一节自己标"],
    ["D1–D5", "难度；颜色让给了主线，难度只用灰阶深浅"],
    ["精通 / 掌握 / 了解", "掌握目标，决定要投入到什么程度"],
    ["概念 / 技能 / 策略", "知识类型，决定该怎么学（ADR 0031）"],
    ["箭头", "先修关系；粗线表示后继要求精通或标了「先拿下」"],
  ]
    .map(([key, text]) => `<li><span class="key">${key}</span><span>${text}</span></li>`)
    .join("");
}

function openTopic(topicId: string) {
  const topic = findTopic(topicId);
  const chapter = findChapterForTopic(topicId);
  if (!topic || !chapter) return;
  state.topicId = topicId;
  state.chapterId = chapter.id;
  state.tab = "guide";
  state.source = "";
  showView("topic");
  void refreshTopic();
}

function renderNav() {
  const cur = state.curriculum;
  if (!cur) return;
  $("nav").innerHTML = cur.chapters
    .map((ch) => {
      const topics = ch.topics
        .map((t) => {
          const active = t.id === state.topicId ? " is-active" : "";
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
      return `<div class="chapter">
        <div class="chapter-title">${escapeHtml(ch.title)}</div>
        <p class="chapter-summary">${escapeHtml(ch.summary)}</p>
        ${topics}
      </div>`;
    })
    .join("");

  $("nav").querySelectorAll<HTMLButtonElement>("[data-topic]").forEach((btn) => {
    btn.addEventListener("click", () => {
      openTopic(btn.dataset.topic ?? "");
    });
  });
}

function syncTabs() {
  document.querySelectorAll<HTMLButtonElement>(".tab").forEach((tab) => {
    tab.classList.toggle("is-active", tab.dataset.tab === state.tab);
  });
}

function renderGuide(chapter: Chapter, topic: Topic, cur: Curriculum) {
  const inChapter = chapter.topics
    .map(
      (t) =>
        `<p class="prose"><strong>${escapeHtml(t.title)}</strong> — ${escapeHtml(t.guide_line)}
        <span class="${goalClass(t.mastery_goal)}">${goalLabel(t.mastery_goal)}</span></p>`,
    )
    .join("");
  return `
    <div class="card"><p class="lead">${escapeHtml(cur.tagline)}</p>
      <p class="prose muted" style="margin-top:8px">${escapeHtml(cur.description)}</p></div>
    <div class="card"><h3>本章 · ${escapeHtml(chapter.title)}</h3>
      <p class="prose">${escapeHtml(chapter.summary)}</p>
      <div style="margin-top:10px">${inChapter}</div></div>
    <div class="card"><h3>当前 · ${escapeHtml(topic.title)}</h3>
      <p class="prose">${escapeHtml(topic.guide_line)}</p>
      <p class="prose muted" style="margin-top:8px">先修：${
        topic.requires.length
          ? topic.requires
              .map((id) => escapeHtml(findTopic(id)?.title ?? id))
              .join("、")
          : "无"
      }</p></div>`;
}

function renderOutline(topic: Topic) {
  const o = topic.outline;
  return (
    [
      ["这一节要解决什么", o.promise],
      ["痛点与来历", o.pain],
      ["心智模型", o.model],
      ["讲什么与边界", o.scope],
      ["判断与代价", o.judgment],
      ["落点", o.landing],
    ] as [string, string][]
  )
    .map(
      ([title, body]) =>
        `<div class="card"><h3>${escapeHtml(title)}</h3><p class="prose">${escapeHtml(body)}</p></div>`,
    )
    .join("");
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
    .map((b) => {
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
        </div>`;
      }
      if (b.type === "practice") {
        return `<div class="card practice">
          <h3>变式练习</h3>
          <p class="prose">${escapeHtml(b.prompt)}</p>
          ${b.hint ? `<p class="prose muted">提示：${escapeHtml(b.hint)}</p>` : ""}
        </div>`;
      }
      return `<div class="card"><p class="prose">${escapeHtml(b.text)}</p></div>`;
    })
    .join("");

  return head + body;
}

function renderLab(topic: Topic) {
  if (!topic.lab) {
    return `<div class="empty">本节尚未挂实验。可先在图谱打开「大 O 表示法」体验保存并运行。</div>`;
  }
  return `
    <div class="lab">
      <div class="lab-toolbar">
        <button type="button" class="primary" id="run-btn">保存并运行</button>
        <button type="button" id="reload-btn">从磁盘重载</button>
        <button type="button" id="mastery-btn">标记熟练 +1</button>
        <span class="hint">${escapeHtml(topic.lab.hint ?? "")}</span>
      </div>
      <div class="editor">
        <div class="pane-title">C++ · ${escapeHtml(topic.lab.case)}/${escapeHtml(topic.lab.entrypoint)}</div>
        <textarea class="code" id="source" spellcheck="false"></textarea>
      </div>
      <div class="side-stack">
        <div class="output" id="output">
          <div class="pane-title">编译 / 输出</div>
          <pre id="output-body">尚未运行</pre>
        </div>
        <div class="observe">
          <div class="pane-title">观察区</div>
          <div class="body">后续在此接结构图 / 步进。当前请看编译输出中的步数对照。</div>
        </div>
      </div>
    </div>`;
}

async function refreshTopic() {
  const cur = state.curriculum;
  const topic = findTopic(state.topicId);
  const chapter = findChapterForTopic(state.topicId);
  if (!cur || !topic || !chapter) {
    $("panel").innerHTML = `<div class="empty">未找到知识点。</div>`;
    return;
  }

  $("topic-head").innerHTML = `
    <h2>${escapeHtml(topic.title)}</h2>
    <p><span class="${typeClass(topic.knowledge_type)}">${typeLabel(topic.knowledge_type)}</span>
    ${escapeHtml(topic.guide_line)} · 熟练度 ${state.mastery[topic.id] ?? 0}/5</p>`;

  renderNav();
  syncTabs();

  const panel = $("panel");
  if (state.tab === "guide") panel.innerHTML = renderGuide(chapter, topic, cur);
  else if (state.tab === "outline") panel.innerHTML = renderOutline(topic);
  else if (state.tab === "lesson") {
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
        const ok = btn.dataset.ok === "1";
        const why = btn.dataset.why ?? "";
        const box = btn.closest(".scenario")?.querySelector(".scenario-feedback");
        if (box) {
          box.className = `scenario-feedback ${ok ? "is-ok" : "is-bad"}`;
          box.textContent = `${ok ? "合适。" : "不合适。"} ${why}`;
        }
      });
    });
  } else panel.innerHTML = renderLab(topic);

  if (state.tab === "lab" && topic.lab) {
    const area = document.getElementById("source") as HTMLTextAreaElement | null;
    if (area) {
      if (!state.source) {
        try {
          state.source = await invoke<string>("load_case_source", {
            caseId: topic.lab.case,
            entrypoint: topic.lab.entrypoint,
          });
        } catch (err) {
          state.source = `// 无法加载案例：${String(err)}\n`;
        }
      }
      area.value = state.source;
    }
    document.getElementById("run-btn")?.addEventListener("click", () => void runLab());
    document.getElementById("reload-btn")?.addEventListener("click", () => void reloadSource());
    document.getElementById("mastery-btn")?.addEventListener("click", () => void bumpMastery());
  }
}

async function reloadSource() {
  const topic = findTopic(state.topicId);
  if (!topic?.lab) return;
  state.source = await invoke<string>("load_case_source", {
    caseId: topic.lab.case,
    entrypoint: topic.lab.entrypoint,
  });
  const area = document.getElementById("source") as HTMLTextAreaElement | null;
  if (area) area.value = state.source;
}

async function runLab() {
  const topic = findTopic(state.topicId);
  if (!topic?.lab) return;
  const area = document.getElementById("source") as HTMLTextAreaElement | null;
  const runBtn = document.getElementById("run-btn") as HTMLButtonElement | null;
  const out = document.getElementById("output");
  const body = document.getElementById("output-body");
  if (!area || !body || !out) return;

  state.source = area.value;
  if (runBtn) runBtn.disabled = true;
  body.textContent = "编译中…";
  out.classList.remove("is-error");

  try {
    await invoke("save_case_source", {
      caseId: topic.lab.case,
      entrypoint: topic.lab.entrypoint,
      source: state.source,
    });
    const result = await invoke<RunResult>("compile_and_run", {
      caseId: topic.lab.case,
      entrypoint: topic.lab.entrypoint,
    });
    const parts = [
      result.compile_log.trim() ? `【编译】\n${result.compile_log.trim()}` : "【编译】成功",
      result.stdout.trim() ? `【标准输出】\n${result.stdout.trim()}` : "",
      result.stderr.trim() ? `【标准错误】\n${result.stderr.trim()}` : "",
      `（${result.duration_ms} ms）`,
    ].filter(Boolean);
    body.textContent = parts.join("\n\n");
    out.classList.toggle("is-error", !result.ok);
  } catch (err) {
    body.textContent = String(err);
    out.classList.add("is-error");
  } finally {
    if (runBtn) runBtn.disabled = false;
  }
}

async function bumpMastery() {
  const topic = findTopic(state.topicId);
  if (!topic) return;
  const next = Math.min(5, (state.mastery[topic.id] ?? 0) + 1);
  try {
    await invoke("save_mastery", { topicId: topic.id, mastery: next });
  } catch {
    /* 无进度库时仍更新本地显示 */
  }
  state.mastery[topic.id] = next;
  await refreshTopic();
  renderMap();
}

async function boot() {
  $("home-btn").addEventListener("click", () => {
    showView("map");
    renderMap();
  });

  document.querySelectorAll<HTMLButtonElement>(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const area = document.getElementById("source") as HTMLTextAreaElement | null;
      if (area) state.source = area.value;
      state.tab = (tab.dataset.tab as TabId) ?? "guide";
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

  const cur = state.curriculum!;
  $("app-title").textContent = cur.title;
  $("app-tagline").textContent = cur.tagline;
  const info = state.info;
  $("app-meta").textContent = info
    ? [
        "独立进度库",
        info.compiler ? `编译器 ${info.compiler}` : "未检测到 C++ 编译器",
      ].join(" · ")
    : "浏览器预览模式";

  showView("map");
  renderMap();
}

void boot();
