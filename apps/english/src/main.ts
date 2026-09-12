// 前端入口：三个视图——能力路线（走到哪一级、这一级三条轨什么状态）、
// 练习台（练习即时给解析，考核成套作答后统一反馈）、错题本。
// 内容和进度由 backend 提供，判定与组卷在 practice，这里只渲染和接事件。

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
  trackKindLabel,
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

const dom = {
  title: byId("app-title"),
  trail: byId("app-trail"),
  btnDue: byId<HTMLButtonElement>("btn-due"),
  btnMistakes: byId<HTMLButtonElement>("btn-mistakes"),
  btnContinue: byId<HTMLButtonElement>("btn-continue"),

  viewRoute: byId("view-route"),
  viewDrill: byId("view-drill"),
  viewMistakes: byId("view-mistakes"),

  stageList: byId("stage-list"),
  endpoint: byId("endpoint-text"),
  stageTitle: byId("stage-title"),
  stageGoal: byId("stage-goal"),
  stageBadge: byId("stage-badge"),
  examStrip: byId("exam-strip"),
  trackCards: byId("track-cards"),
  unlockNote: byId("unlock-note"),

  drillTitle: byId("drill-title"),
  drillProgress: byId("drill-progress"),
  rail: byId("drill-rail"),
  passage: byId("passage-box"),
  card: byId("card-box"),
  report: byId("exam-report"),

  mistakeList: byId("mistake-list"),
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
  title: string;
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
let session: Session | null = null;

function esc(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function nowSeconds(): number {
  return Math.floor(Date.now() / 1000);
}

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

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
  return trackStats(
    runtime.deck.items,
    review,
    mistakes,
    runtime.track.id,
    trackPassed(runtime.track),
    nowSeconds(),
  );
}

/** 当前该做的那一级：第一个还没三项全过的，全过了就停在最后一级。 */
function activeStage(): Stage {
  const stages = curriculum.stages;
  return stages.find((stage) => !stagePassed(stage)) ?? stages[stages.length - 1]!;
}

/* --------------------------------------------------------- 顶栏 */

function dueTotal(): number {
  const now = nowSeconds();
  let count = 0;
  for (const state of review.values()) {
    if (isDue(state, now)) {
      count += 1;
    }
  }
  return count;
}

function renderTopBar(): void {
  const due = dueTotal();
  dom.btnDue.innerHTML = `今日复习 <b>${due}</b>`;
  dom.btnDue.disabled = due === 0;
  dom.btnMistakes.innerHTML = `错题本 <b>${mistakes.length}</b>`;
  dom.btnMistakes.disabled = mistakes.length === 0;

  const next = nextTask();
  dom.btnContinue.textContent = next ? next.label : "三级都已通过";
  dom.btnContinue.disabled = next === null;
}

interface NextTask {
  label: string;
  run: () => void;
}

/** 到期复习优先，其次当前等级第一条没过的轨。 */
function nextTask(): NextTask | null {
  if (dueTotal() > 0) {
    return { label: "继续当前任务", run: startDueSession };
  }
  const stage = activeStage();
  for (const track of stage.tracks) {
    const runtime = runtimes.get(track.id);
    if (runtime && !trackPassed(track)) {
      return {
        label: `继续${stage.title} · ${track.title}`,
        run: () => startPractice(runtime, runtime.deck.items),
      };
    }
  }
  return null;
}

/* ----------------------------------------------------- 能力路线 */

function renderStageList(): void {
  dom.stageList.innerHTML = curriculum.stages
    .map((stage, index) => {
      const passed = stagePassed(stage);
      const unlocked = stageUnlocked(stage);
      const done = stage.tracks.filter(trackPassed).length;
      const note = passed
        ? "单词 · 例句 · 作文已过"
        : unlocked
          ? `三项已过 ${done} 项`
          : `三项达到${requiredTitles(stage)}后解锁`;
      const mark = passed ? "✓" : String(index + 1);
      return `<li>
          <button type="button" class="stage-btn${stage.id === currentStageId ? " is-current" : ""}" data-stage="${esc(stage.id)}">
            <span class="stage-mark${passed ? " is-done" : ""}">${mark}</span>
            <span><strong>${esc(stage.title)} · ${esc(stage.subtitle)}</strong><small>${esc(note)}</small></span>
          </button>
        </li>`;
    })
    .join("");
}

function requiredTitles(stage: Stage): string {
  return stage.requires
    .map((id) => curriculum.stages.find((other) => other.id === id)?.title ?? id)
    .join("、");
}

function examLabel(track: Track): string {
  return `${track.title}考核`;
}

function renderExamStrip(stage: Stage): void {
  dom.examStrip.innerHTML = stage.tracks
    .map((track) => {
      const runtime = runtimes.get(track.id);
      if (!runtime) {
        return "";
      }
      const stats = statsOf(runtime);
      const passed = stats.passed;
      const detail = passed
        ? `已通过 · 正确率 ${stats.accuracy === null ? "—" : percent(stats.accuracy)}`
        : stats.done === 0
          ? "待完成 · 还没开始"
          : `待完成 · 已练 ${stats.done}/${stats.total}`;
      return `<div class="exam-cell">
          <span class="exam-icon ${passed ? "is-pass" : "is-todo"}">${passed ? "✓" : "!"}</span>
          <span><strong>${esc(examLabel(track))}</strong><span>${esc(detail)}</span></span>
        </div>`;
    })
    .join("");
}

function trackTag(stats: ReturnType<typeof statsOf>): string {
  if (stats.passed) {
    return "考核已通过";
  }
  if (stats.done === 0) {
    return "尚未开始";
  }
  return stats.fresh === 0 ? "已具备考核条件" : "正在学习";
}

function renderTrackCards(stage: Stage): void {
  dom.trackCards.innerHTML = stage.tracks
    .map((track) => {
      const runtime = runtimes.get(track.id);
      if (!runtime) {
        return "";
      }
      const stats = statsOf(runtime);
      const weak = stats.weakTag ? `薄弱：${stats.weakTag}` : "暂无薄弱项";
      const left =
        track.kind === "writing"
          ? "继续引导写作"
          : track.kind === "vocab"
            ? "复习薄弱词"
            : `再练 ${Math.max(1, Math.min(5, stats.total))} 句`;
      const right =
        track.kind === "writing"
          ? `<button type="button" class="chip" data-rubric="${esc(track.id)}">查看评分维度</button>`
          : `<button type="button" class="chip is-primary" data-exam="${esc(track.id)}">开始考核</button>`;
      return `<article class="track-card kind-${esc(track.kind)}">
          <div class="track-top">
            <h3>${esc(track.title)}</h3>
            <span class="track-tag">${esc(trackTag(stats))}</span>
          </div>
          <p>${esc(track.goal)}</p>
          <div class="bar"><span style="width:${percent(stats.coverage)}"></span></div>
          <div class="track-stats">
            <span>练习覆盖 ${percent(stats.coverage)}${
              stats.accuracy === null ? "" : ` · 正确率 ${percent(stats.accuracy)}`
            }</span>
            <span>${esc(stats.due > 0 ? `到期复习 ${stats.due}` : weak)}</span>
          </div>
          <div class="track-acts">
            <button type="button" class="chip" data-weak="${esc(track.id)}">${esc(left)}</button>
            ${right}
          </div>
        </article>`;
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
  dom.stageBadge.textContent = passed ? "已通过" : unlocked ? "当前等级" : "未解锁";
  dom.stageBadge.className = `badge ${passed ? "is-done" : unlocked ? "is-current" : "is-locked"}`;

  renderExamStrip(stage);
  renderTrackCards(stage);

  dom.unlockNote.textContent = unlocked
    ? passed
      ? "这一级三项都已通过，可以推进下一级。"
      : "三项分别达标后，下一级自动解锁。"
    : `完成${requiredTitles(stage)}的单词、例句与作文后，这一级自动解锁。`;
}

function renderRoute(): void {
  renderTopBar();
  renderStageList();
  renderStageDetail();
}

function showRoute(): void {
  session = null;
  dom.viewDrill.classList.add("is-hidden");
  dom.viewMistakes.classList.add("is-hidden");
  dom.viewRoute.classList.remove("is-hidden");
  renderRoute();
}

async function backToRoute(): Promise<void> {
  await refreshProgress();
  showRoute();
}

/* ------------------------------------------------------- 错题本 */

function showMistakes(): void {
  dom.viewRoute.classList.add("is-hidden");
  dom.viewDrill.classList.add("is-hidden");
  dom.viewMistakes.classList.remove("is-hidden");

  if (mistakes.length === 0) {
    dom.mistakeList.innerHTML = `<p class="empty">错题本是空的。</p>`;
    return;
  }
  dom.mistakeList.innerHTML = mistakes
    .map((mistake) => {
      const runtime = runtimes.get(mistake.topic_id);
      const where = runtime ? `${runtime.stage.title} · ${runtime.track.title}` : mistake.topic_id;
      const need = mistake.variant_correct ? "变式已做对" : "还要做对一次变式";
      return `<button type="button" class="mistake" data-mistake="${esc(mistake.item_id)}" data-topic="${esc(mistake.topic_id)}">
          <strong>${esc(mistake.error_tag)}</strong>
          <p>${esc(where)} · 错 ${mistake.wrong_count} 次 · 已连对 ${mistake.correct_days} 天 · ${esc(need)}</p>
          <p>正解：${esc(mistake.correct_answer)}</p>
        </button>`;
    })
    .join("");
}

/* ------------------------------------------------------- 练习台 */

function openSession(next: Session, passage?: string): void {
  if (next.items.length === 0) {
    return;
  }
  session = next;
  dom.viewRoute.classList.add("is-hidden");
  dom.viewMistakes.classList.add("is-hidden");
  dom.viewDrill.classList.remove("is-hidden");
  dom.report.classList.add("is-hidden");
  dom.report.innerHTML = "";
  dom.card.classList.remove("is-hidden");

  if (passage) {
    dom.passage.innerHTML = renderMarkdown(passage);
    dom.passage.classList.remove("is-hidden");
  } else {
    dom.passage.classList.add("is-hidden");
    dom.passage.innerHTML = "";
  }
  renderCard();
}

function startPractice(runtime: TrackRuntime, items: DeckItem[], focusId?: string): void {
  const ordered = orderItems(items, review, nowSeconds());
  const index = focusId ? ordered.findIndex((item) => item.id === focusId) : 0;
  openSession(
    {
      title: `${runtime.stage.title} · ${runtime.track.title}`,
      mode: "practice",
      items: ordered.map((item) => ({ item, runtime })),
      index: index >= 0 ? index : 0,
      answered: false,
      inVariant: false,
      variantDone: false,
      attempts: [],
    },
    runtime.passage,
  );
}

function startExam(runtime: TrackRuntime): void {
  const items = examItems(runtime.deck, review, nowSeconds());
  openSession(
    {
      title: `${examLabel(runtime.track)} · ${runtime.stage.title}`,
      mode: "exam",
      items: items.map((item) => ({ item, runtime })),
      index: 0,
      answered: false,
      inVariant: false,
      variantDone: false,
      attempts: [],
    },
    runtime.passage,
  );
}

/** 到期复习跨轨：今天该回头看的题排在一起，不用先挑进哪条轨。 */
function startDueSession(): void {
  const now = nowSeconds();
  const items: SessionItem[] = [];
  for (const runtime of runtimes.values()) {
    for (const item of orderItems(runtime.deck.items, review, now)) {
      const state = review.get(item.id);
      if (state && isDue(state, now)) {
        items.push({ item, runtime });
      }
    }
  }
  openSession({
    title: "今日复习",
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
  if (!session) {
    return null;
  }
  return session.items[session.index] ?? null;
}

function renderHead(): void {
  if (!session) {
    return;
  }
  dom.drillTitle.textContent = session.title;
  dom.drillProgress.textContent =
    session.mode === "exam"
      ? `考核中 · 第 ${session.index + 1} / ${session.items.length} 题 · 交卷后统一反馈`
      : `第 ${session.index + 1} / ${session.items.length} 题`;
}

/** 这一轮要做的条目、各自的到期状态和当前位置；考核成套作答，不让跳题。 */
function itemStatus(item: DeckItem, now: number): string {
  const state = review.get(item.id);
  if (!state) {
    return "还没做";
  }
  if (state.last_rating !== null && state.last_rating < 3) {
    return "上次答错";
  }
  return isDue(state, now) ? "到期重练" : `已过 ${state.reps} 轮`;
}

function renderRail(): void {
  const active = session;
  if (!active) {
    return;
  }
  const exam = active.mode === "exam";
  const now = nowSeconds();
  const rows = active.items
    .map((entry, position) => {
      const label = exam ? `第 ${position + 1} 题` : itemSummary(entry.item);
      const note = exam
        ? position < active.index
          ? "已作答"
          : position === active.index
            ? "作答中"
            : "未作答"
        : itemStatus(entry.item, now);
      return `<li${position === active.index ? ' class="is-active"' : ""}>
          <button type="button" data-index="${position}"${exam ? " disabled" : ""}>${esc(label)}<small>${esc(note)}</small></button>
        </li>`;
    })
    .join("");
  const head = exam ? "考核条目" : (active.items[0]?.runtime.track.title ?? "本轮条目");
  dom.rail.innerHTML = `<p class="pane-title">${esc(head)}</p><ul class="item-index">${rows}</ul>`;
}

function renderCard(): void {
  const entry = current();
  if (!session || !entry) {
    return;
  }
  session.answered = false;
  session.inVariant = false;
  session.variantDone = false;
  renderHead();
  renderRail();
  if (entry.runtime.deck.kind === "writing") {
    renderWritingCard(entry);
  } else {
    renderChoiceCard(entry, entry.item, false);
  }
}

function kickerOf(entry: SessionItem, suffix?: string): string {
  const kind = entry.runtime.deck.kind;
  return [trackKindLabel(kind), errorTagOf(entry.item, kind), suffix].filter(Boolean).join(" · ");
}

function sensesHtml(item: DeckItem): string {
  if (!item.senses || item.senses.length === 0) {
    return "";
  }
  const rows = item.senses.map((sense) => `<li><em>${esc(sense.pos)}</em> ${esc(sense.gloss)}</li>`).join("");
  return `<ul class="check-list">${rows}</ul>`;
}

function renderChoiceCard(entry: SessionItem, source: DeckItem | Variant, inVariant: boolean): void {
  if (!session) {
    return;
  }
  session.answered = false;
  session.inVariant = inVariant;

  const item = entry.item;
  const stem = itemStem(source);
  const word = item.word && !inVariant ? `<p class="word">${esc(item.word)}</p>` : "";
  const suffix = inVariant ? "变式" : itemKindLabel(item.kind) || undefined;
  const choices = (source.choices ?? [])
    .map((choice, position) => `<button type="button" class="choice" data-choice="${position}">${esc(choice.label)}</button>`)
    .join("");

  dom.card.innerHTML = `<p class="card-kicker">${esc(kickerOf(entry, suffix))}</p>
    ${word}
    ${stem ? `<p class="stem">${esc(stem)}</p>` : ""}
    <p class="prompt">${esc(source.prompt)}</p>
    <div class="choices">${choices}</div>`;

  const buttons = Array.from(dom.card.querySelectorAll<HTMLButtonElement>("button.choice"));
  buttons.forEach((button, position) => {
    button.addEventListener("click", () => {
      void answerChoice(entry, source, position, inVariant, buttons);
    });
  });
}

async function answerChoice(
  entry: SessionItem,
  source: DeckItem | Variant,
  position: number,
  inVariant: boolean,
  buttons: HTMLButtonElement[],
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
    buttons[position]?.classList.add("is-picked");
    await goNext();
    return;
  }

  buttons.forEach((button, index) => {
    button.disabled = true;
    const choice = choices[index];
    if (!choice) {
      return;
    }
    if (choice.ok) {
      button.classList.add("is-ok");
    } else if (index === position) {
      button.classList.add("is-bad");
    }
  });

  dom.card.insertAdjacentHTML(
    "beforeend",
    `<div class="explain">
      <p><strong>${correct ? "对了。" : "错了。"}</strong>${esc((correct ? picked.why : answer.why) ?? "")}</p>
      ${!correct && picked.why ? `<p class="muted">你选的：${esc(picked.why)}</p>` : ""}
      ${inVariant ? "" : sensesHtml(entry.item)}
      ${otherWhyHtml(choices, position)}
    </div>`,
  );

  if (inVariant) {
    session.variantDone = true;
  }
  renderRateRow(entry, correct);
}

/** 干扰项的解析一并摊开：知道“不是哪个意思”才算认识这个词。 */
function otherWhyHtml(choices: Choice[], picked: number): string {
  const rows = choices
    .map((choice, index) =>
      choice.ok || index === picked || !choice.why ? "" : `<li>${esc(choice.label)}——${esc(choice.why)}</li>`,
    )
    .filter(Boolean)
    .join("");
  return rows ? `<ul class="check-list">${rows}</ul>` : "";
}

function renderRateRow(entry: SessionItem, correct: boolean): void {
  if (!session) {
    return;
  }
  const hasVariant = (entry.item.variants?.length ?? 0) > 0;
  const needVariant = hasVariant && !session.variantDone;
  const last = session.index >= session.items.length - 1;

  const buttons: string[] = [];
  if (needVariant) {
    buttons.push(`<button type="button" class="chip" data-act="variant">换一句再问一次</button>`);
  }
  buttons.push(
    `<button type="button" class="chip is-primary" data-act="next">${last ? "练完，回路线" : "下一题"}</button>`,
  );
  const note =
    !correct && needVariant ? `<span class="muted">这题记进错题本了：做对变式才算清账。</span>` : "";

  dom.card.insertAdjacentHTML("beforeend", `<div class="rate-row">${buttons.join("")}${note}</div>`);

  dom.card.querySelector<HTMLButtonElement>('[data-act="variant"]')?.addEventListener("click", () => {
    const variant = entry.item.variants?.[0];
    if (variant) {
      renderChoiceCard(entry, variant, true);
    }
  });
  dom.card.querySelector<HTMLButtonElement>('[data-act="next"]')?.addEventListener("click", () => {
    void goNext();
  });
}

function renderWritingCard(entry: SessionItem): void {
  if (!session) {
    return;
  }
  const item = entry.item;
  const checklist = (item.checklist ?? []).map((line) => `<li>${esc(line)}</li>`).join("");
  const required = item.required_any ?? [];
  const demand = [
    item.min_words ? `不少于 ${item.min_words} 词` : "",
    required.length > 0 ? `至少用上 ${required.join(" / ")}` : "",
  ]
    .filter(Boolean)
    .join("，");

  dom.card.innerHTML = `<p class="card-kicker">${esc(kickerOf(entry))}</p>
    <p class="prompt">${esc(item.prompt)}</p>
    ${demand ? `<p class="muted">${esc(demand)}</p>` : ""}
    ${checklist ? `<ul class="check-list">${checklist}</ul>` : ""}
    <textarea class="composer" spellcheck="false"></textarea>
    <div class="rate-row"><button type="button" class="chip is-primary" data-act="submit">${
      session.mode === "exam" ? "交卷" : "写完了，对照参考"
    }</button></div>`;

  const composer = dom.card.querySelector<HTMLTextAreaElement>("textarea.composer");
  if (composer && item.starter) {
    composer.value = `${item.starter} `;
  }
  composer?.focus();
  dom.card.querySelector<HTMLButtonElement>('[data-act="submit"]')?.addEventListener("click", () => {
    void submitWriting(entry);
  });
}

async function submitWriting(entry: SessionItem): Promise<void> {
  if (!session || session.answered) {
    return;
  }
  const composer = dom.card.querySelector<HTMLTextAreaElement>("textarea.composer");
  if (!composer) {
    return;
  }
  const text = composer.value.trim();
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

  dom.card.querySelector(".rate-row")?.remove();
  dom.card.insertAdjacentHTML(
    "beforeend",
    `<div class="explain">
      <p><strong>${grade.correct ? "达标。" : "还没达标。"}</strong>${esc(verdict)}</p>
      <p class="muted">下面是参考写法，用它对照上面的自查项，别逐字抄。</p>
      <p class="reference">${esc(item.reference ?? "")}</p>
    </div>`,
  );
  renderRateRow(entry, grade.correct);
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
    dom.card.insertAdjacentHTML(
      "beforeend",
      `<p class="muted">这次结果没能写进进度库：${esc(String(error))}</p>`,
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
    await backToRoute();
    return;
  }
  session.index += 1;
  renderCard();
}

/** 考核的统一反馈：先给分，再逐题摊开对错和解析。 */
function renderReport(): void {
  if (!session) {
    return;
  }
  const attempts = session.attempts;
  const right = attempts.filter((attempt) => attempt.correct).length;
  const score = attempts.length === 0 ? 0 : Math.round((right / attempts.length) * 100);
  const pass = score >= 80;

  dom.card.innerHTML = "";
  dom.card.classList.add("is-hidden");
  session.index = session.items.length;
  renderRail();
  renderTopBar();
  dom.drillProgress.textContent = "已交卷";
  dom.report.innerHTML = `<h3>${esc(session.title)}</h3>
    <p><span class="score ${pass ? "is-pass" : "is-fail"}">${score} 分</span>
      <span class="muted">答对 ${right} / ${attempts.length}${pass ? "" : " · 80 分及格"}</span></p>
    ${attempts
      .map(
        (attempt) => `<div class="report-row">
          <span class="${attempt.correct ? "ok" : "bad"}">${attempt.correct ? "✓" : "✗"}</span>
          <span>
            <b>${esc(attempt.item.word ?? itemStem(attempt.item) ?? attempt.item.prompt)}</b>
            <span class="muted">你的答案：${esc(attempt.picked)}</span>
            ${attempt.correct ? "" : `<span class="muted">正解：${esc(attempt.answer)}</span>`}
            <span class="muted">${esc(attempt.why)}</span>
          </span>
        </div>`,
      )
      .join("")}
    <div class="rate-row"><button type="button" class="chip is-primary" data-act="done">回路线</button></div>`;
  dom.report.classList.remove("is-hidden");
  dom.report.querySelector<HTMLButtonElement>('[data-act="done"]')?.addEventListener("click", () => {
    void backToRoute();
  });
}

/** 作文不机器判优劣，这里把这一轨的要求和自查项摊开，作为评分维度。 */
function showRubric(runtime: TrackRuntime): void {
  session = null;
  dom.viewRoute.classList.add("is-hidden");
  dom.viewMistakes.classList.add("is-hidden");
  dom.viewDrill.classList.remove("is-hidden");
  dom.passage.classList.add("is-hidden");
  dom.report.classList.add("is-hidden");
  dom.drillTitle.textContent = `${runtime.track.title} · 评分维度`;
  dom.drillProgress.textContent = "机器只判前两项，其余自己对照";

  const rows = runtime.deck.items
    .map((item) => {
      const demands = [
        item.min_words ? `不少于 ${item.min_words} 词` : "",
        (item.required_any ?? []).length > 0 ? `用上 ${(item.required_any ?? []).join(" / ")}` : "",
      ]
        .filter(Boolean)
        .join("，");
      const checks = (item.checklist ?? []).map((line) => `<li>${esc(line)}</li>`).join("");
      return `<div class="explain">
          <p class="prompt">${esc(item.prompt)}</p>
          ${demands ? `<p class="muted">机器判定：${esc(demands)}</p>` : ""}
          ${checks ? `<ul class="check-list">${checks}</ul>` : ""}
        </div>`;
    })
    .join("");

  dom.card.innerHTML = `<p class="card-kicker">${esc(trackKindLabel(runtime.track.kind))} · 评分维度</p>
    <p>字数和要求用上的连接方式由机器判定，进掌握度；组织、用词和语气由你对照自查项和参考写法自己看。</p>
    ${rows}
    <div class="rate-row"><button type="button" class="chip is-primary" data-act="done">回路线</button></div>`;
  dom.card.querySelector<HTMLButtonElement>('[data-act="done"]')?.addEventListener("click", () => {
    void backToRoute();
  });
}

/* --------------------------------------------------------- 装配 */

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
  dom.btnContinue.addEventListener("click", () => {
    nextTask()?.run();
  });

  for (const button of Array.from(document.querySelectorAll<HTMLButtonElement>("[data-back]"))) {
    button.addEventListener("click", () => {
      void backToRoute();
    });
  }

  dom.stageList.addEventListener("click", (event) => {
    const button = (event.target as HTMLElement).closest<HTMLElement>("[data-stage]");
    if (button?.dataset.stage) {
      currentStageId = button.dataset.stage;
      renderStageList();
      renderStageDetail();
    }
  });

  dom.trackCards.addEventListener("click", (event) => {
    const target = event.target as HTMLElement;
    const weak = target.closest<HTMLElement>("[data-weak]")?.dataset.weak;
    if (weak) {
      const runtime = runtimes.get(weak);
      if (runtime) {
        const items = weakItems(runtime.deck.items, review, nowSeconds());
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

  dom.rail.addEventListener("click", (event) => {
    const button = (event.target as HTMLElement).closest<HTMLElement>("[data-index]");
    if (!session || session.mode === "exam" || !button?.dataset.index) {
      return;
    }
    const index = Number(button.dataset.index);
    if (Number.isInteger(index) && index >= 0 && index < session.items.length) {
      session.index = index;
      renderCard();
    }
  });

  dom.mistakeList.addEventListener("click", (event) => {
    const button = (event.target as HTMLElement).closest<HTMLElement>("[data-mistake]");
    const topic = button?.dataset.topic;
    const itemId = button?.dataset.mistake;
    if (!topic || !itemId) {
      return;
    }
    const runtime = runtimes.get(topic);
    if (runtime) {
      startPractice(runtime, runtime.deck.items, itemId);
    }
  });
}

function fail(error: unknown): void {
  dom.viewRoute.classList.remove("is-hidden");
  dom.trackCards.innerHTML = `<article class="track-card"><h3>没能把课表读起来</h3><p>${esc(
    String(error),
  )}</p></article>`;
}

async function boot(): Promise<void> {
  const [info, loaded] = await Promise.all([loadAppInfo(), loadCurriculum()]);
  curriculum = loaded;
  dom.title.textContent = curriculum.title;
  dom.trail.textContent = `${curriculum.stages.map((stage) => stage.title).join(" → ")} · ${curriculum.tagline}`;
  dom.endpoint.textContent = curriculum.endpoint ?? curriculum.description;
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
  showRoute();
}

boot().catch(fail);
