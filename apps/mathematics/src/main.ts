// Athena Mathematics — 前端入口。
// 内容驱动：界面按 content/ 下的 JSON 渲染，不为新增知识点或诊断项复制整页。

import { invoke } from "@tauri-apps/api/core";
import { TransformView, readoutOf, type Mat2, type Readout } from "./transform-view";
import {
  renderDiagnostics,
  adviceOf,
  type Diagnostics,
  type Answer,
} from "./diagnostic";

// ── 课表类型（只声明用到的字段）──────────────────
interface TextbookRef {
  kind?: string;
  note?: string;
  covers?: string[];
  prepares?: string[];
}
interface Experiment {
  kind: string;
  id: string;
  title: string;
  prompt: string;
  answer?: string;
  why?: string;
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
  outline?: Record<string, string>;
  experiments?: Experiment[];
}
interface Chapter {
  id: string;
  title: string;
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

type View = { kind: "diag" } | { kind: "topic"; id: string };
let view: View = { kind: "diag" };

const key = (a: string, b: string) => `${a}::${b}`;

async function boot() {
  try {
    curriculum = await invoke<Curriculum>("load_curriculum");
    diagnostics = await invoke<Diagnostics>("load_diagnostics");
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
  render();
}

function render() {
  app.innerHTML = `<nav id="side"></nav><section id="main"></section>`;
  renderSide();
  if (view.kind === "diag") renderDiagPage();
  else renderTopic(view.id);
}

function renderSide() {
  const side = document.getElementById("side")!;
  const parts: string[] = [
    `<div class="brand"><h1>${curriculum.title}</h1>
     <div class="pass">第一遍 · 走通为准</div></div>`,
  ];

  // 诊断入口排在最前：先知道哪些要补，再决定路径（ADR 0015 第 4 节）
  const doneGroups = diagnostics.groups.filter((g) =>
    g.items.every((it) => diagAnswers.has(key(g.id, it.id))),
  ).length;
  parts.push(`<div class="chapter-title">开始之前</div>`);
  parts.push(
    `<button class="topic${view.kind === "diag" ? " active" : ""}" data-diag="1">
       ${diagnostics.title}
       <span class="meta">六组 · 已答完 ${doneGroups} 组</span>
     </button>`,
  );

  for (const ch of curriculum.chapters) {
    parts.push(`<div class="chapter-title">${ch.title}</div>`);
    for (const t of ch.topics) {
      const seen = progress.get(key(t.id, "overview"));
      parts.push(
        `<button class="topic${
          view.kind === "topic" && t.id === view.id ? " active" : ""
        }" data-id="${t.id}">
           ${t.title}
           <span class="meta">难度 ${t.difficulty} · ${scopeLabel(t.scope)}${
             seen ? ' · <span class="dot">看过</span>' : ""
           }</span>
         </button>`,
      );
    }
  }
  side.innerHTML = parts.join("");

  side.querySelectorAll<HTMLButtonElement>(".topic").forEach((b) =>
    b.addEventListener("click", () => {
      view = b.dataset.diag ? { kind: "diag" } : { kind: "topic", id: b.dataset.id! };
      render();
      document.getElementById("main")!.scrollTop = 0;
    }),
  );
}

function scopeLabel(scope: string): string {
  if (scope === "math2") return "考纲内";
  if (scope === "beyond") return "拓展";
  if (scope === "prereq") return "前置";
  return scope;
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
      ref.kind === "cross_chapter" ? "跨章导入 · 教材无此独立节" : ref.note || ""
    }</div>`,
    ref.covers?.length ? `<div class="row">　覆盖：${ref.covers.join(" · ")}</div>` : "",
    ref.prepares?.length
      ? `<div class="row">　预铺：${ref.prepares.map((s) => s.split(" —— ")[0]).join(" · ")}</div>`
      : "",
    `<div class="row"><b>大纲坐标</b>　${t.syllabus_ref}</div>`,
  ].join("");

  const predict = (t.experiments || []).find((e) => e.answer);
  const prev = predict ? predictions.get(key(t.id, predict.id)) : undefined;

  main.innerHTML = `
    <div class="page">
      <div class="coord">${coord}</div>
      <h2 class="title">${t.title}</h2>
      <p class="tagline">${t.outline?.promise ?? ""}</p>
      ${t.hook ? `<div class="hook"><p>${t.hook.text}</p></div>` : ""}

      <div class="stage">
        <canvas id="cv" width="1360" height="1020"></canvas>
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
          <div class="read">
            <div><span class="k">面积变成原来的</span><span class="v" id="r-det">1.00 倍</span></div>
            <div><span class="k">翻面了吗</span><span class="v" id="r-flip">没有</span></div>
            <div><span class="k">压到几维</span><span class="v" id="r-rank">2</span></div>
            <div><span class="k">方向不变的方向</span><span class="v" id="r-eig">绿色虚线</span></div>
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
      </div>

      ${predict ? renderPredict(predict, prev) : ""}

      ${
        ref.prepares?.length
          ? `<div class="prep"><h3>这一张图，后面每一章都会回来</h3><table>${ref.prepares
              .map((s) => {
                const [k, v] = s.split(" —— ");
                return `<tr><td>${k}</td><td>${v ?? ""}</td></tr>`;
              })
              .join("")}</table></div>`
          : ""
      }

      <div class="foot">
        <span>掌握目标：${t.mastery_goal} · 先修：${
          t.requires.length ? t.requires.join("、") : "无"
        }</span>
        <span>${t.ideas?.length ? "思想：" + t.ideas.join(" · ") : ""}</span>
      </div>
    </div>`;

  mountCanvas();
  if (predict) bindPredict(t, predict);
  void invoke("save_progress", { topicId: t.id, depth: "overview", status: "seen" }).then(
    () => {
      progress.set(key(t.id, "overview"), "seen");
    },
  );
}

function renderPredict(e: Experiment, prev?: PredictionRow): string {
  const opts = ["还是整张平面，只是被拉斜了", "缩成一条直线", "缩成一个点"];
  return `
    <div class="ask">
      <h3>${e.title}</h3>
      <p class="q">${e.prompt}</p>
      <div class="opts">
        ${opts.map((o) => `<button data-pick="${o}">${o}</button>`).join("")}
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

function mountCanvas() {
  const cv = document.getElementById("cv") as HTMLCanvasElement;
  const ids = ["a", "b", "c", "d"] as const;
  const inputs = Object.fromEntries(
    ids.map((k) => [k, document.getElementById(`m-${k}`) as HTMLInputElement]),
  ) as Record<(typeof ids)[number], HTMLInputElement>;

  const v = new TransformView(cv, (m, r) => {
    for (const k of ids) inputs[k].value = String(+m[k].toFixed(2));
    showReadout(r);
  });

  for (const k of ids) {
    inputs[k].addEventListener("input", () => {
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
      const [a, bb, c, d] = b.dataset.m!.split(",").map(Number);
      v.set({ a, b: bb, c, d });
    }),
  );
  v.draw();
  (window as unknown as { __view: TransformView }).__view = v;
}

function showReadout(r: Readout) {
  const set = (id: string, text: string, alert = false) => {
    const el = document.getElementById(id)!;
    el.textContent = text;
    el.className = "v" + (alert ? " alert" : "");
  };
  set("r-det", Math.abs(r.det).toFixed(2) + " 倍", Math.abs(r.det) < 1e-9);
  set("r-flip", r.flipped ? "翻了" : "没有", r.flipped);
  set("r-rank", String(r.rank), r.rank < 2);
  set(
    "r-eig",
    r.rank < 2 ? "已压扁" : r.eigenDirs.length ? "绿色虚线" : "一条也没有",
    r.rank < 2,
  );
}

function bindPredict(t: Topic, e: Experiment) {
  document.querySelectorAll<HTMLButtonElement>(".opts button").forEach((b) =>
    b.addEventListener("click", () => {
      document.querySelectorAll(".opts button").forEach((x) => x.classList.remove("picked"));
      b.classList.add("picked");

      const picked = b.dataset.pick!;
      const correct = picked === e.answer;

      const m: Mat2 = { a: 1, b: 2, c: 2, d: 4 };
      (window as unknown as { __view: TransformView }).__view.set(m);
      const r = readoutOf(m);

      const vd = document.getElementById("verdict")!;
      vd.className = "verdict show " + (correct ? "right" : "wrong");
      vd.innerHTML =
        (correct ? '<b class="right">对了。</b>' : '<b class="wrong">再看图。</b>') +
        `${e.why ?? ""}<br><br>右边「面积变成原来的」显示 <b>${Math.abs(r.det).toFixed(
          2,
        )} 倍</b>：面积没了，因为它已经不是面了。压扁之后回不去——落在同一点上的原像有无穷多个，你没法知道它原来在哪。<b>这就是「行列式为零 ⟺ 不可逆」</b>，先看见，第 1 章再用符号说一遍。`;

      void invoke("save_prediction", {
        topicId: t.id,
        expId: e.id,
        picked,
        correct,
      }).then(() => {
        predictions.set(key(t.id, e.id), {
          topic_id: t.id,
          exp_id: e.id,
          picked,
          correct,
        });
      });
    }),
  );
}

void boot();
