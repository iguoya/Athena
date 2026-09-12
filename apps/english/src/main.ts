// 前端入口：三个视图切换靠根元素的 data-view（overview / practice / mistakes），
// class 名与 docs/ui-sketch/ 的草图一一对应，样式表原样套用。
// 内容和进度由 backend 提供，排序、判定和组卷在 practice，这里只渲染和接事件。

import "./styles.css";
import { renderMarkdown } from "./markdown";
import {
  loadAppInfo,
  loadCurriculum,
  loadDeck,
  loadMastery,
  loadMistakes,
  loadReview,
  loadText,
  saveAnswer,
} from "./backend";
import {
  errorTagOf,
  examItems,
  gradeWriting,
  isDue,
  itemKindLabel,
  itemStem,
  itemSummary,
  orderItems,
  trackStats,
  weakItems,
  writingVerdict,
} from "./practice";
import type {
  Choice,
  Curriculum,
  Deck,
  DeckItem,
  MasteryState,
  Mistake,
  ReviewState,
  Stage,
  Track,
  Variant,
} from "./types";

function byId<T extends HTMLElement>(id: string): T {
  const node = document.getElementById(id);
  if (!node) {
    throw new Error(`页面缺少 #${id}`);
  }
  return node as T;
}

const root = byId("english-stage-map");
const dom = {
  title: byId("app-title"),
  subtitle: byId("app-subtitle"),
  backStage: byId<HTMLButtonElement>("back-stage"),
  btnDue: byId<HTMLButtonElement>("btn-due"),
  btnMistakes: byId<HTMLButtonElement>("btn-mistakes"),
  btnContinue: byId<HTMLButtonElement>("btn-continue"),

  stageList: byId("stage-list"),
  endpoint: byId("endpoint"),
  stageTitle: byId("stage-title"),
  stageGoal: byId("stage-goal"),
  stageBadge: byId("stage-badge"),
  gate: byId("gate"),
  tracks: byId("tracks"),
  lockNote: byId("lock-note"),

  practiceListTitle: byId("practice-list-title"),
  practiceCount: byId("practice-count"),
  itemList: byId("item-list"),
  practiceCrumb: byId("practice-crumb"),
  practiceTitle: byId("practice-title"),
  practiceGoal: byId("practice-goal"),
  practiceContext: byId("practice-context"),
  question: byId("question"),

  mistakeCount: byId("mistake-count"),
  mistakeList: byId("mistake-list"),
  mistakeDetail: byId("mistake-detail"),
};

interface TrackRuntime {
  stage: Stage;
  track: Track;
  deck: Deck;
  passage?: string;
}

type SessionMode = "practice" | "exam";

interface SessionItem {
  item: DeckItem;
  runtime: TrackRuntime;
}

interface Attempt {
  item: DeckItem;
  runtime: TrackRuntime;
  correct: boolean;
  picked: string;
  answer: string;
  why: string;
}

interface Session {
  listTitle: string;
  crumb: string;
  title: string;
  goal: string;
  mode: SessionMode;
  items: SessionItem[];
  index: number;
  answered: boolean;
  inVariant: boolean;
  variantDone: boolean;
  attempts: Attempt[];
}

const runtimes = new Map<string, TrackRuntime>();
let curriculum: Curriculum;
let review = new Map<string, ReviewState>();
let mastery = new Map<string, MasteryState>();
let mistakes: Mistake[] = [];
let currentStageId = "";
let currentMistakeId = "";
let session: Session | null = null;

