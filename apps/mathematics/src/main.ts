// Athena Mathematics — 前端入口。
// 内容驱动：界面按 content/ 下的 JSON 渲染，不为新增知识点或诊断项复制整页。

import { invoke } from "@tauri-apps/api/core";
import { TransformView, type Mat2, type Readout } from "./transform-view";
import { GraphView, type GraphNode } from "./graph-view";
import {
  renderDiagnostics,
  adviceOf,
  type Diagnostics,
  type Answer,
} from "./diagnostic";
import {
  speak,
  stopSpeech,
  speechAvailable,
  listVoices,
  getVoiceName,
  setVoiceName,
  getRate,
  setRate,
  voicesReady,
} from "./speak";

// ── 课表类型（只声明用到的字段）──────────────────
interface TextbookRef {
  kind?: string;
  note?: string;
  covers?: string[];
  prepares?: string[];
}
interface PredictOption {
  text: string;
  ok?: boolean;
  /** 选对时补一句它后面用在哪 */
  why?: string;
  /** 选错时说明这个选项通常是怎么想的——不是「你错了」（ADR 0014 第 5 节） */
  misread?: string;
}
interface Experiment {
  kind: string;
  id: string;
  title: string;
  prompt: string;
  /** 作答后把画布演到这个矩阵，让人自己看结果 */
  verify_m?: number[];
  options?: PredictOption[];
}
interface Topic {
  id: string;
  title: string;
  scope: string;
  difficulty: number;
  mastery_goal: string;
  ideas?: string[];
  requires: string[];
  textbook_ref: TextbookRef;
  syllabus_ref: string;
  hook?: { text: string };
  sources?: {
    intuition?: { site: string; title: string; url: string };
    rigorous?: { site: string; title: string; url: string };
    textbook?: string[];
    textbook_only?: boolean;
    note?: string;
  };
  widget?: string;
  widget_preset?: {
    m: number[];
    focus?: string | null;
    caption?: string;
    readout?: "arrows" | "full";
  };
  overview?: {
    asks: string;
    says: string;
    why_now: string;
    aha?: string;
    steps?: string[];
  };
  walkthrough?: {
    title: string;
    lines: Array<{ say: string; m: number[] }>;
  };
  experiments?: Experiment[];
}
interface Chapter {
  id: string;
  title: string;
  summary?: string;
  topics: Topic[];
}
interface Curriculum {
  title: string;
  chapters: Chapter[];
}

interface ProgressRow {
  topic_id: string;
  depth: string;
  status: string;
}
interface PredictionRow {
  topic_id: string;
  exp_id: string;
  picked: string;
  correct: boolean;
}

const app = document.getElementById("app")!;
let curriculum: Curriculum;
let diagnostics: Diagnostics;
const progress = new Map<string, string>();
const predictions = new Map<string, PredictionRow>();
const diagAnswers = new Map<string, Answer>();

type View = { kind: "diag" } | { kind: "graph" } | { kind: "topic"; id: string };
let view: View = { kind: "graph" };

const key = (a: string, b: string) => `${a}::${b}`;

/**
 * 正文里的重点标记。**文字** 着强调色，==文字== 加背景高亮。
 * 只标句内的关键处，不给整段铺底色——铺满等于没标。
 */
function rich(src: string): string {
  return src
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, '<b class="em">$1</b>')
    .replace(/==(.+?)==/g, '<mark class="hl">$1</mark>');
}

async function boot() {
  try {
    curriculum = await invoke<Curriculum>("load_curriculum");
    diagnostics = await invoke<Diagnostics>("load_diagnostics");
    shuffleOptions(diagnostics);
    for (const p of await invoke<ProgressRow[]>("load_all_progress")) {
      progress.set(key(p.topic_id, p.depth), p.status);
    }
    for (const p of await invoke<PredictionRow[]>("load_all_predictions")) {
      predictions.set(key(p.topic_id, p.exp_id), p);
      // 诊断作答与知识点预测共用 predictions 表，按 topic_id 前缀区分
      if (p.topic_id.startsWith("math.prereq.")) {
        diagAnswers.set(key(p.topic_id, p.exp_id), {
          picked: p.picked,
          correct: p.correct,
        });
      }
    }
  } catch (e) {
    app.innerHTML = `<div class="err">内容加载失败：${String(e)}</div>`;
    return;
  }
  await voicesReady();
  render();
  bindKeys();
}

