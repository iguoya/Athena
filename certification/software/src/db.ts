// 进度库访问:应用里跑 Tauri invoke;纯浏览器 dev(vite 直开)降级到 localStorage,
// 让界面开发不必先起 Rust。降级层只服务开发,发布产物里不会出现。
import { invoke } from "@tauri-apps/api/core";

export interface KpSummary {
  kp_id: string;
  total: number;
  correct: number;
  last_at: number;
  streak: number;
}

export interface TodayStats {
  date: string;
  answered: number;
  correct: number;
}

export interface AttemptInput {
  course: string;
  chapterId: string;
  kpId: string;
  questionId: string;
  correct: boolean;
  mode: "chapter" | "past-exam";
}

const LS_KEY = "athena-software-attempts";

function inTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

function lsAttempts(): (AttemptInput & { answered_at: number })[] {
  try {
    return JSON.parse(localStorage.getItem(LS_KEY) ?? "[]");
  } catch {
    return [];
  }
}

export async function recordAttempt(input: AttemptInput): Promise<void> {
  if (inTauri()) {
    await invoke("record_attempt", {
      course: input.course,
      chapterId: input.chapterId,
      kpId: input.kpId,
      questionId: input.questionId,
      correct: input.correct,
      mode: input.mode,
    });
    return;
  }
  const all = lsAttempts();
  all.push({ ...input, answered_at: Date.now() });
  localStorage.setItem(LS_KEY, JSON.stringify(all));
}

function lsSummary(): KpSummary[] {
  const byKp = new Map<string, KpSummary>();
  for (const a of lsAttempts()) {
    const cur = byKp.get(a.kpId) ?? {
      kp_id: a.kpId,
      total: 0,
      correct: 0,
      last_at: 0,
      streak: 0,
    };
    cur.total += 1;
    cur.correct += a.correct ? 1 : 0;
    cur.last_at = Math.max(cur.last_at, a.answered_at);
    byKp.set(a.kpId, cur);
  }
  const out = [...byKp.values()];
  for (const s of out) {
    const recent = lsAttempts()
      .filter((a) => a.kpId === s.kp_id)
      .sort((a, b) => b.answered_at - a.answered_at);
    let streak = 0;
    for (const a of recent) {
      if (a.correct) streak += 1;
      else break;
    }
    s.streak = streak;
  }
  return out.sort((a, b) => b.last_at - a.last_at);
}

export async function attemptsSummary(): Promise<KpSummary[]> {
  if (inTauri()) return invoke<KpSummary[]>("attempts_summary");
  return lsSummary();
}

export async function todayStats(): Promise<TodayStats> {
  if (inTauri()) return invoke<TodayStats>("today_stats");
  const today = new Date();
  const date = today.toLocaleDateString("sv"); // YYYY-MM-DD
  const all = lsAttempts().filter((a) =>
    new Date(a.answered_at).toLocaleDateString("sv") === date,
  );
  return {
    date,
    answered: all.length,
    correct: all.filter((a) => a.correct).length,
  };
}

export async function loadSetting(key: string): Promise<string | null> {
  if (inTauri()) return invoke<string | null>("load_setting", { key });
  return localStorage.getItem(`${LS_KEY}-setting-${key}`);
}

export async function saveSetting(key: string, value: string): Promise<void> {
  if (inTauri()) {
    await invoke("save_setting", { key, value });
    return;
  }
  localStorage.setItem(`${LS_KEY}-setting-${key}`, value);
}

export interface SqlLabOutcome {
  columns: string[];
  rows: string[][];
  passed: boolean;
  detail: string;
}

/** SQL 实验：内存库执行 setup 后跑学习者查询与参考查询并比对。纯浏览器 dev 没有
 * SQLite 引擎,返回 null,界面提示改用应用运行(softcert ADR 0002)。 */
export async function runSqlLab(
  setup: string[],
  userSql: string,
  answerSql: string,
): Promise<SqlLabOutcome | null> {
  if (!inTauri()) return null;
  return invoke<SqlLabOutcome>("run_sql_lab", { setup, userSql, answerSql });
}
