// 后端桥：内容读取与进度读写。
//
// 桌面（Tauri）下一律走 src-tauri 的命令，排期、掌握度和错题出库规则只有 Rust 一份。
// 浏览器（npm run dev）下内容从打包进来的 content/ 读，进度退化为本次会话的内存记录：
// 不排期、不落库、刷新即清空——只为调界面，不是第二套判分规则（README 已写明）。

import type {
  AppInfo,
  AttemptStats,
  Curriculum,
  Deck,
  Mistake,
  ReviewInput,
  ReviewState,
  MasteryState,
  AssessmentInput,
  SourceCatalog,
} from "./types";

export const isDesktop =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

async function call<T>(command: string, args?: Record<string, unknown>): Promise<T> {
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke<T>(command, args);
}

const bundled = import.meta.glob(["../content/**/*.json", "../content/passages/**/*.md"], {
  query: "?raw",
  import: "default",
}) as Record<string, () => Promise<string>>;

async function readBundled(relative: string): Promise<string> {
  const loader = bundled[`../content/${relative}`];
  if (!loader) {
    throw new Error(`缺少内容文件：content/${relative}`);
  }
  return loader();
}

export async function loadAppInfo(): Promise<AppInfo> {
  if (isDesktop) {
    return call<AppInfo>("get_app_info");
  }
  return {
    title: "英语学习",
    content_root: "浏览器预览",
    store_path: "未连接进度库：答题结果不会保存",
  };
}

export async function loadCurriculum(): Promise<Curriculum> {
  if (isDesktop) {
    return call<Curriculum>("load_curriculum");
  }
  return JSON.parse(await readBundled("curriculum.json")) as Curriculum;
}

export async function loadSourceCatalog(): Promise<SourceCatalog> {
  if (isDesktop) {
    return call<SourceCatalog>("load_content_json", { relative: "sources/catalog.json" });
  }
  return JSON.parse(await readBundled("sources/catalog.json")) as SourceCatalog;
}

export async function loadDeck(relative: string): Promise<Deck> {
  if (isDesktop) {
    return call<Deck>("load_content_json", { relative });
  }
  return JSON.parse(await readBundled(relative)) as Deck;
}

export async function loadText(relative: string): Promise<string> {
  if (isDesktop) {
    return call<string>("load_content_text", { relative });
  }
  return readBundled(relative);
}

/** 浏览器预览用：本次会话答过的题与还没做对的题。 */
const sessionReview = new Map<string, ReviewState>();
const sessionMistakes = new Map<string, Mistake>();
const sessionMastery = new Map<string, MasteryState>();
const sessionAttempts = { attempts: 0, correct: 0 };

function emptyAttemptStats(): AttemptStats {
  return { attempts: 0, correct: 0, active_days: 0, streak: 0 };
}

export async function loadAttemptStats(): Promise<AttemptStats> {
  if (!isDesktop) {
    if (sessionAttempts.attempts === 0) {
      return emptyAttemptStats();
    }
    return {
      attempts: sessionAttempts.attempts,
      correct: sessionAttempts.correct,
      active_days: 1,
      streak: 1,
    };
  }
  return call<AttemptStats>("load_attempt_stats");
}

export async function loadReview(): Promise<Map<string, ReviewState>> {
  if (!isDesktop) {
    return new Map(sessionReview);
  }
  const raw = await call<Record<string, ReviewState>>("load_all_review");
  return new Map(Object.entries(raw));
}

export async function loadMastery(): Promise<Map<string, MasteryState>> {
  if (!isDesktop) {
    return new Map(sessionMastery);
  }
  const raw = await call<Record<string, MasteryState>>("load_all_mastery");
  return new Map(Object.entries(raw));
}

/** 整套独立考核交卷后才写入；练习作答不会调用这里。 */
export async function saveAssessmentResult(input: AssessmentInput): Promise<MasteryState> {
  if (isDesktop) {
    return call<MasteryState>("save_assessment_result", { input });
  }
  const previous = sessionMastery.get(input.topic_id);
  const passedNow = input.total > 0 && input.correct * 100 >= input.total * 80;
  const next: MasteryState = {
    mastery: previous?.mastery === 1 || passedNow ? 1 : 0,
    last_correct: input.correct,
    last_total: input.total,
  };
  sessionMastery.set(input.topic_id, next);
  return next;
}

export async function loadMistakes(): Promise<Mistake[]> {
  if (!isDesktop) {
    return [...sessionMistakes.values()];
  }
  return call<Mistake[]>("load_mistakes");
}

export async function saveAnswer(input: ReviewInput): Promise<ReviewState> {
  if (isDesktop) {
    return call<ReviewState>("save_answer", { input });
  }

  const previous = sessionReview.get(input.item_id);
  const nextReps = input.correct ? (previous?.reps ?? 0) + 1 : 0;
  const nextInterval = input.correct ? (nextReps === 1 ? 1 : nextReps === 2 ? 3 : 7) : 0;
  const next: ReviewState = {
    item_id: input.item_id,
    reps: nextReps,
    ease: 2.5,
    interval_days: nextInterval,
    due_at: String(Math.floor(Date.now() / 1000) + Math.round(nextInterval * 86400)),
    last_rating: input.correct ? 4 : 1,
  };
  sessionReview.set(input.item_id, next);
  sessionAttempts.attempts += 1;
  if (input.correct) {
    sessionAttempts.correct += 1;
  }

  if (input.correct) {
    sessionMistakes.delete(input.item_id);
  } else {
    const before = sessionMistakes.get(input.item_id);
    sessionMistakes.set(input.item_id, {
      item_id: input.item_id,
      topic_id: input.topic_id,
      kind: input.kind,
      error_tag: input.error_tag,
      wrong_count: (before?.wrong_count ?? 0) + 1,
      correct_days: 0,
      variant_correct: false,
      selected_answer: input.selected_answer,
      correct_answer: input.correct_answer,
      explanation: input.explanation,
    });
  }
  return next;
}