/**
 * 每次打开都重排选项顺序。
 * 正确答案固定在某个位置会让人按位置选，诊断结果就分不清真懂还是蒙对——
 * 这正是诊断要避免的。已保存的作答按选项文字匹配，打乱不影响回显。
 */
function shuffleOptions(d: Diagnostics) {
  for (const g of d.groups) {
    for (const it of g.items) {
      const o = it.options;
      for (let i = o.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [o[i], o[j]] = [o[j], o[i]];
      }
    }
  }
}

function render() {
  app.innerHTML = `<nav id="side"></nav><section id="main"></section>`;
  renderSide();
  if (view.kind === "diag") renderDiagPage();
  else if (view.kind === "graph") renderGraphPage();
  else renderTopic(view.id);
}

function renderSide() {
  const side = document.getElementById("side")!;
  const all = flatTopics();
  const walked = all.filter((t) => topicSeen(t.id)).length;
  const pct = all.length ? Math.round((walked / all.length) * 100) : 0;

  const parts: string[] = [
    `<div class="brand">
       <h1>${curriculum.title}</h1>
       <div class="pass">第一遍 · 走通为准</div>
       <div class="bar"><span style="width:${pct}%"></span></div>
       <div class="bar-txt">${all.length} 节走过 ${walked} 节</div>
     </div>`,
  ];

  // 顶层只有两个去处：诊断和图谱。知识点之间的关系全部交给图谱表达，
  // 不在侧边栏重复列表——进了一节还把另外十几节摆在旁边，是纯粹的噪音
  // （ADR 0011 第 6 节：只暴露当前需要的自由度）。
  const passedGroups = diagnostics.groups.filter(
    (g) =>
      g.items.every((it) => diagAnswers.has(key(g.id, it.id))) &&
      g.items.every((it) => diagAnswers.get(key(g.id, it.id))!.correct),
  ).length;
  parts.push(`<div class="chapter-title">去哪里</div>`);
  parts.push(
    `<button class="topic${view.kind === "diag" ? " active" : ""}" data-diag="1">
       ${diagnostics.title}
       <span class="meta">${
         passedGroups
           ? `<span class="dot">✓ ${passedGroups} / ${diagnostics.groups.length} 组已通过</span>`
           : `共 ${diagnostics.groups.length} 组`
       }</span>
     </button>`,
  );
  parts.push(
    `<button class="topic${view.kind === "graph" ? " active" : ""}" data-graph="1">
       线性代数图谱
       <span class="meta">${all.length} 节 · 按先修关系连起来</span>
     </button>`,
  );

  // 正在读某一节时，下面列的是这一节内部的结构
  if (view.kind === "topic") {
    const t = findTopic(view.id);
    if (t) {
      const at = all.findIndex((x) => x.id === t.id);
      const secs: Array<[string, string]> = [];
      if (t.sources) secs.push(["s-src", "出处"]);
      if (t.hook) secs.push(["s-hook", "为什么需要它"]);
      if (t.overview) secs.push(["s-ov", "讲什么"]);
      if (t.walkthrough) secs.push(["s-walk", "先看一遍"]);
      if (t.widget) secs.push(["s-widget", "动手试"]);
      if ((t.experiments ?? []).some((e) => e.options?.length)) secs.push(["s-ask", "先猜再验"]);
      if (t.textbook_ref.prepares?.length && t.widget) secs.push(["s-prep", "后面会回来"]);

      parts.push(
        `<div class="chapter-title cur">正在读 · 第 ${at + 1} / ${all.length} 节</div>`,
      );
      parts.push(`<div class="cur-title">${t.title}</div>`);
      for (const [id, label] of secs) {
        parts.push(`<button class="sec" data-sec="${id}">${label}</button>`);
      }
    }
  }

  side.innerHTML = parts.join("");

  side.querySelectorAll<HTMLButtonElement>(".topic").forEach((b) =>
    b.addEventListener("click", () => {
      stopGuide();
      view = b.dataset.diag ? { kind: "diag" } : { kind: "graph" };
      render();
      document.getElementById("main")!.scrollTop = 0;
    }),
  );
  side.querySelectorAll<HTMLButtonElement>(".sec").forEach((b) =>
    b.addEventListener("click", () => {
      document.getElementById(b.dataset.sec!)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }),
  );
}

