// 前端入口：三个视图切换靠根元素的 data-view（overview / practice / mistakes），
// class 名与 docs/ui-sketch/ 的草图一一对应，样式表原样套用。
// 内容和进度由 backend 提供，排序、判定和组卷在 practice，这里只渲染和接事件。

import "./styles.css";
import { renderMarkdown } from "./markdown";
import {
  loadAppInfo,
  loadAttemptStats,
  loadCurriculum,
  loadDeck,
  loadMastery,
  loadMistakes,
  loadReview,
  loadSourceCatalog,
  loadText,
  saveAnswer,
  saveAssessmentResult,
} from "./backend";
import {
  computeOutcomes,
  errorTagOf,
  gradeWriting,
  isDue,
  itemKindLabel,
  itemStem,
  itemSummary,
  orderItems,
  practiceBatch,
  shuffled,
  trackStats,
  vocabFormProbe,
  weakItems,
  wordFormPattern,
  writingVerdict,
} from "./practice";
import {
  canSpeak,
  getRate,
  getVoiceName,
  listEnglishVoices,
  openExternal,
  previewVoice,
  RATE_OPTIONS,
  setRate,
  setVoiceName,
  speakEnglish,
  stopSpeaking,
  VoiceRecorder,
  voicesReady,
} from "./voice";
import type {
  AttemptStats,
  Choice,
  ContentSource,
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
  voiceRate: byId<HTMLSelectElement>("voice-rate"),
  voiceName: byId<HTMLSelectElement>("voice-name"),
  voiceTry: byId<HTMLButtonElement>("voice-try"),

  stageList: byId("stage-list"),
  endpoint: byId("endpoint"),
  stageTitle: byId("stage-title"),
  stageGoal: byId("stage-goal"),
  stageBadge: byId("stage-badge"),
  outcomes: byId("outcomes"),
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
  assessment: Deck;
  passage?: string;
}

type SessionMode = "practice" | "exam";

interface SessionItem {
  item: DeckItem;
  runtime: TrackRuntime;
  deck: Deck;
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
  inFormRecall: boolean;
  formRecallDone: boolean;
  pendingVocab?: {
    meaningCorrect: boolean;
    picked: string;
    answer: string;
    why: string;
  };
  attempts: Attempt[];
  assessmentId?: string;
}

const runtimes = new Map<string, TrackRuntime>();
const PRACTICE_SESSION_SIZE = 20;
const REVIEW_SESSION_SIZE = 30;
const sourceCatalog = new Map<string, ContentSource>();
const voiceRecorder = new VoiceRecorder();
let curriculum: Curriculum;
let review = new Map<string, ReviewState>();
let mastery = new Map<string, MasteryState>();
let mistakes: Mistake[] = [];
let attemptStats: AttemptStats = { attempts: 0, correct: 0, active_days: 0, streak: 0 };
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

