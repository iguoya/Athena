// 后端桥：内容读取与进度读写。
//
// 桌面（Tauri）下一律走 src-tauri 的命令，排期、掌握度和错题出库规则只有 Rust 一份。
// 浏览器（npm run dev）下内容从打包进来的 content/ 读，进度退化为本次会话的内存记录：
// 不排期、不落库、刷新即清空——只为调界面，不是第二套判分规则（README 已写明）。

import type {
  AppInfo,
  Curriculum,
  Deck,
  Mistake,
  ReviewInput,
  ReviewState,
  MasteryState,
} from "./types";

export const isDesktop =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

async function call<T>(command: string, args?: Record<string, unknown>): Promise<T> {
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke<T>(command, args);
}

const bundled = import.meta.glob("../content/**/*.{json,md}", {
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
    title: "英语自学",
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

export async function loadReview(): Promise<Map<string, ReviewState>> {
  if (!isDesktop) {
    return new Map(sessionReview);
  }
  const raw = await call<Record<string, ReviewState>>("load_all_review");
  return new Map(Object.entries(raw));
}

export async function loadMastery(): Promise<Map<string, MasteryState>> {
  if (!isDesktop) {
    return new Map();
  }
  const raw = await call<Record<string, MasteryState>>("load_all_mastery");
  return new Map(Object.entries(raw));
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
  const next: ReviewState = {
    item_id: input.item_id,
    reps: input.correct ? (previous?.reps ?? 0) + 1 : 0,
    ease: 2.5,
    interval_days: 0,
    due_at: String(Math.floor(Date.now() / 1000)),
    last_rating: input.correct ? 4 : 1,
  };
  sessionReview.set(input.item_id, next);

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