/** 课表里的全部知识点，按拓扑序（JSON 的书写顺序即拓扑序，由 lint 保证可解） */
function flatTopics(): Topic[] {
  return curriculum.chapters.flatMap((c) => c.topics);
}

function topicSeen(id: string): boolean {
  return progress.has(key(id, "overview"));
}

/** 这一节有判对错的题，且全都答对了。没有这类题的节永远返回 false——不凭「看过」标绿。 */
function topicPassed(t: Topic): boolean {
  const judged = (t.experiments ?? []).filter((e) => e.options?.length);
  if (!judged.length) return false;
  return judged.every((e) => predictions.get(key(t.id, e.id))?.correct === true);
}

/**
 * 里程碑。学习天然缺少「做完了」的时刻，要主动造出来——
 * 这是成年自学者最受用的一种激励（ADR 0011 第 4 节第 5 项）。
 * 内容全部来自实际进度，不是撒花动画。
 */
function milestoneHtml(t: Topic, all: Topic[]): string {
  const ch = curriculum.chapters.find((c) => c.topics.some((x) => x.id === t.id));
  if (!ch) return "";
  const isChapterEnd = ch.topics[ch.topics.length - 1].id === t.id;
  const chapterDone = ch.topics.every((x) => topicSeen(x.id));
  const allDone = all.every((x) => topicSeen(x.id));

  if (allDone && all[all.length - 1].id === t.id) {
    const passed = all.filter(topicPassed).length;
    return `<div class="milestone big">
        <h3>第一遍走完了</h3>
        <p>${all.length} 节全部走过${passed ? `，其中 ${passed} 节的判断题也答对了` : ""}。
        这一遍的产物是一张全局地图：矩阵是把平面搬一次，行列式是面积伸缩比，
        秩是压到几维，特征向量是没被转走的方向，二次型是那个图形自己的轴。</p>
        <p class="next-pass">下一遍（机制与边界）再回到同样的顺序，
        每一节都会第二次见面——那时你已经知道它后面连着什么。</p>
      </div>`;
  }
  if (isChapterEnd && chapterDone) {
    return `<div class="milestone">
        <h3>「${ch.title}」走完了</h3>
        <p>${ch.summary ?? ""}这一章的 ${ch.topics.length} 节都走过了。</p>
      </div>`;
  }
  return "";
}

function goTo(id: string) {
  stopGuide();
  view = { kind: "topic", id };
  render();
  document.getElementById("main")!.scrollTop = 0;
}

/** ← → 翻页：少一次找鼠标、找目录，就少一个走神的缺口（ADR 0011 第 6 节） */
function bindKeys() {
  document.addEventListener("keydown", (e) => {
    if (view.kind !== "topic") return;
    const tag = (e.target as HTMLElement)?.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA") return;
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    const all = flatTopics();
    const at = all.findIndex((x) => x.id === (view as { id: string }).id);
    const to = e.key === "ArrowLeft" ? all[at - 1] : all[at + 1];
    if (to) {
      e.preventDefault();
      goTo(to.id);
    }
  });
}

function scopeLabel(scope: string): string {
  if (scope === "math2") return "考纲内";
  if (scope === "beyond") return "拓展";
  if (scope === "prereq") return "前置";
  return scope;
}