function plainSpeechText(text: string): string {
  return text
    .replace(/[#*_>`]/g, " ")
    .replace(/\[(.*?)\]\(.*?\)/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}

function speechText(entry: SessionItem, source: DeckItem | Variant): string {
  const stem = itemStem(source) || entry.runtime.passage || source.prompt;
  if (session?.inFormRecall && entry.item.word && stem) {
    return plainSpeechText(stem.replace(wordFormPattern(entry.item.word), " blank "));
  }
  return plainSpeechText(stem);
}

function formatStem(stem: string, word: string | undefined, mode: "mark" | "cloze"): string {
  if (!word) {
    return esc(stem);
  }
  const match = wordFormPattern(word).exec(stem);
  if (!match || match.index === undefined) {
    return esc(stem);
  }
  const end = match.index + match[0].length;
  const before = esc(stem.slice(0, match.index));
  const after = esc(stem.slice(end));
  if (mode === "cloze") {
    return `${before}<span class="english-cloze" aria-label="空格">______</span>${after}`;
  }
  return `${before}<mark class="english-word-mark">${esc(match[0])}</mark>${after}`;
}

function fillVoicePicker(): void {
  const voices = listEnglishVoices();
  const currentVoice = getVoiceName();
  const currentRate = getRate();
  dom.voiceRate.innerHTML = RATE_OPTIONS.map(
    ([rate, label]) =>
      `<option value="${rate}"${Math.abs(rate - currentRate) < 0.01 ? " selected" : ""}>${label}</option>`,
  ).join("");
  if (voices.length === 0) {
    dom.voiceName.innerHTML = `<option value="">系统还没有美式英语音色</option>`;
    dom.voiceName.disabled = true;
    dom.voiceTry.disabled = true;
    return;
  }
  dom.voiceName.disabled = !canSpeak();
  dom.voiceTry.disabled = !canSpeak();
  dom.voiceName.innerHTML = voices
    .map(
      (voice) =>
        `<option value="${esc(voice.name)}"${voice.name === currentVoice ? " selected" : ""}>${esc(voice.label)}</option>`,
    )
    .join("");
}

function bindVoicePicker(): void {
  fillVoicePicker();
  window.speechSynthesis?.addEventListener("voiceschanged", fillVoicePicker);
  const hear = () => {
    try {
      previewVoice();
    } catch (error) {
      dom.voiceTry.title = String(error);
    }
  };
  dom.voiceRate.addEventListener("change", () => {
    setRate(Number(dom.voiceRate.value));
    hear();
  });
  dom.voiceName.addEventListener("change", () => {
    setVoiceName(dom.voiceName.value);
    hear();
  });
  dom.voiceTry.addEventListener("click", hear);
}

const relationLabels = {
  selection_basis: "选材依据",
  quoted: "原文节选",
  adapted: "据原文改写",
  exam_alignment: "考核对齐",
} as const;

const skillLabels = {
  listen: "听",
  speak: "说",
  read: "读",
  write: "写",
} as const;

function sourcePanelHtml(entry: SessionItem): string {
  const refs = [...(entry.deck.source_refs ?? []), ...(entry.item.source_refs ?? [])].filter(
    (ref, index, all) =>
      all.findIndex((candidate) => candidate.source_id === ref.source_id && candidate.relation === ref.relation) === index,
  );
  const rows = refs
    .map((ref) => {
      const source = sourceCatalog.get(ref.source_id);
      if (!source) {
        return "";
      }
      return `<button type="button" class="english-source-link" data-source-url="${esc(ref.locator_url ?? source.url)}">
          <span>${esc(relationLabels[ref.relation])}</span>
          <strong>${esc(source.title)}</strong>
          <small>${esc(source.publisher)} · ${esc(source.license)}${ref.locator ? `<br>定位：${esc(ref.locator)}` : ""}<br>${esc(ref.note)}</small>
        </button>`;
    })
    .join("");
  const media = (entry.item.media ?? entry.deck.media ?? [])
    .map((asset) =>
      asset.kind === "audio"
        ? `<div class="english-original-media"><strong>真人原声 · ${esc(asset.title)}</strong>
             <audio controls preload="none" src="${esc(asset.url)}"></audio></div>`
        : `<details class="english-original-media"><summary>原教材视频 · ${esc(asset.title)}</summary>
             <video controls playsinline preload="metadata" src="${esc(asset.url)}"></video></details>`,
    )
    .join("");

  return `<section class="english-source-panel" aria-label="教材依据与语音练习">
      <div class="english-source-head"><strong>教材依据</strong><span>点开可核查原教材、发布者和授权说明</span></div>
      <div class="english-source-list">${rows || "<p class=\"english-source-empty\">这一课还没有对上可核对的来源。</p>"}</div>
      <div class="english-voice-tools">
        <button type="button" data-voice="speak"${canSpeak() ? "" : " disabled"}>系统朗读</button>
        <button type="button" data-voice="stop-speak"${canSpeak() ? "" : " disabled"}>停止朗读</button>
        <button type="button" data-voice="record"${voiceRecorder.supported() ? "" : " disabled"}>跟读录音</button>
        <button type="button" data-voice="stop-record" disabled>停止录音</button>
        <span class="english-voice-status" role="status">录音只在本次页面中回听，不上传、不判分。</span>
      </div>
      <audio class="english-recording-playback" controls hidden aria-label="跟读录音回听"></audio>
      ${media}
    </section>`;
}

function bindSourceAndVoice(entry: SessionItem, source: DeckItem | Variant): void {
  const status = dom.question.querySelector<HTMLElement>(".english-voice-status");
  const record = dom.question.querySelector<HTMLButtonElement>('[data-voice="record"]');
  const stopRecord = dom.question.querySelector<HTMLButtonElement>('[data-voice="stop-record"]');
  const playback = dom.question.querySelector<HTMLAudioElement>(".english-recording-playback");
  const setStatus = (message: string) => {
    if (status) status.textContent = message;
  };

  dom.question.querySelectorAll<HTMLButtonElement>("[data-source-url]").forEach((button) => {
    button.addEventListener("click", () => {
      const url = button.dataset.sourceUrl;
      if (url) {
        void openExternal(url).catch((error) => setStatus(`原教材链接打开失败：${String(error)}`));
      }
    });
  });
  dom.question.querySelector<HTMLButtonElement>('[data-voice="speak"]')?.addEventListener("click", () => {
    try {
      speakEnglish(speechText(entry, source));
      setStatus("正在用系统英文语音朗读；真人原声请使用下方教材媒体。");
    } catch (error) {
      setStatus(String(error));
    }
  });
  dom.question.querySelector<HTMLButtonElement>('[data-voice="stop-speak"]')?.addEventListener("click", () => {
    stopSpeaking();
    setStatus("朗读已停止。");
  });
  record?.addEventListener("click", () => {
    record.disabled = true;
    if (stopRecord) stopRecord.disabled = true;
    if (playback) playback.hidden = true;
    setStatus("正在请求麦克风并录音……");
    void voiceRecorder
      .start()
      .then(() => {
        if (stopRecord) stopRecord.disabled = false;
        setStatus("正在录音；读完后点“停止录音”。");
      })
      .catch((error) => {
        record.disabled = false;
        if (stopRecord) stopRecord.disabled = true;
        setStatus(`无法录音：${String(error)}`);
      });
  });
  stopRecord?.addEventListener("click", () => {
    stopRecord.disabled = true;
    void voiceRecorder
      .stop()
      .then((url) => {
        if (playback) {
          playback.src = url;
          playback.hidden = false;
        }
        if (record) record.disabled = false;
        setStatus("录音完成，可在下方回听并与原声或系统朗读对照。");
      })
      .catch((error) => {
        if (record) record.disabled = false;
        setStatus(`停止录音失败：${String(error)}`);
      });
  });
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
      const assessment = mastery.get(track.id);
      const lastAssessment = assessment && assessment.last_total > 0
        ? `最近 ${assessment.last_correct}/${assessment.last_total}`
        : "还未参加独立考核";
      const detail = stats.passed
        ? `已通过 · ${lastAssessment}`
        : assessment && assessment.last_total > 0
          ? `待通过 · ${lastAssessment}`
          : stats.done === 0
            ? "待完成 · 还没开始"
            : `待考核 · 已练 ${stats.done}/${stats.total}`;
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
      const examButton = `<button type="button" data-exam="${esc(track.id)}"${isFocus ? " data-primary" : ""}>${
        stats.passed ? "再考一次" : `开始${track.title}考核`
      }</button>`;
      const right =
        track.kind === "writing"
          ? `<button type="button" data-rubric="${esc(track.id)}">评分维度</button>${examButton}`
          : examButton;
      const measureRight = stats.due > 0 ? `到期复习 ${stats.due}` : stats.weakTag ? `薄弱：${stats.weakTag}` : "暂无薄弱项";
      const measureLeft =
        stats.accuracy === null ? `练习覆盖 ${pct(stats.coverage)}` : `近期正确率 ${pct(stats.accuracy)}`;
      return `<section class="english-track">
          <div class="english-track-top"><h3>${esc(track.title)}</h3><span class="english-track-state">${esc(
            trackState(stats),
          )}</span></div>
          <p class="english-track-desc">${esc(track.goal)}</p>
          <div class="english-skill-strip" aria-label="训练动作">${track.skills
            .map((skill) => `<span data-skill="${skill}">${skillLabels[skill]}</span>`)
            .join("")}</div>
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

function renderOutcomes(): void {
  const outcomes = computeOutcomes({
    stages: curriculum.stages,
    tracks: [...runtimes.values()].map((runtime) => ({
      kind: runtime.track.kind,
      stageId: runtime.stage.id,
      items: runtime.deck.items,
      passed: trackPassed(runtime.track),
    })),
    review,
    mistakeCount: mistakes.length,
    attempts: attemptStats,
    nowSeconds: now(),
  });
  const earned = outcomes.badges.filter((badge) => badge.earned).length;
  const accuracy =
    outcomes.accuracy === null ? "还没有作答记录" : `作答正确率 ${pct(outcomes.accuracy)}`;
  dom.outcomes.innerHTML = `
    <p class="english-cheer">${esc(outcomes.cheer)}</p>
    <div class="english-outcome-stats">
      <div class="english-outcome-stat"><strong>${outcomes.streak}</strong><span>连续天数</span></div>
      <div class="english-outcome-stat"><strong>${outcomes.heldItems}</strong><span>已稳住</span></div>
      <div class="english-outcome-stat"><strong>${outcomes.tracksPassed}/${outcomes.tracksTotal}</strong><span>通过考核</span></div>
      <div class="english-outcome-stat"><strong>${outcomes.attempts}</strong><span>累计作答</span></div>
    </div>
    <div class="english-outcome-kinds">
      ${outcomes.byKind
        .map(
          (kind) => `
        <div class="english-outcome-kind">
          <span>${esc(kind.title)}</span>
          <div class="english-meter" aria-hidden="true"><span style="width:${pct(
            kind.total === 0 ? 0 : kind.seen / kind.total,
          )}"></span></div>
          <small>${kind.seen}/${kind.total} · 稳住 ${kind.held}</small>
        </div>`,
        )
        .join("")}
    </div>
    <div class="english-badges">
      ${outcomes.badges
        .map(
          (badge) =>
            `<span class="english-badge" data-earned="${badge.earned}" title="${esc(
              badge.hint,
            )}">${esc(badge.title)}</span>`,
        )
        .join("")}
    </div>
    <p class="english-outcome-note">${esc(accuracy)} · 已点亮 ${earned} / ${outcomes.badges.length} 枚徽章</p>`;
}

function showOverview(): void {
  stopSpeaking();
  voiceRecorder.reset();
  session = null;
  setView("overview");
  renderTopBar();
  renderStageList();
  renderOutcomes();
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

function sessionOf(runtime: TrackRuntime, deck: Deck, items: DeckItem[], mode: SessionMode, title: string): Session {
  return {
    listTitle: `${runtime.track.title}${mode === "exam" ? "考核" : "练习"}`,
    crumb: `${runtime.stage.title} · ${runtime.track.title}`,
    title,
    goal: runtime.track.goal,
    mode,
    items: items.map((item) => ({ item, runtime, deck })),
    index: 0,
    answered: false,
    inVariant: false,
    variantDone: false,
    inFormRecall: false,
    formRecallDone: false,
    attempts: [],
  };
}

function startPractice(runtime: TrackRuntime, items: DeckItem[], focusId?: string): void {
  const batch = practiceBatch(items, review, now(), PRACTICE_SESSION_SIZE, focusId);
  const next = sessionOf(runtime, runtime.deck, batch, "practice", "先判断，再看解析");
  openSession(next, runtime.passage);
}

function startExam(runtime: TrackRuntime): void {
  const next = sessionOf(
    runtime,
    runtime.assessment,
    runtime.assessment.items,
    "exam",
    "独立平行材料考核",
  );
  next.assessmentId = runtime.assessment.assessment_id;
  next.goal = "题目与练习材料不同；作答期间不给解析，全部答完后统一提交和反馈。";
  openSession(next);
}

function startDueSession(): void {
  const stamp = now();
  const items: SessionItem[] = [];
  for (const runtime of runtimes.values()) {
    for (const item of orderItems(runtime.deck.items, review, stamp)) {
      const state = review.get(item.id);
      if (state && isDue(state, stamp) && items.length < REVIEW_SESSION_SIZE) {
        items.push({ item, runtime, deck: runtime.deck });
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
    inFormRecall: false,
    formRecallDone: false,
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

function renderContext(entry: SessionItem, source: DeckItem | Variant, revealListening = false): void {
  const passage = entry.runtime.passage;
  const stem = itemStem(source);
  if (stem) {
    if (entry.item.kind === "listening" && !revealListening) {
      dom.practiceContext.className = "english-context english-listening-hidden";
      dom.practiceContext.innerHTML = `<span>先播放原声或系统朗读完成听辨，再决定是否查看文本。</span>
        <button type="button" data-reveal-listening>显示文本</button>`;
      dom.practiceContext.style.display = "flex";
      dom.practiceContext
        .querySelector<HTMLButtonElement>("[data-reveal-listening]")
        ?.addEventListener("click", () => renderContext(entry, source, true));
      return;
    }
    const vocab = entry.runtime.track.kind === "vocab" && Boolean(entry.item.word);
    const mode = session?.inFormRecall ? "cloze" : "mark";
    dom.practiceContext.className = vocab
      ? "english-context english-vocab-stem"
      : "english-context";
    dom.practiceContext.innerHTML = vocab ? formatStem(stem, entry.item.word, mode) : esc(stem);
    dom.practiceContext.style.display = "block";
    return;
  }
  if (passage) {
    dom.practiceContext.className = "english-context english-markdown";
    dom.practiceContext.innerHTML = renderMarkdown(passage);
    dom.practiceContext.style.display = "block";
    return;
  }
  dom.practiceContext.className = "english-context";
  dom.practiceContext.style.display = "none";
}

function renderCard(): void {
  const entry = current();
  if (!session || !entry) {
    return;
  }
  session.answered = false;
  stopSpeaking();
  voiceRecorder.reset();
  session.inVariant = false;
  session.variantDone = false;
  session.inFormRecall = false;
  session.formRecallDone = false;
  session.pendingVocab = undefined;
  dom.practiceCrumb.textContent = `${entry.runtime.stage.title} · ${entry.runtime.track.title} · ${
    errorTagOf(entry.item, entry.deck.kind)
  }`;
  renderSide();
  if ((entry.item.choices?.length ?? 0) === 0) {
    renderWriting(entry);
  } else {
    renderChoices(entry, entry.item, false);
  }
}

function wordCardHtml(item: DeckItem): string {
  if (!item.word) {
    return "";
  }
  const gloss =
    item.senses && item.senses.length > 0
      ? item.senses.map((sense) => `${sense.pos} ${sense.gloss}`).join("；")
      : (item.choices?.find((choice) => choice.ok)?.label ?? "");
  return `<div class="english-word-card"><strong>${esc(item.word)}</strong><span>${esc(gloss)}</span></div>`;
}

function vocabCue(inFormRecall: boolean): string {
  return inFormRecall
    ? "先听或默读挖空后的句子，再把词形提取出来。"
    : "先听或读原句，再判断标记词在本句的意思；词形先不摊开。";
}

function needsFormRecall(entry: SessionItem): boolean {
  return (
    Boolean(session) &&
    session!.mode === "practice" &&
    entry.runtime.track.kind === "vocab" &&
    Boolean(entry.item.word) &&
    !session!.formRecallDone &&
    vocabFormProbe(entry.item, entry.deck.items) !== null
  );
}

function renderChoices(entry: SessionItem, source: DeckItem | Variant, inVariant: boolean): void {
  if (!session) {
    return;
  }
  session.answered = false;
  session.inVariant = inVariant;
  renderContext(entry, source);

  const vocab = entry.runtime.track.kind === "vocab" && Boolean(entry.item.word);
  const kind = session.inFormRecall
    ? "提取词形"
    : inVariant
      ? "变式"
      : vocab
        ? "提取义项"
        : itemKindLabel(entry.item.kind);
  const cue = vocab ? `<p class="english-task-cue">${esc(vocabCue(session.inFormRecall))}</p>` : "";
  const choices = shuffled(source.choices ?? []);
  dom.question.innerHTML = `${sourcePanelHtml(entry)}${cue}<p class="english-prompt">${esc(source.prompt)}${
    kind ? `<span class="english-track-state"> · ${esc(kind)}</span>` : ""
  }</p>
    <div class="english-choices">${choices
      .map(
        (choice) =>
          `<button type="button" class="english-choice" data-label="${esc(choice.label)}">${esc(choice.label)}</button>`,
      )
      .join("")}</div>
    <div class="english-feedback" id="feedback"></div>`;

  bindSourceAndVoice(entry, source);

  dom.question.querySelectorAll<HTMLButtonElement>("[data-label]").forEach((button) => {
    button.addEventListener("click", () => {
      const index = (source.choices ?? []).findIndex((choice) => choice.label === button.dataset.label);
      void answerChoice(entry, source, index, inVariant);
    });
  });
}

function renderFormRecall(entry: SessionItem): void {
  if (!session) {
    return;
  }
  const probe = vocabFormProbe(entry.item, entry.deck.items);
  if (!probe) {
    session.formRecallDone = true;
    void goNext();
    return;
  }
  session.inFormRecall = true;
  session.formRecallDone = false;
  renderChoices(entry, probe, true);
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
  const buttons = Array.from(dom.question.querySelectorAll<HTMLButtonElement>("[data-label]"));
  if (entry.item.kind === "listening" || session.inFormRecall) {
    renderContext(entry, source, true);
  }

  const formRecall = session.inFormRecall;
  const waitForForm = !formRecall && needsFormRecall(entry);

  if (formRecall) {
    const pending = session.pendingVocab;
    const meaningCorrect = pending?.meaningCorrect ?? true;
    const overall = meaningCorrect && correct;
    session.attempts.push({
      item: entry.item,
      runtime: entry.runtime,
      correct: overall,
      picked: `${pending?.picked ?? ""} → ${picked.label}`,
      answer: `${pending?.answer ?? ""} / ${answer.label}`,
      why: answer.why ?? pending?.why ?? "",
    });
    let stored = true;
    if (session.mode === "practice") {
      stored = await recordAnswer(entry, {
        correct: overall,
        selected: picked.label,
        answer: answer.label,
        explanation: answer.why ?? "",
        isVariant: correct,
      });
    }
    paintChoiceResult(buttons, source, picked.label);
    const feedback = document.getElementById("feedback");
    if (feedback) {
      feedback.innerHTML = formRecallFeedback(entry, correct, overall, stored, picked, answer, choices, position);
      feedback.classList.add("is-visible");
      session.formRecallDone = true;
      session.inFormRecall = false;
      appendNextAction(entry, overall, feedback);
    }
    return;
  }

  if (!waitForForm) {
    session.attempts.push({
      item: entry.item,
      runtime: entry.runtime,
      correct,
      picked: picked.label,
      answer: answer.label,
      why: answer.why ?? "",
    });
  }

  let stored = true;
  if (session.mode === "practice" && !waitForForm) {
    stored = await recordAnswer(entry, {
      correct,
      selected: picked.label,
      answer: answer.label,
      explanation: answer.why ?? "",
      isVariant: inVariant,
    });
  } else if (waitForForm) {
    session.pendingVocab = {
      meaningCorrect: correct,
      picked: picked.label,
      answer: answer.label,
      why: answer.why ?? "",
    };
  }

  if (session.mode === "exam") {
    buttons.forEach((button) => {
      button.disabled = true;
    });
    await goNext();
    return;
  }

  paintChoiceResult(buttons, source, picked.label);

  const feedback = document.getElementById("feedback");
  if (feedback) {
    feedback.innerHTML = meaningFeedback(entry, correct, stored && !waitForForm, picked, answer, choices, position, inVariant);
    feedback.classList.add("is-visible");
    if (inVariant) {
      session.variantDone = true;
    }
    appendNextAction(entry, correct, feedback);
  }
}

function paintChoiceResult(buttons: HTMLButtonElement[], source: DeckItem | Variant, pickedLabel: string): void {
  const choices = source.choices ?? [];
  buttons.forEach((button) => {
    button.disabled = true;
    const choice = choices.find((item) => item.label === button.dataset.label);
    if (choice?.ok) {
      button.dataset.result = "ok";
    } else if (button.dataset.label === pickedLabel) {
      button.dataset.result = "bad";
    }
  });
}

function meaningFeedback(
  entry: SessionItem,
  correct: boolean,
  stored: boolean,
  picked: Choice,
  answer: Choice,
  choices: Choice[],
  position: number,
  inVariant: boolean,
): string {
  const card = inVariant ? "" : wordCardHtml(entry.item);
  if (correct) {
    return `<div class="english-feedback-head"><strong>判断正确</strong><span>${
      session?.pendingVocab ? "还要把词形填回去" : "不进入错题本"
    }</span></div>
         ${card}<p>${esc(picked.why ?? answer.why ?? "")}</p>${otherWhyHtml(choices, position)}`;
  }
  return `<div class="english-feedback-head"><strong data-wrong="true">${
    session?.pendingVocab ? "先看清义项，再提取词形" : stored ? "已自动加入错题本" : "错题未能保存"
  }</strong><span>错因：${esc(errorTagOf(entry.item, entry.runtime.deck.kind))}</span></div>
         ${card}<p>${esc(answer.why ?? "")}</p>
         ${picked.why ? `<p>你选的：${esc(picked.why)}</p>` : ""}
         ${otherWhyHtml(choices, position)}`;
}

function formRecallFeedback(
  entry: SessionItem,
  formCorrect: boolean,
  overall: boolean,
  stored: boolean,
  picked: Choice,
  answer: Choice,
  choices: Choice[],
  position: number,
): string {
  const card = wordCardHtml(entry.item);
  if (overall) {
    return `<div class="english-feedback-head"><strong>义项和词形都提取对了</strong><span>不进入错题本</span></div>
      ${card}<p>${esc(picked.why ?? answer.why ?? "")}</p>${otherWhyHtml(choices, position)}`;
  }
  if (!formCorrect) {
    return `<div class="english-feedback-head"><strong data-wrong="true">${
      stored ? "已记入错题本" : "结果未能保存"
    }</strong><span>认得意思还要能把词形提取出来</span></div>
      ${card}<p>${esc(answer.why ?? "")}</p>
      ${picked.why ? `<p>你选的：${esc(picked.why)}</p>` : ""}
      ${otherWhyHtml(choices, position)}`;
  }
  return `<div class="english-feedback-head"><strong data-wrong="true">${
    stored ? "已记入错题本" : "结果未能保存"
  }</strong><span>词形填对了，但本句义项仍算错过</span></div>
      ${card}<p>${esc(session?.pendingVocab?.why ?? "")}</p>`;
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
  const needForm = needsFormRecall(entry);
  const hasVariant = (entry.item.variants?.length ?? 0) > 0;
  const needVariant =
    !needForm && entry.runtime.track.kind !== "vocab" && hasVariant && !session.variantDone;
  const last = session.index >= session.items.length - 1;
  const buttons = [
    needForm
      ? `<button type="button" class="english-feedback-action" data-act="form" data-primary>下一步：把词填回去</button>`
      : "",
    needVariant ? `<button type="button" class="english-feedback-action" data-act="variant">换一句再问一次</button>` : "",
    needForm
      ? ""
      : `<button type="button" class="english-feedback-action" data-act="next"${
          needVariant ? "" : " data-primary"
        }>${last ? "练完，回路线" : "下一题"}</button>`,
  ]
    .filter(Boolean)
    .join(" ");
  feedback.insertAdjacentHTML("beforeend", `<div class="english-mistake-actions">${buttons}</div>`);
  void correct;

  feedback.querySelector<HTMLButtonElement>('[data-act="form"]')?.addEventListener("click", () => {
    renderFormRecall(entry);
  });
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

  dom.question.innerHTML = `${sourcePanelHtml(entry)}<p class="english-prompt">${esc(item.prompt)}</p>
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

  bindSourceAndVoice(entry, item);

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

  let stored = true;
  if (session.mode === "practice") {
    stored = await recordAnswer(entry, {
      correct: grade.correct,
      selected: text.slice(0, 500),
      answer: item.reference ?? "",
      explanation: verdict,
      isVariant: false,
    });
  }

  if (session.mode === "exam") {
    await goNext();
    return;
  }

  dom.question.querySelector('[data-act="submit"]')?.remove();
  const feedback = document.getElementById("feedback");
  if (feedback) {
    feedback.innerHTML = `<div class="english-feedback-head"><strong${
      grade.correct ? "" : ' data-wrong="true"'
    }>${grade.correct ? "形式要求达到" : stored ? "形式要求未达到，已记入错题本" : "形式要求未达到，保存失败"}</strong><span>${esc(verdict)}</span></div>
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

async function recordAnswer(entry: SessionItem, record: AnswerRecord): Promise<boolean> {
  const { runtime, item } = entry;
  try {
    const state = await saveAnswer({
      item_id: item.id,
      topic_id: runtime.track.id,
      kind: entry.deck.kind,
      correct: record.correct,
      deck_total: entry.deck.items.length,
      selected_answer: record.selected,
      correct_answer: record.answer,
      explanation: record.explanation,
      error_tag: errorTagOf(item, entry.deck.kind),
      is_variant: record.isVariant,
    });
    review.set(state.item_id, state);
    return true;
  } catch (error) {
    dom.question.insertAdjacentHTML(
      "beforeend",
      `<p class="english-empty">这次结果没能写进进度库：${esc(String(error))}</p>`,
    );
    return false;
  }
}

async function goNext(): Promise<void> {
  if (!session) {
    return;
  }
  if (session.index >= session.items.length - 1) {
    if (session.mode === "exam") {
      try {
        await persistExamResult(session);
        await refreshProgress();
        renderReport();
      } catch (error) {
        dom.question.innerHTML = `<div class="english-feedback is-visible">
          <div class="english-feedback-head"><strong data-wrong="true">交卷没有保存</strong></div>
          <p>${esc(String(error))}</p>
          <div class="english-mistake-actions"><button type="button" data-primary data-act="retry-submit">重新交卷</button></div>
        </div>`;
        dom.question.querySelector<HTMLButtonElement>('[data-act="retry-submit"]')?.addEventListener("click", () => {
          void goNext();
        });
      }
      return;
    }
    await backToOverview();
    return;
  }
  session.index += 1;
  renderCard();
}

async function persistExamResult(active: Session): Promise<void> {
  if (!active.assessmentId || active.attempts.length === 0) {
    throw new Error("独立考核缺少 assessment_id 或作答结果");
  }
  const topicId = active.items[0]?.runtime.track.id;
  if (!topicId) {
    throw new Error("独立考核缺少轨道 id");
  }
  const right = active.attempts.filter((attempt) => attempt.correct).length;
  const state = await saveAssessmentResult({
    assessment_id: active.assessmentId,
    topic_id: topicId,
    correct: right,
    total: active.attempts.length,
  });
  mastery.set(topicId, state);
}

function renderReport(): void {
  const active = session;
  if (!active) {
    return;
  }
  const right = active.attempts.filter((attempt) => attempt.correct).length;
  const score = active.attempts.length === 0 ? 0 : Math.round((right / active.attempts.length) * 100);
  const pass = score >= 80;
  const topicId = active.items[0]?.runtime.track.id;
  const qualificationRetained = topicId ? (mastery.get(topicId)?.mastery ?? 0) === 1 : false;

  active.index = active.items.length;
  renderSide();
  renderTopBar();
  dom.practiceTitle.textContent = "已交卷";
  dom.practiceGoal.textContent = pass
    ? "本轨阶段资格已经记录；之后的复习答错不会撤销它。"
    : qualificationRetained
      ? "本次没有达到 80%，但既有通过资格保留；可按报告回练习台补强。"
      : "逐题对照解析，再回练习台补强薄弱点；考核题不混入练习错题本。";
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
    "字数和连接方式只给练习反馈，不决定阶段资格；独立写作考核另测任务回应、组织、衔接和语言选择。";
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
  dom.mistakeList.innerHTML = mistakeGroups()
    .map((group) => {
      const runtime = runtimes.get(group.items[0]!.topic_id);
      const holds = group.items.some((mistake) => mistake.item_id === currentMistakeId);
      return `<button type="button" class="english-item" data-tag="${esc(group.tag)}" aria-current="${holds}">
          <span>${esc(group.tag)}</span><small>${esc(runtime?.track.title ?? "")} · ${group.items.length} 次</small>
        </button>`;
    })
    .join("");
  renderMistakeDetail();
}

interface MistakeGroup {
  tag: string;
  items: Mistake[];
}

/** 草图的错题本左栏按错因归组：一个错因一行，右边是这一组的题数。 */
function mistakeGroups(): MistakeGroup[] {
  const groups = new Map<string, Mistake[]>();
  for (const mistake of mistakes) {
    const bucket = groups.get(mistake.error_tag);
    if (bucket) {
      bucket.push(mistake);
    } else {
      groups.set(mistake.error_tag, [mistake]);
    }
  }
  return [...groups].map(([tag, items]) => ({ tag, items }));
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

  const group = mistakeGroups().find((entry) => entry.tag === mistake.error_tag);
  const position = (group?.items.findIndex((entry) => entry.item_id === mistake.item_id) ?? 0) + 1;
  const groupSize = group?.items.length ?? 1;
  dom.mistakeDetail.innerHTML = `<p class="english-crumb">${esc(runtime?.stage.title ?? "")} · ${esc(
    runtime?.track.title ?? "",
  )} · 错因：${esc(mistake.error_tag)}${groupSize > 1 ? ` · 本组第 ${position} / ${groupSize} 题` : ""}</p>
    <h2>不是重做原题，而是纠正判断</h2>
    <p class="english-practice-goal">保留原题、错误答案和解析，再用同一知识点的变式确认是否真正会了。</p>
    ${stem ? `<blockquote class="english-context">${item?.word ? formatStem(stem, item.word, "mark") : esc(stem)}</blockquote>` : ""}
    <div class="english-answer-compare">
      <div class="english-answer-box" data-kind="wrong"><strong>当时的错误判断</strong><span>${esc(
        mistake.selected_answer,
      )}</span></div>
      <div class="english-answer-box" data-kind="right"><strong>正确判断</strong><span>${esc(
        mistake.correct_answer,
      )}</span></div>
    </div>
    <div class="english-mistake-rule"><strong>移出规则：</strong>不同日期连续答对原知识点和一道未见变式后，系统自动移出；再次答错则重新累计。当前已连对 ${
      mistake.correct_days
    } 天，变式${mistake.variant_correct ? "已做对" : "还没做对"}。</div>
    <div class="english-mistake-actions">
      <button type="button" data-primary data-act="retry">${hasVariant ? "开始一道变式" : "重做这道题"}</button>
      <button type="button" data-act="explain">查看完整解析</button>
    </div>
    <div class="english-feedback" id="mistake-explain"></div>`;

  dom.mistakeDetail.querySelector<HTMLButtonElement>('[data-act="retry"]')?.addEventListener("click", () => {
    if (!runtime || !item) {
      return;
    }
    const sameTrack = (group?.items ?? [])
      .filter((entry) => entry.topic_id === mistake.topic_id)
      .map((entry) => runtime.deck.items.find((deckItem) => deckItem.id === entry.item_id))
      .filter((entry): entry is DeckItem => entry !== undefined);
    startPractice(runtime, sameTrack.length > 0 ? sameTrack : [item], mistake.item_id);
  });
  dom.mistakeDetail.querySelector<HTMLButtonElement>('[data-act="explain"]')?.addEventListener("click", () => {
    const box = document.getElementById("mistake-explain");
    if (!box) {
      return;
    }
    const choices = item?.choices ?? [];
    const answer = choices.find((choice) => choice.ok);
    box.innerHTML = `<p>${esc(mistake.explanation || answer?.why || "这道题没有留下解析。")}</p>
      ${choices
        .filter((choice) => !choice.ok && choice.why)
        .map((choice) => `<p>${esc(choice.label)}——${esc(choice.why ?? "")}</p>`)
        .join("")}
      ${
        runtime
          ? `<button type="button" class="english-feedback-action" data-act="open-track">回到${esc(
              runtime.track.title,
            )}练习</button>`
          : ""
      }`;
    box.classList.add("is-visible");
    box.querySelector<HTMLButtonElement>('[data-act="open-track"]')?.addEventListener("click", () => {
      if (runtime) {
        startPractice(runtime, runtime.deck.items, mistake.item_id);
      }
    });
  });
}

/* --------------------------------------------------------------- 装配 */

async function refreshProgress(): Promise<void> {
  const [nextReview, nextMastery, nextMistakes, nextAttempts] = await Promise.all([
    loadReview(),
    loadMastery(),
    loadMistakes(),
    loadAttemptStats(),
  ]);
  review = nextReview;
  mastery = nextMastery;
  mistakes = nextMistakes;
  attemptStats = nextAttempts;
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
    const tag = (event.target as HTMLElement).closest<HTMLElement>("[data-tag]")?.dataset.tag;
    const group = tag ? mistakeGroups().find((entry) => entry.tag === tag) : undefined;
    if (group) {
      currentMistakeId = group.items[0]!.item_id;
      showMistakes();
    }
  });
}

function fail(error: unknown): void {
  dom.tracks.innerHTML = `<section class="english-track"><h3>没能把课表读起来</h3><p class="english-track-desc">${esc(
    String(error),
  )}</p></section>`;
}

async function loadTrackDeck(track: Track): Promise<Deck> {
  const paths = track.decks?.length ? track.decks : track.deck ? [track.deck] : [];
  if (paths.length === 0) {
    throw new Error(`${track.id} 没有配置练习内容`);
  }
  const decks = await Promise.all(paths.map(loadDeck));
  const first = decks[0]!;
  for (const deck of decks) {
    if (deck.topic_id !== track.id || (decks.length > 1 && deck.kind !== first.kind)) {
      throw new Error(`${track.id} 的内容单元 topic_id 或 kind 不一致`);
    }
  }
  const seenRefs = new Set<string>();
  const sourceRefs = decks.flatMap((deck) => deck.source_refs).filter((ref) => {
    const key = JSON.stringify(ref);
    if (seenRefs.has(key)) {
      return false;
    }
    seenRefs.add(key);
    return true;
  });
  return {
    ...first,
    source_refs: sourceRefs,
    items: decks.flatMap((deck) => deck.items),
  };
}

async function boot(): Promise<void> {
  const [info, loaded, loadedSources] = await Promise.all([loadAppInfo(), loadCurriculum(), loadSourceCatalog()]);
  curriculum = loaded;
  for (const source of loadedSources.sources) {
    sourceCatalog.set(source.id, source);
  }
  dom.title.textContent = curriculum.title;
  dom.subtitle.textContent = `${curriculum.stages.map((stage) => stage.title).join(" → ")} · ${curriculum.tagline}`;
  dom.endpoint.innerHTML = `<strong>终点</strong><br>${esc(curriculum.endpoint ?? curriculum.description)}`;
  void info;

  await Promise.all(
    curriculum.stages.flatMap((stage) =>
      stage.tracks.map(async (track: Track) => {
        const [deck, assessment, passage] = await Promise.all([
          loadTrackDeck(track),
          loadDeck(track.assessment),
          track.passage ? loadText(track.passage) : Promise.resolve(undefined),
        ]);
        runtimes.set(track.id, { stage, track, deck, assessment, passage });
      }),
    ),
  );

  await refreshProgress();
  currentStageId = activeStage().id;
  bindEvents();
  await voicesReady();
  bindVoicePicker();
  showOverview();
}

boot().catch(fail);