function esc(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const now = (): number => Math.floor(Date.now() / 1000);
const pct = (value: number): string => `${Math.round(value * 100)}%`;

function trackPassed(track: Track): boolean {
  return (mastery.get(track.id)?.mastery ?? 0) === 1;
}

function stagePassed(stage: Stage): boolean {
  return stage.tracks.every(trackPassed);
}

function stageUnlocked(stage: Stage): boolean {
  return stage.requires.every((id) => {
    const required = curriculum.stages.find((other) => other.id === id);
    return required ? stagePassed(required) : true;
  });
}

function statsOf(runtime: TrackRuntime) {
  return trackStats(runtime.deck.items, review, mistakes, runtime.track.id, trackPassed(runtime.track), now());
}

function activeStage(): Stage {
  return curriculum.stages.find((stage) => !stagePassed(stage)) ?? curriculum.stages[curriculum.stages.length - 1]!;
}

function requiredTitles(stage: Stage): string {
  return stage.requires
    .map((id) => curriculum.stages.find((other) => other.id === id)?.title ?? id)
    .join("、");
}

function setView(view: "overview" | "practice" | "mistakes"): void {
  root.dataset.view = view;
}

/* --------------------------------------------------------------- 顶栏 */

function dueTotal(): number {
  let count = 0;
  const stamp = now();
  for (const state of review.values()) {
    if (isDue(state, stamp)) {
      count += 1;
    }
  }
  return count;
}

interface NextTask {
  label: string;
  run: () => void;
}

function nextTask(): NextTask | null {
  if (dueTotal() > 0) {
    return { label: "继续当前任务", run: startDueSession };
  }
  const stage = activeStage();
  for (const track of stage.tracks) {
    const runtime = runtimes.get(track.id);
    if (runtime && !trackPassed(track)) {
      return {
        label: `继续${track.title}`,
        run: () => startPractice(runtime, runtime.deck.items),
      };
    }
  }
  return null;
}

function renderTopBar(): void {
  const due = dueTotal();
  dom.btnDue.textContent = `今日复习 ${due}`;
  dom.btnDue.disabled = due === 0;
  dom.btnMistakes.textContent = `错题本 ${mistakes.length}`;
  dom.btnMistakes.disabled = mistakes.length === 0;
  const next = nextTask();
  dom.btnContinue.textContent = next ? "继续当前任务" : "三级都已通过";
  dom.btnContinue.title = next ? next.label : "";
  dom.btnContinue.disabled = next === null;
}

/* ----------------------------------------------------------- 能力路线 */

function renderStageList(): void {
  dom.stageList.innerHTML = curriculum.stages
    .map((stage, index) => {
      const passed = stagePassed(stage);
      const unlocked = stageUnlocked(stage);
      const status = passed ? "passed" : unlocked ? "current" : "locked";
      const done = stage.tracks.filter(trackPassed).length;
      const state = passed
        ? "单词 · 例句 · 作文已通过"
        : unlocked
          ? `三项已过 ${done} 项`
          : `三项达到${requiredTitles(stage)}后解锁`;
      return `<button class="english-stage" type="button" data-stage="${esc(stage.id)}" data-status="${status}"${
        unlocked ? "" : ' data-locked="true"'
      } aria-pressed="${stage.id === currentStageId}">
          <span class="english-stage-index">${passed ? "✓" : index + 1}</span>
          <span>
            <span class="english-stage-name">${esc(stage.title)} · ${esc(stage.subtitle)}</span>
            <span class="english-stage-state">${esc(state)}</span>
          </span>
        </button>`;
    })
    .join("");
}

function renderGate(stage: Stage): void {
  dom.gate.innerHTML = stage.tracks
    .map((track) => {
      const runtime = runtimes.get(track.id);
      if (!runtime) {
        return "";
      }
      const stats = statsOf(runtime);
      const detail = stats.passed
        ? `已通过 · 正确率 ${stats.accuracy === null ? "—" : pct(stats.accuracy)}`
        : stats.done === 0
          ? "待完成 · 还没开始"
          : `待完成 · 已练 ${stats.done}/${stats.total}`;
      return `<div class="english-gate-part">
          <span class="english-${stats.passed ? "check" : "wait"}">${stats.passed ? "✓" : "!"}</span>
          <span><strong>${esc(track.title)}考核</strong><br><small>${esc(detail)}</small></span>
        </div>`;
    })
    .join("");
}

function trackState(stats: ReturnType<typeof statsOf>): string {
  if (stats.passed) {
    return "考核已通过";
  }
  if (stats.done === 0) {
    return "尚未开始";
  }
  return stats.fresh === 0 ? "已具备考核条件" : "正在学习";
}

function renderTracks(stage: Stage): void {
  const focus = stage.tracks.find((track) => !trackPassed(track))?.id ?? null;
  dom.tracks.innerHTML = stage.tracks
    .map((track) => {
      const runtime = runtimes.get(track.id);
      if (!runtime) {
        return "";
      }
      const stats = statsOf(runtime);
      const isFocus = track.id === focus;
      const left =
        track.kind === "writing"
          ? "继续引导写作"
          : track.kind === "vocab"
            ? "复习薄弱词"
            : `再练 ${Math.max(1, Math.min(5, stats.total))} 句`;
      const right =
        track.kind === "writing"
          ? `<button type="button" data-rubric="${esc(track.id)}">查看评分维度</button>`
          : `<button type="button" data-exam="${esc(track.id)}"${isFocus ? " data-primary" : ""}>${
              stats.passed ? "再考一次" : `开始${track.title}考核`
            }</button>`;
      const measureRight = stats.due > 0 ? `到期复习 ${stats.due}` : stats.weakTag ? `薄弱：${stats.weakTag}` : "暂无薄弱项";
      const measureLeft =
        stats.accuracy === null ? `练习覆盖 ${pct(stats.coverage)}` : `近期正确率 ${pct(stats.accuracy)}`;
      return `<section class="english-track">
          <div class="english-track-top"><h3>${esc(track.title)}</h3><span class="english-track-state">${esc(
            trackState(stats),
          )}</span></div>
          <p class="english-track-desc">${esc(track.goal)}</p>
          <div class="english-meter"><span style="width: ${pct(stats.coverage)}"></span></div>
          <div class="english-measure"><span>${esc(measureLeft)}</span><span>${esc(measureRight)}</span></div>
          <div class="english-track-actions">
            <button type="button" data-weak="${esc(track.id)}">${esc(left)}</button>
            ${right}
          </div>
        </section>`;
    })
    .join("");
}

function renderStageDetail(): void {
  const stage = curriculum.stages.find((item) => item.id === currentStageId) ?? activeStage();
  currentStageId = stage.id;
  const passed = stagePassed(stage);
  const unlocked = stageUnlocked(stage);

  dom.stageTitle.textContent = `${stage.title} · ${stage.subtitle}`;
  dom.stageGoal.textContent = stage.goal;
  dom.stageBadge.textContent = passed ? "已通过" : unlocked ? "当前阶段" : "预览";

  renderGate(stage);
  renderTracks(stage);

  dom.lockNote.style.display = unlocked ? "none" : "block";
  dom.lockNote.textContent = unlocked
    ? ""
    : `完成${requiredTitles(stage)}的单词、例句与作文考核后，${stage.title}自动解锁。`;
}

function showOverview(): void {
  session = null;
  setView("overview");
  renderTopBar();
  renderStageList();
  renderStageDetail();
}

async function backToOverview(): Promise<void> {
  await refreshProgress();
  showOverview();
}

/* ------------------------------------------------------------- 练习台 */

function openSession(next: Session, passage?: string): void {
  if (next.items.length === 0) {
    return;
  }
  session = next;
  setView("practice");
  dom.backStage.textContent = "← 返回路线";
  dom.practiceListTitle.textContent = next.listTitle;
  dom.practiceCrumb.textContent = next.crumb;
  dom.practiceTitle.textContent = next.title;
  dom.practiceGoal.textContent = next.goal;
  if (passage) {
    dom.practiceContext.className = "english-context english-markdown";
    dom.practiceContext.innerHTML = renderMarkdown(passage);
  }
  renderCard();
}

function sessionOf(runtime: TrackRuntime, items: DeckItem[], mode: SessionMode, title: string): Session {
  return {
    listTitle: `${runtime.track.title}${mode === "exam" ? "考核" : "练习"}`,
    crumb: `${runtime.stage.title} · ${runtime.track.title}`,
    title,
    goal: runtime.track.goal,
    mode,
    items: items.map((item) => ({ item, runtime })),
    index: 0,
    answered: false,
    inVariant: false,
    variantDone: false,
    attempts: [],
  };
}

function startPractice(runtime: TrackRuntime, items: DeckItem[], focusId?: string): void {
  const ordered = orderItems(items, review, now());
  const next = sessionOf(runtime, ordered, "practice", "先判断，再看解析");
  const index = focusId ? ordered.findIndex((item) => item.id === focusId) : 0;
  next.index = index >= 0 ? index : 0;
  openSession(next, runtime.passage);
}

function startExam(runtime: TrackRuntime): void {
  const items = examItems(runtime.deck, review, now());
  const next = sessionOf(runtime, items, "exam", "成套作答，交卷后统一反馈");
  next.goal = "作答期间不给解析，也不显示答案；全部答完一次性出分。";
  openSession(next, runtime.passage);
}

function startDueSession(): void {
  const stamp = now();
  const items: SessionItem[] = [];
  for (const runtime of runtimes.values()) {
    for (const item of orderItems(runtime.deck.items, review, stamp)) {
      const state = review.get(item.id);
      if (state && isDue(state, stamp)) {
        items.push({ item, runtime });
      }
    }
  }
  openSession({
    listTitle: "今日复习",
    crumb: "跨轨检索",
    title: "先把到期的做完",
    goal: "今天该回头看的题排在一起，做完再推进新内容。",
    mode: "practice",
    items,
    index: 0,
    answered: false,
    inVariant: false,
    variantDone: false,
    attempts: [],
  });
}

function current(): SessionItem | null {
  return session ? (session.items[session.index] ?? null) : null;
}

function itemStatus(item: DeckItem, stamp: number): string {
  const state = review.get(item.id);
  if (!state) {
    return "新题";
  }
  if (state.last_rating !== null && state.last_rating < 3) {
    return "错过";
  }
  return isDue(state, stamp) ? "到期" : "后续";
}

function renderSide(): void {
  const active = session;
  if (!active) {
    return;
  }
  const stamp = now();
  const exam = active.mode === "exam";
  const due = active.items.filter((entry) => isDue(review.get(entry.item.id), stamp)).length;
  dom.practiceCount.textContent = exam
    ? `共 ${active.items.length} 题 · 作答中`
    : `${due} 条到期 / 共 ${active.items.length} 条`;
  dom.itemList.innerHTML = active.items
    .map((entry, position) => {
      const label = exam ? `第 ${position + 1} 题` : itemSummary(entry.item);
      const note = exam
        ? position < active.index
          ? "已答"
          : position === active.index
            ? "作答中"
            : "未答"
        : itemStatus(entry.item, stamp);
      return `<button type="button" class="english-item" data-index="${position}" aria-current="${
        position === active.index
      }"${exam ? " disabled" : ""}><span>${esc(label)}</span><small>${esc(note)}</small></button>`;
    })
    .join("");
}

function renderContext(entry: SessionItem, source: DeckItem | Variant): void {
  const passage = entry.runtime.passage;
  const stem = itemStem(source);
  if (passage) {
    dom.practiceContext.className = "english-context english-markdown";
    dom.practiceContext.innerHTML = renderMarkdown(passage);
    dom.practiceContext.style.display = "block";
    return;
  }
  dom.practiceContext.className = "english-context";
  if (stem) {
    dom.practiceContext.textContent = stem;
    dom.practiceContext.style.display = "block";
  } else {
    dom.practiceContext.style.display = "none";
  }
}

function renderCard(): void {
  const entry = current();
  if (!session || !entry) {
    return;
  }
  session.answered = false;
  session.inVariant = false;
  session.variantDone = false;
  dom.practiceCrumb.textContent = `${entry.runtime.stage.title} · ${entry.runtime.track.title} · ${
    errorTagOf(entry.item, entry.runtime.deck.kind)
  }`;
  renderSide();
  if (entry.runtime.deck.kind === "writing") {
    renderWriting(entry);
  } else {
    renderChoices(entry, entry.item, false);
  }
}

function sensesHtml(item: DeckItem): string {
  if (!item.senses || item.senses.length === 0) {
    return "";
  }
  return `<ul class="english-senses">${item.senses
    .map((sense) => `<li>${esc(sense.pos)} ${esc(sense.gloss)}</li>`)
    .join("")}</ul>`;
}

function renderChoices(entry: SessionItem, source: DeckItem | Variant, inVariant: boolean): void {
  if (!session) {
    return;
  }
  session.answered = false;
  session.inVariant = inVariant;
  renderContext(entry, source);

  const word = entry.item.word && !inVariant ? `${entry.item.word} — ` : "";
  const kind = inVariant ? "变式" : itemKindLabel(entry.item.kind);
  dom.question.innerHTML = `<p class="english-prompt">${esc(word)}${esc(source.prompt)}${
    kind ? `<span class="english-track-state"> · ${esc(kind)}</span>` : ""
  }</p>
    <div class="english-choices">${(source.choices ?? [])
      .map((choice, index) => `<button type="button" class="english-choice" data-choice="${index}">${esc(choice.label)}</button>`)
      .join("")}</div>
    <div class="english-feedback" id="feedback"></div>`;

  dom.question.querySelectorAll<HTMLButtonElement>("[data-choice]").forEach((button) => {
    button.addEventListener("click", () => {
      void answerChoice(entry, source, Number(button.dataset.choice), inVariant);
    });
  });
}

async function answerChoice(
  entry: SessionItem,
  source: DeckItem | Variant,
  position: number,
  inVariant: boolean,
): Promise<void> {
  if (!session || session.answered) {
    return;
  }
  session.answered = true;

  const choices = source.choices ?? [];
  const picked = choices[position];
  const answer = choices.find((choice) => choice.ok);
  if (!picked || !answer) {
    return;
  }
  const correct = picked.ok;
  const buttons = Array.from(dom.question.querySelectorAll<HTMLButtonElement>("[data-choice]"));

  session.attempts.push({
    item: entry.item,
    runtime: entry.runtime,
    correct,
    picked: picked.label,
    answer: answer.label,
    why: answer.why ?? "",
  });

  await recordAnswer(entry, {
    correct,
    selected: picked.label,
    answer: answer.label,
    explanation: answer.why ?? "",
    isVariant: inVariant,
  });

  if (session.mode === "exam") {
    buttons.forEach((button) => {
      button.disabled = true;
    });
    await goNext();
    return;
  }

  buttons.forEach((button, index) => {
    button.disabled = true;
    if (choices[index]?.ok) {
      button.dataset.result = "ok";
    } else if (index === position) {
      button.dataset.result = "bad";
    }
  });

  const feedback = document.getElementById("feedback");
  if (feedback) {
    feedback.innerHTML = correct
      ? `<div class="english-feedback-head"><strong>判断正确</strong><span>不进入错题本</span></div>
         <p>${esc(picked.why ?? answer.why ?? "")}</p>${inVariant ? "" : sensesHtml(entry.item)}${otherWhyHtml(choices, position)}`
      : `<div class="english-feedback-head"><strong data-wrong="true">已自动加入错题本</strong><span>错因：${esc(
          errorTagOf(entry.item, entry.runtime.deck.kind),
        )}</span></div>
         <p>${esc(answer.why ?? "")}</p>
         ${picked.why ? `<p>你选的：${esc(picked.why)}</p>` : ""}
         ${inVariant ? "" : sensesHtml(entry.item)}${otherWhyHtml(choices, position)}`;
    feedback.classList.add("is-visible");
    if (inVariant) {
      session.variantDone = true;
    }
    appendNextAction(entry, correct, feedback);
  }
}

/** 干扰项的解析一并摊开：知道“不是哪个意思”才算认识这个词。 */
function otherWhyHtml(choices: Choice[], picked: number): string {
  const rows = choices
    .map((choice, index) =>
      choice.ok || index === picked || !choice.why ? "" : `<li>${esc(choice.label)}——${esc(choice.why)}</li>`,
    )
    .filter(Boolean)
    .join("");
  return rows ? `<ul class="english-why-list">${rows}</ul>` : "";
}

function appendNextAction(entry: SessionItem, correct: boolean, feedback: HTMLElement): void {
  if (!session) {
    return;
  }
  const hasVariant = (entry.item.variants?.length ?? 0) > 0;
  const needVariant = hasVariant && !session.variantDone;
  const last = session.index >= session.items.length - 1;
  const buttons = [
    needVariant ? `<button type="button" class="english-feedback-action" data-act="variant">换一句再问一次</button>` : "",
    `<button type="button" class="english-feedback-action" data-act="next"${
      needVariant ? "" : " data-primary"
    }>${last ? "练完，回路线" : "下一题"}</button>`,
  ]
    .filter(Boolean)
    .join(" ");
  feedback.insertAdjacentHTML("beforeend", `<div class="english-mistake-actions">${buttons}</div>`);
  void correct;

  feedback.querySelector<HTMLButtonElement>('[data-act="variant"]')?.addEventListener("click", () => {
    const variant = entry.item.variants?.[0];
    if (variant) {
      renderChoices(entry, variant, true);
    }
  });
  feedback.querySelector<HTMLButtonElement>('[data-act="next"]')?.addEventListener("click", () => {
    void goNext();
  });
}

function renderWriting(entry: SessionItem): void {
  if (!session) {
    return;
  }
  const item = entry.item;
  renderContext(entry, item);
  const demand = [
    item.min_words ? `不少于 ${item.min_words} 词` : "",
    (item.required_any ?? []).length > 0 ? `至少用上 ${(item.required_any ?? []).join(" / ")}` : "",
  ]
    .filter(Boolean)
    .join("，");

  dom.question.innerHTML = `<p class="english-prompt">${esc(item.prompt)}</p>
    ${demand ? `<p class="english-track-desc">${esc(demand)}</p>` : ""}
    ${
      (item.checklist ?? []).length > 0
        ? `<ul class="english-why-list">${(item.checklist ?? []).map((line) => `<li>${esc(line)}</li>`).join("")}</ul>`
        : ""
    }
    <textarea class="english-write-box" aria-label="写作练习输入" placeholder="在这里完成这一小段……"></textarea>
    <button type="button" class="english-write-action" data-primary data-act="submit">${
      session.mode === "exam" ? "交卷" : "提交本段"
    }</button>
    <div class="english-feedback" id="feedback"></div>`;

  const box = dom.question.querySelector<HTMLTextAreaElement>(".english-write-box");
  if (box && item.starter) {
    box.value = `${item.starter} `;
  }
  box?.focus();
  dom.question.querySelector<HTMLButtonElement>('[data-act="submit"]')?.addEventListener("click", () => {
    void submitWriting(entry);
  });
}

async function submitWriting(entry: SessionItem): Promise<void> {
  if (!session || session.answered) {
    return;
  }
  const box = dom.question.querySelector<HTMLTextAreaElement>(".english-write-box");
  const text = box?.value.trim() ?? "";
  if (text.length === 0) {
    return;
  }
  session.answered = true;

  const item = entry.item;
  const grade = gradeWriting(item, text);
  const verdict = writingVerdict(grade);

  session.attempts.push({
    item,
    runtime: entry.runtime,
    correct: grade.correct,
    picked: text.slice(0, 200),
    answer: item.reference ?? "",
    why: verdict,
  });

  await recordAnswer(entry, {
    correct: grade.correct,
    selected: text.slice(0, 500),
    answer: item.reference ?? "",
    explanation: verdict,
    isVariant: false,
  });

  if (session.mode === "exam") {
    await goNext();
    return;
  }

  dom.question.querySelector('[data-act="submit"]')?.remove();
  const feedback = document.getElementById("feedback");
  if (feedback) {
    feedback.innerHTML = `<div class="english-feedback-head"><strong${
      grade.correct ? "" : ' data-wrong="true"'
    }>${grade.correct ? "达标" : "还没达标"}</strong><span>${esc(verdict)}</span></div>
      <p>下面是参考写法，用它对照上面的自查项，别逐字抄。</p>
      <blockquote class="english-context">${esc(item.reference ?? "")}</blockquote>`;
    feedback.classList.add("is-visible");
    appendNextAction(entry, grade.correct, feedback);
  }
}

interface AnswerRecord {
  correct: boolean;
  selected: string;
  answer: string;
  explanation: string;
  isVariant: boolean;
}

async function recordAnswer(entry: SessionItem, record: AnswerRecord): Promise<void> {
  const { runtime, item } = entry;
  try {
    const state = await saveAnswer({
      item_id: item.id,
      topic_id: runtime.track.id,
      kind: runtime.deck.kind,
      correct: record.correct,
      deck_total: runtime.deck.items.length,
      selected_answer: record.selected,
      correct_answer: record.answer,
      explanation: record.explanation,
      error_tag: errorTagOf(item, runtime.deck.kind),
      is_variant: record.isVariant,
    });
    review.set(state.item_id, state);
  } catch (error) {
    dom.question.insertAdjacentHTML(
      "beforeend",
      `<p class="english-empty">这次结果没能写进进度库：${esc(String(error))}</p>`,
    );
  }
}

async function goNext(): Promise<void> {
  if (!session) {
    return;
  }
  if (session.index >= session.items.length - 1) {
    if (session.mode === "exam") {
      await refreshProgress();
      renderReport();
      return;
    }
    await backToOverview();
    return;
  }
  session.index += 1;
  renderCard();
}

function renderReport(): void {
  const active = session;
  if (!active) {
    return;
  }
  const right = active.attempts.filter((attempt) => attempt.correct).length;
  const score = active.attempts.length === 0 ? 0 : Math.round((right / active.attempts.length) * 100);
  const pass = score >= 80;

  active.index = active.items.length;
  renderSide();
  renderTopBar();
  dom.practiceTitle.textContent = "已交卷";
  dom.practiceGoal.textContent = "逐题对照解析；答错的已经进了错题本。";
  dom.practiceContext.style.display = "none";
  dom.question.innerHTML = `<div class="english-feedback-head">
      <span class="english-score" data-pass="${pass}">${score} 分</span>
      <span>答对 ${right} / ${active.attempts.length}${pass ? "" : " · 80 分及格"}</span>
    </div>
    ${active.attempts
      .map(
        (attempt) => `<div class="english-report-row">
          <span class="english-${attempt.correct ? "ok" : "bad"}">${attempt.correct ? "✓" : "✗"}</span>
          <span>
            <strong>${esc(attempt.item.word ?? itemStem(attempt.item) ?? attempt.item.prompt)}</strong>
            <small>你的答案：${esc(attempt.picked)}</small>
            ${attempt.correct ? "" : `<small>正解：${esc(attempt.answer)}</small>`}
            <small>${esc(attempt.why)}</small>
          </span>
        </div>`,
      )
      .join("")}
    <div class="english-mistake-actions"><button type="button" data-primary data-act="done">回路线</button></div>`;
  dom.question.querySelector<HTMLButtonElement>('[data-act="done"]')?.addEventListener("click", () => {
    void backToOverview();
  });
}

function showRubric(runtime: TrackRuntime): void {
  session = null;
  setView("practice");
  dom.backStage.textContent = "← 返回路线";
  dom.practiceListTitle.textContent = `${runtime.track.title}评分维度`;
  dom.practiceCount.textContent = `共 ${runtime.deck.items.length} 题`;
  dom.itemList.innerHTML = "";
  dom.practiceCrumb.textContent = `${runtime.stage.title} · ${runtime.track.title}`;
  dom.practiceTitle.textContent = "机器判什么，你自己判什么";
  dom.practiceGoal.textContent =
    "字数和要求用上的连接方式由机器判定，进掌握度；组织、用词和语气由你对照自查项和参考写法自己看。";
  dom.practiceContext.style.display = "none";
  dom.question.innerHTML =
    runtime.deck.items
      .map((item) => {
        const demand = [
          item.min_words ? `不少于 ${item.min_words} 词` : "",
          (item.required_any ?? []).length > 0 ? `用上 ${(item.required_any ?? []).join(" / ")}` : "",
        ]
          .filter(Boolean)
          .join("，");
        return `<div class="english-report-row">
            <span class="english-ok">·</span>
            <span>
              <strong>${esc(item.prompt)}</strong>
              ${demand ? `<small>机器判定：${esc(demand)}</small>` : ""}
              ${(item.checklist ?? []).map((line) => `<small>自查：${esc(line)}</small>`).join("")}
            </span>
          </div>`;
      })
      .join("") +
    `<div class="english-mistake-actions"><button type="button" data-primary data-act="done">回路线</button></div>`;
  dom.question.querySelector<HTMLButtonElement>('[data-act="done"]')?.addEventListener("click", () => {
    void backToOverview();
  });
}

/* ------------------------------------------------------------- 错题本 */

function showMistakes(): void {
  session = null;
  setView("mistakes");
  dom.backStage.textContent = "← 返回路线";
  dom.mistakeCount.textContent = `${mistakes.length} 题待纠正 · 按错因归组`;
  if (mistakes.length === 0) {
    dom.mistakeList.innerHTML = "";
    dom.mistakeDetail.innerHTML = `<p class="english-empty">错题本是空的。</p>`;
    return;
  }
  if (!mistakes.some((mistake) => mistake.item_id === currentMistakeId)) {
    currentMistakeId = mistakes[0]!.item_id;
  }
  dom.mistakeList.innerHTML = mistakes
    .map((mistake) => {
      const runtime = runtimes.get(mistake.topic_id);
      return `<button type="button" class="english-item" data-mistake="${esc(mistake.item_id)}" aria-current="${
        mistake.item_id === currentMistakeId
      }"><span>${esc(mistake.error_tag)}</span><small>${esc(runtime?.track.title ?? "")} · ${
        mistake.wrong_count
      } 次</small></button>`;
    })
    .join("");
  renderMistakeDetail();
}

function renderMistakeDetail(): void {
  const mistake = mistakes.find((item) => item.item_id === currentMistakeId);
  if (!mistake) {
    return;
  }
  const runtime = runtimes.get(mistake.topic_id);
  const item = runtime?.deck.items.find((entry) => entry.id === mistake.item_id);
  const stem = item ? itemStem(item) : undefined;
  const hasVariant = (item?.variants?.length ?? 0) > 0;

  dom.mistakeDetail.innerHTML = `<p class="english-crumb">${esc(runtime?.stage.title ?? "")} · ${esc(
    runtime?.track.title ?? "",
  )} · 错因：${esc(mistake.error_tag)}</p>
    <h2>不是重做原题，而是纠正判断</h2>
    <p class="english-practice-goal">保留原题、错误答案和解析，再用同一知识点的变式确认是否真正会了。</p>
    ${stem ? `<blockquote class="english-context">${esc(stem)}</blockquote>` : ""}
    <div class="english-answer-compare">
      <div class="english-answer-box" data-kind="wrong"><strong>当时的错误判断</strong><span>${esc(
        mistake.selected_answer,
      )}</span></div>
      <div class="english-answer-box" data-kind="right"><strong>正确判断</strong><span>${esc(
        mistake.correct_answer,
      )}</span></div>
    </div>
    <div class="english-mistake-rule"><strong>移出规则：</strong>不同日期连续答对原知识点和一道未见变式后自动移出；再次答错则重新累计。当前已连对 ${
      mistake.correct_days
    } 天，变式${mistake.variant_correct ? "已做对" : "还没做对"}。</div>
    ${mistake.explanation ? `<p class="english-practice-goal">${esc(mistake.explanation)}</p>` : ""}
    <div class="english-mistake-actions">
      <button type="button" data-primary data-act="retry">${hasVariant ? "开始一道变式" : "重做这道题"}</button>
      <button type="button" data-act="open-track">回到${esc(runtime?.track.title ?? "该轨")}练习</button>
    </div>`;

  dom.mistakeDetail.querySelector<HTMLButtonElement>('[data-act="retry"]')?.addEventListener("click", () => {
    if (runtime && item) {
      startPractice(runtime, [item]);
    }
  });
  dom.mistakeDetail.querySelector<HTMLButtonElement>('[data-act="open-track"]')?.addEventListener("click", () => {
    if (runtime) {
      startPractice(runtime, runtime.deck.items, mistake.item_id);
    }
  });
}

/* --------------------------------------------------------------- 装配 */

async function refreshProgress(): Promise<void> {
  const [nextReview, nextMastery, nextMistakes] = await Promise.all([
    loadReview(),
    loadMastery(),
    loadMistakes(),
  ]);
  review = nextReview;
  mastery = nextMastery;
  mistakes = nextMistakes;
}

function bindEvents(): void {
  dom.btnDue.addEventListener("click", startDueSession);
  dom.btnMistakes.addEventListener("click", showMistakes);
  dom.btnContinue.addEventListener("click", () => nextTask()?.run());
  dom.backStage.addEventListener("click", () => {
    void backToOverview();
  });

  dom.stageList.addEventListener("click", (event) => {
    const stageId = (event.target as HTMLElement).closest<HTMLElement>("[data-stage]")?.dataset.stage;
    if (stageId) {
      currentStageId = stageId;
      renderStageList();
      renderStageDetail();
    }
  });

  dom.tracks.addEventListener("click", (event) => {
    const target = event.target as HTMLElement;
    const weak = target.closest<HTMLElement>("[data-weak]")?.dataset.weak;
    if (weak) {
      const runtime = runtimes.get(weak);
      if (runtime) {
        const items = weakItems(runtime.deck.items, review, now());
        startPractice(runtime, items.length > 0 ? items : runtime.deck.items);
      }
      return;
    }
    const exam = target.closest<HTMLElement>("[data-exam]")?.dataset.exam;
    if (exam) {
      const runtime = runtimes.get(exam);
      if (runtime) {
        startExam(runtime);
      }
      return;
    }
    const rubric = target.closest<HTMLElement>("[data-rubric]")?.dataset.rubric;
    if (rubric) {
      const runtime = runtimes.get(rubric);
      if (runtime) {
        showRubric(runtime);
      }
    }
  });

  dom.itemList.addEventListener("click", (event) => {
    const index = (event.target as HTMLElement).closest<HTMLElement>("[data-index]")?.dataset.index;
    if (!session || session.mode === "exam" || index === undefined) {
      return;
    }
    const position = Number(index);
    if (Number.isInteger(position) && position >= 0 && position < session.items.length) {
      session.index = position;
      renderCard();
    }
  });

  dom.mistakeList.addEventListener("click", (event) => {
    const id = (event.target as HTMLElement).closest<HTMLElement>("[data-mistake]")?.dataset.mistake;
    if (id) {
      currentMistakeId = id;
      showMistakes();
    }
  });
}

function fail(error: unknown): void {
  dom.tracks.innerHTML = `<section class="english-track"><h3>没能把课表读起来</h3><p class="english-track-desc">${esc(
    String(error),
  )}</p></section>`;
}

async function boot(): Promise<void> {
  const [info, loaded] = await Promise.all([loadAppInfo(), loadCurriculum()]);
  curriculum = loaded;
  dom.title.textContent = curriculum.title;
  dom.subtitle.textContent = `${curriculum.stages.map((stage) => stage.title).join(" → ")} · ${curriculum.tagline}`;
  dom.endpoint.innerHTML = `<strong>终点</strong><br>${esc(curriculum.endpoint ?? curriculum.description)}`;
  void info;

  await Promise.all(
    curriculum.stages.flatMap((stage) =>
      stage.tracks.map(async (track: Track) => {
        const [deck, passage] = await Promise.all([
          loadDeck(track.deck),
          track.passage ? loadText(track.passage) : Promise.resolve(undefined),
        ]);
        runtimes.set(track.id, { stage, track, deck, passage });
      }),
    ),
  );

  await refreshProgress();
  currentStageId = activeStage().id;
  bindEvents();
  showOverview();
}

boot().catch(fail);