// ── 图谱页 ─────────────────────────────────────
function renderGraphPage() {
  const main = document.getElementById("main")!;
  const all = flatTopics();
  const walked = all.filter((t) => topicSeen(t.id)).length;

  main.innerHTML = `
    <div class="page wide">
      <h2 class="title">线性代数图谱</h2>
      <p class="tagline">一切从「矩阵就是把平面搬一次」发散出去，最后收敛到二次型。
      连线是先修关系，由课表算出来，不是画上去的。</p>
      <div class="g-legend">
        <span><i class="sw-todo"></i>未走</span>
        <span><i class="sw-seen"></i>走过</span>
        <span><i class="sw-pass"></i>答对</span>
        <span class="g-tip">把鼠标停在任意一节上 → 点亮它全部的先修；点一下进入那一节</span>
      </div>
      <canvas id="graph" width="1400" height="1120"></canvas>
      <div class="g-foot">${all.length} 节走过 ${walked} 节。虚线内框表示考纲外的拓展节。</div>
    </div>`;

  const nodes: GraphNode[] = all.map((t) => ({
    id: t.id,
    title: t.title,
    requires: t.requires,
    seen: topicSeen(t.id),
    passed: topicPassed(t),
    scope: t.scope,
  }));
  const g = new GraphView(
    document.getElementById("graph") as HTMLCanvasElement,
    nodes,
    (id) => goTo(id),
  );
  g.draw();
}

// ── 诊断页 ─────────────────────────────────────
function renderDiagPage() {
  const main = document.getElementById("main")!;
  main.innerHTML = renderDiagnostics(diagnostics, diagAnswers);

  main.querySelectorAll<HTMLButtonElement>(".d-opt").forEach((b) =>
    b.addEventListener("click", () => {
      const g = b.dataset.g!;
      const i = b.dataset.i!;
      const picked = b.dataset.text!;
      const correct = b.dataset.ok === "1";

      diagAnswers.set(key(g, i), { picked, correct });
      void invoke("save_prediction", { topicId: g, expId: i, picked, correct });

      // 一组答完就把结论写进 progress：只存建议，不存分数（ADR 0015 第 4 节）
      const group = diagnostics.groups.find((x) => x.id === g)!;
      if (group.items.every((it) => diagAnswers.has(key(g, it.id)))) {
        const wrong = group.items.filter(
          (it) => !diagAnswers.get(key(g, it.id))!.correct,
        ).length;
        const advice = adviceOf(diagnostics.advice_rule, wrong);
        progress.set(key(g, "diagnostic"), advice);
        void invoke("save_progress", {
          topicId: g,
          depth: "diagnostic",
          status: advice,
        });
      }

      const y = main.scrollTop;
      renderSide();
      renderDiagPage();
      main.scrollTop = y;
    }),
  );
}

// ── 知识点页 ────────────────────────────────────
function findTopic(id: string): Topic | undefined {
  for (const ch of curriculum.chapters) {
    const t = ch.topics.find((x) => x.id === id);
    if (t) return t;
  }
  return undefined;
}

function renderTopic(id: string) {
  const main = document.getElementById("main")!;
  const t = findTopic(id);
  if (!t) {
    main.innerHTML = `<div class="err">没有找到这个知识点。</div>`;
    return;
  }

  const ref = t.textbook_ref;
  const coord = [
    `<div class="row"><b>教材坐标</b>　${
      ref.kind === "cross_chapter"
        ? "跨章导入 · 教材无此独立节"
        : (ref.covers || []).join(" · ") || ref.note || ""
    }</div>`,
    ref.kind === "cross_chapter" && ref.covers?.length
      ? `<div class="row">　覆盖：${ref.covers.join(" · ")}</div>`
      : "",
    ref.prepares?.length
      ? `<div class="row">　预铺：${ref.prepares.map((s) => s.split(" —— ")[0]).join(" · ")}</div>`
      : "",
    `<div class="row"><b>大纲坐标</b>　${t.syllabus_ref}</div>`,
  ].join("");

  const src = t.sources;
  const srcHtml = src
    ? `<div id="s-src" class="src${src.textbook_only ? " only-book" : ""}">
        <div class="src-t">这一节的出处</div>
        ${
          src.intuition
            ? `<div class="src-row"><span class="src-k">直觉</span>
                 <a href="${src.intuition.url}" target="_blank" rel="noreferrer">${src.intuition.site} · ${src.intuition.title}</a></div>`
            : ""
        }
        ${
          src.rigorous
            ? `<div class="src-row"><span class="src-k">严格表述</span>
                 <a href="${src.rigorous.url}" target="_blank" rel="noreferrer">${src.rigorous.site} · ${src.rigorous.title}</a></div>`
            : ""
        }
        ${
          src.textbook?.length
            ? `<div class="src-row"><span class="src-k">教材</span><span>${src.textbook.join(" · ")}</span></div>`
            : ""
        }
        ${src.note ? `<div class="src-note">${src.note}</div>` : ""}
      </div>`
    : "";

  const ov = t.overview;
  const predict = (t.experiments || []).find((e) => e.options?.length);
  const prev = predict ? predictions.get(key(t.id, predict.id)) : undefined;

  // 第一遍只走 overview 层：极薄，走完即可，不设挡路考核（ADR 0012 第 2 节）
  const overviewHtml = ov
    ? `<div id="s-ov" class="ov">
         <div class="ov-asks"><span class="ov-tag">这一节问什么</span>${rich(ov.asks)}</div>
         <p class="ov-says">${rich(ov.says)}</p>
         ${
           ov.steps?.length
             ? `<ol class="ov-steps">${ov.steps.map((s) => `<li>${rich(s)}</li>`).join("")}</ol>`
             : ""
         }
         ${ov.aha ? `<div class="ov-aha"><span class="ov-tag">值得记住的一点</span>${rich(ov.aha)}</div>` : ""}
         <p class="ov-why"><b>它在哪一环：</b>${ov.why_now}</p>
       </div>`
    : "";

  const walk = t.walkthrough;
  const walkHtml = walk
    ? `<div id="s-walk" class="walk">
         <div class="walk-bar">
           <button type="button" class="walk-play" id="walk-play">${walk.title}</button>
           <button type="button" class="walk-stop" id="walk-stop">停</button>
           ${speechAvailable() ? voiceControls() : ""}
         </div>
         <p class="walk-line" id="walk-line">点上面按钮，图会动、会出声。也可以不听，直接拖。</p>
       </div>`
    : "";

  const pre = t.widget_preset;
  const f = (k: string) => (pre?.focus === k ? ' class="focus"' : "");
  const widgetHtml =
    t.widget === "transform2d"
      ? `<div id="s-widget" class="stage">
        <div>
        <canvas id="cv" width="1360" height="1020"></canvas>
        ${pre?.caption ? `<p class="cv-cap">${rich(pre.caption)}</p>` : ""}
        </div>
        <div class="panel">
          <h3>这一次的搬法</h3>
          <div class="mat">
            <span class="brk">[</span>
            <div class="cells">
              <input id="m-a" value="1"><input id="m-b" value="0">
              <input id="m-c" value="0"><input id="m-d" value="1">
            </div>
            <span class="brk">]</span>
          </div>
          <div class="legend">
            第一列 <i class="a">蓝箭头</i>＝向右一格去哪<br>
            第二列 <i class="b">橙箭头</i>＝向上一格去哪
          </div>
          <div class="read" data-mode="${pre?.readout === "arrows" ? "arrows" : "full"}">
            <div id="r-i-row"><span class="k">蓝箭头现在在</span><span class="v" id="r-i">(1, 0)</span></div>
            <div id="r-j-row"><span class="k">橙箭头现在在</span><span class="v" id="r-j">(0, 1)</span></div>
            <div${f("det")} id="r-det-row"><span class="k">面积变成原来的</span><span class="v" id="r-det">1.00 倍</span></div>
            <div${f("flip")} id="r-flip-row"><span class="k">翻面了吗</span><span class="v" id="r-flip">没有</span></div>
            <div${f("rank")} id="r-rank-row"><span class="k">压到几维</span><span class="v" id="r-rank">2</span></div>
            <div${f("eig")} id="r-eig-row"><span class="k">方向不变的方向</span><span class="v" id="r-eig">绿色虚线</span></div>
          </div>
          <div class="presets">
            <button data-m="1,0,0,1">还原</button>
            <button data-m="0,-1,1,0">旋转 90°</button>
            <button data-m="2,0,0,2">放大 2 倍</button>
            <button data-m="1,1,0,1">切变</button>
            <button data-m="-1,0,0,1">镜像</button>
            <button data-m="1,2,2,4">压扁</button>
          </div>
        </div>
      </div>`
      : "";

  // 先乐观记下这一节已走过，下面的里程碑判断才能把它算进去
  progress.set(key(t.id, "overview"), "seen");

  // 当前在整条线的哪一步——「不知还要多久」的解药（ADR 0011 第 1 节）
  const all = flatTopics();
  const at = all.findIndex((x) => x.id === t.id);
  const prevTopic = at > 0 ? all[at - 1] : undefined;
  const nextTopic = at >= 0 && at < all.length - 1 ? all[at + 1] : undefined;

  // 先修状态：走过的明确回指，没走过的只提示不阻拦（ADR 0013 第 1 节「回指已有的成功」）
  const reqs = t.requires.map((r) => ({ t: findTopic(r), done: topicSeen(r) }));
  const reqHtml = reqs.length
    ? reqs.every((r) => r.done)
      ? `<div class="req ok">它依赖的内容你都走过了：${reqs
          .map((r) => r.t?.title ?? "")
          .join("、")}</div>`
      : `<div class="req todo">建议先看：${reqs
          .filter((r) => !r.done)
          .map((r) => `<button class="jump" data-id="${r.t?.id}">${r.t?.title ?? ""}</button>`)
          .join("、")}</div>`
    : "";

  main.innerHTML = `
    <div class="page">
      <div class="where">第 ${at + 1} 节 / 共 ${all.length} 节
        <button class="to-graph" data-graph="1">在图谱里看它的位置</button>
      </div>
      <div class="coord">${coord}</div>
      <h2 class="title">${t.title}</h2>
      ${reqHtml}
      ${srcHtml}
      ${t.hook ? `<div id="s-hook" class="hook"><p>${rich(t.hook.text)}</p></div>` : ""}
      ${overviewHtml}
      ${walkHtml}
      ${widgetHtml}
      ${predict ? renderPredict(predict, prev) : ""}
      ${
        ref.prepares?.length && t.widget
          ? `<div id="s-prep" class="prep"><h3>这一张图，后面每一章都会回来</h3><table>${ref.prepares
              .map((s) => {
                const [k, v] = s.split(" —— ");
                return `<tr><td>${k}</td><td>${v ?? ""}</td></tr>`;
              })
              .join("")}</table></div>`
          : ""
      }
      <div class="foot">
        <span>难度 ${t.difficulty} · ${scopeLabel(t.scope)} · 掌握目标 ${t.mastery_goal}</span>
        <span>${t.ideas?.length ? "思想：" + t.ideas.join(" · ") : ""}</span>
      </div>

      ${milestoneHtml(t, all)}

      <nav class="stepper">
        ${
          prevTopic
            ? `<button class="step prev" data-id="${prevTopic.id}">
                 <span class="step-k">← 上一节</span><span class="step-t">${prevTopic.title}</span>
               </button>`
            : "<span></span>"
        }
        ${
          nextTopic
            ? `<button class="step next" data-id="${nextTopic.id}">
                 <span class="step-k">下一节 →</span><span class="step-t">${nextTopic.title}</span>
               </button>`
            : `<span class="step-end">这是最后一节。第一遍走完了。</span>`
        }
      </nav>
      <div class="kbd-hint">也可以按 ← → 翻页</div>
    </div>`;

  // 读完一节，下一步必须一眼可见。回侧边栏找是摩擦，摩擦处就是分心的入口。
  main.querySelectorAll<HTMLButtonElement>(".step, .jump").forEach((b) =>
    b.addEventListener("click", () => goTo(b.dataset.id!)),
  );
  main.querySelector<HTMLButtonElement>(".to-graph")?.addEventListener("click", () => {
    stopGuide();
    view = { kind: "graph" };
    render();
    document.getElementById("main")!.scrollTop = 0;
  });

  if (t.widget === "transform2d") mountCanvas(pre?.m, pre?.readout ?? "full");
  if (walk) bindWalkthrough(t);
  if (predict) bindPredict(t, predict);
  void invoke("save_progress", { topicId: t.id, depth: "overview", status: "seen" });
  renderSide();
}

function renderPredict(e: Experiment, prev?: PredictionRow): string {
  const opts = [...(e.options ?? [])];
  // 正确答案固定在某个位置会让人按位置选，每次进页面重排一次
  for (let i = opts.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [opts[i], opts[j]] = [opts[j], opts[i]];
  }
  return `
    <div id="s-ask" class="ask">
      <h3>${e.title}</h3>
      <p class="q">${rich(e.prompt)}</p>
      <div class="opts">
        ${opts
          .map(
            (o) =>
              `<button data-pick="${o.text.replace(/"/g, "&quot;")}" data-ok="${
                o.ok ? 1 : 0
              }">${o.text}</button>`,
          )
          .join("")}
      </div>
      <div class="verdict" id="verdict"></div>
      ${
        prev
          ? `<div class="again">上次你选的是「${prev.picked}」，${
              prev.correct ? "当时就对了" : "当时没对上"
            }。</div>`
          : ""
      }
    </div>`;
}

let guideToken = 0;

function stopGuide() {
  guideToken += 1;
  stopSpeech();
  const view = (window as unknown as { __view?: TransformView }).__view;
  view?.cancelAnimation();
  const line = document.getElementById("walk-line");
  if (line && !line.dataset.keep) {
    line.classList.remove("is-on");
  }
}

/**
 * 语速与音色的现场调节。系统 API 不给性别字段，哪个听着更年轻因人而异，
 * 所以列表只做排序建议，另给试听——由使用者自己定（ADR 0011 第 4 节第 3 项）。
 */
function voiceControls(): string {
  const vs = listVoices();
  if (!vs.length) return "";
  const cur = getVoiceName();
  const rate = getRate();
  const rates: Array<[number, string]> = [
    [0.9, "慢"],
    [1.0, "常速"],
    [1.1, "稍快"],
    [1.25, "快"],
    [1.45, "更快"],
  ];
  return `<span class="walk-voice">
      <label>语速
        <select id="walk-rate">
          ${rates
            .map(
              ([r, label]) =>
                `<option value="${r}"${Math.abs(r - rate) < 0.01 ? " selected" : ""}>${label}</option>`,
            )
            .join("")}
        </select>
      </label>
      <label>声音
        <select id="walk-vname">
          ${vs
            .map(
              (v) =>
                `<option value="${v.name}"${v.name === cur ? " selected" : ""}>${v.name}</option>`,
            )
            .join("")}
        </select>
      </label>
      <button type="button" id="walk-try">试听</button>
    </span>`;
}

function bindWalkthrough(t: Topic) {
  const play = document.getElementById("walk-play");
  const stop = document.getElementById("walk-stop");
  play?.addEventListener("click", () => {
    void runWalkthrough(t);
  });
  const rateSel = document.getElementById("walk-rate") as HTMLSelectElement | null;
  const nameSel = document.getElementById("walk-vname") as HTMLSelectElement | null;
  const tryBtn = document.getElementById("walk-try");
  rateSel?.addEventListener("change", () => setRate(Number(rateSel.value)));
  nameSel?.addEventListener("change", () => {
    setVoiceName(nameSel.value);
    void speak("这是我的声音，语速是这样。");
  });
  tryBtn?.addEventListener("click", () => {
    void speak("两个箭头一旦指向同一条线，整张格子就塌成一条线。");
  });

  stop?.addEventListener("click", () => {
    stopGuide();
    const line = document.getElementById("walk-line");
    if (line) {
      line.textContent = "已停。可以自己拖箭头，或再点一次从头看。";
      line.classList.remove("is-on");
    }
  });
}

async function runWalkthrough(t: Topic) {
  const lines = t.walkthrough?.lines ?? [];
  const view = (window as unknown as { __view?: TransformView }).__view;
  const lineEl = document.getElementById("walk-line");
  if (!view || !lines.length || !lineEl) return;
  stopGuide();
  const token = ++guideToken;
  document.getElementById("s-widget")?.scrollIntoView({ behavior: "smooth", block: "center" });
  for (const step of lines) {
    if (token !== guideToken) return;
    const [a, b, c, d] = step.m;
    lineEl.textContent = step.say;
    lineEl.classList.add("is-on");
    const motion = view.animateTo({ a, b, c, d });
    const voice = speechAvailable()
      ? speak(step.say)
      : new Promise<void>((r) => setTimeout(r, 1600));
    await Promise.all([motion, voice]);
  }
  if (token !== guideToken) return;
  lineEl.textContent = "演完了。现在自己拖两根箭头，看格子怎么跟。";
  lineEl.classList.remove("is-on");
}

function mountCanvas(preset?: number[], readout: "arrows" | "full" = "full") {
  const cv = document.getElementById("cv") as HTMLCanvasElement;
  const ids = ["a", "b", "c", "d"] as const;
  const inputs = Object.fromEntries(
    ids.map((k) => [k, document.getElementById(`m-${k}`) as HTMLInputElement]),
  ) as Record<(typeof ids)[number], HTMLInputElement>;

  const v = new TransformView(
    cv,
    (m, r) => {
      for (const k of ids) inputs[k].value = String(+m[k].toFixed(2));
      showReadout(m, r, readout);
    },
    { showEigen: readout === "full" },
  );

  cv.addEventListener("pointerdown", () => stopGuide());
  for (const k of ids) {
    inputs[k].addEventListener("input", () => {
      stopGuide();
      const m = { ...v.matrix };
      const val = parseFloat(inputs[k].value);
      if (!Number.isNaN(val)) {
        m[k] = val;
        v.set(m);
      }
    });
  }
  document.querySelectorAll<HTMLButtonElement>(".presets button").forEach((b) =>
    b.addEventListener("click", () => {
      stopGuide();
      const [a, bb, c, d] = b.dataset.m!.split(",").map(Number);
      v.set({ a, b: bb, c, d });
    }),
  );
  if (preset && preset.length === 4) {
    v.set({ a: preset[0], b: preset[1], c: preset[2], d: preset[3] });
  } else {
    v.draw();
  }
  (window as unknown as { __view: TransformView }).__view = v;
}

function fmtPair(x: number, y: number): string {
  return `(${x.toFixed(2)}, ${y.toFixed(2)})`;
}

function showReadout(m: Mat2, r: Readout, mode: "arrows" | "full") {
  const set = (id: string, text: string, alert = false) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    el.className = "v" + (alert ? " alert" : "");
  };
  set("r-i", fmtPair(m.a, m.c));
  set("r-j", fmtPair(m.b, m.d));
  if (mode === "full") {
    set("r-det", Math.abs(r.det).toFixed(2) + " 倍", Math.abs(r.det) < 1e-9);
    set("r-flip", r.flipped ? "翻了" : "没有", r.flipped);
    set("r-rank", String(r.rank), r.rank < 2);
    set(
      "r-eig",
      r.rank < 2 ? "已压扁" : r.eigenDirs.length ? "绿色虚线" : "一条也没有",
      r.rank < 2,
    );
  }
}

function bindPredict(t: Topic, e: Experiment) {
  document.querySelectorAll<HTMLButtonElement>(".opts button").forEach((b) =>
    b.addEventListener("click", () => {
      document.querySelectorAll(".opts button").forEach((x) => x.classList.remove("picked"));
      b.classList.add("picked");

      const picked = b.dataset.pick!;
      const correct = b.dataset.ok === "1";
      const chosen = (e.options ?? []).find((o) => o.text === picked);
      const right = (e.options ?? []).find((o) => o.ok);

      // 选完立刻把画布演到待验的矩阵：让人自己看，而不是只读一段文字
      if (e.verify_m?.length === 4) {
        const [a, bb, c, d] = e.verify_m;
        void (window as unknown as { __view?: TransformView }).__view?.animateTo({
          a,
          b: bb,
          c,
          d,
        });
      }

      const vd = document.getElementById("verdict")!;
      vd.className = "verdict show " + (correct ? "right" : "wrong");
      vd.innerHTML = correct
        ? `<b class="right">对了。</b>${rich(chosen?.why ?? "")}`
        : `<b class="wrong">这个选项通常是这么想的：</b>${rich(chosen?.misread ?? "")}` +
          (right
            ? `<div class="d-right">正确的是：${rich(right.text)}。${rich(right.why ?? "")}</div>`
            : "");

      void invoke("save_prediction", { topicId: t.id, expId: e.id, picked, correct }).then(
        () => {
          predictions.set(key(t.id, e.id), {
            topic_id: t.id,
            exp_id: e.id,
            picked,
            correct,
          });
          renderSide();
        },
      );
    }),
  );
}

void boot();
