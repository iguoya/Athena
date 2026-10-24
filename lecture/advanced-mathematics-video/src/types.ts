// 内容文件的类型：一节课 = 课堂脚本（content/lessons/<id>.json）；课树在 content/curriculum.json。
// 规则见 AGENTS.md 与 ADR 0185：进掌握度的任务只有 quick / workout（机器可核对），其余是教学动作，不判分。

/** 作答记录里 knowledge_id 的前缀（ADR 0185）：knowledge_id = 前缀 + 课节 id，如 advvideo.p006。 */
export const KID_PREFIX = "advvideo.";

export interface SourceRef {
  relation: "verbatim" | "adapted";
  /** 「P6 05:12」：分集号 + 视频里的时间 */
  locator: string;
  note?: string;
}

export type Check =
  | { kind: "numbers"; ask: string; answer: number[]; hint?: string }
  | { kind: "choice"; ask?: string; options: Array<{ text: string; ok?: boolean; why: string }>; hint?: string };

interface TaskBase {
  id: string;
  /** 暂停点：视频播放到这一秒自动暂停并弹出本任务；没有则由使用者在课堂区手动打开（时间戳待「边看边标」） */
  at?: number | null;
}

export type Task =
  /** 预测：机器可判的选择/数值，作答记录「预测是否命中」，但不进复习队列（教学动作，不是判分） */
  | (TaskBase & { kind: "predict"; prompt: string; check: Check; reveal: string })
  /** 自我解释：用一句话说为什么，再看参考。教学动作，不判分 */
  | (TaskBase & { kind: "selfexplain"; prompt: string; reference: string })
  /** 速答：机器核对，进掌握度 */
  | (TaskBase & { kind: "quick"; stem: string; check: Check; sol: string; source_refs: SourceRef[]; verify?: string })
  /** 先自己算：视频在讲师开始解题前暂停，使用者先动笔，把答案填回核对，进掌握度；verify 是 sympy 复算代码，只在 check.py 里执行 */
  | (TaskBase & { kind: "workout"; stem: string; check: Check; sol: string; source_refs: SourceRef[]; verify?: string });

export interface Beat {
  id: string;
  title: string;
  /** 本节拍讲的知识点短名；复习卡、交错练习、「待巩固」都按它聚合 */
  concept: string;
  /** 该节拍在视频里的起止秒；待标时为 null */
  start: number | null;
  end: number | null;
  tasks: Task[];
  /** 本节拍的一句话要点 */
  takeaway: string;
}

export interface Lesson {
  id: string;
  title: string;
  /** start/end：本课节在这一集里的区间（秒）；一集可以拆成几个课节（ADR 0185 决策 3） */
  video: { kind: "bilibili"; bvid: string; p: number; duration: number; outline: string; start?: number; end?: number };
  opening: { goal: string; predict?: Extract<Task, { kind: "predict" }> };
  beats: Beat[];
  closing: { exit: Task[]; note_prompt: string };
  /** 平台字幕或机器转写的文本底本（未校对），仅作索引与对照；公式细节以画面为准 */
  transcript?: { source: string; status: string; segments: Array<{ start: number; end: number; text: string }> };
}

export interface CurriculumItem {
  id: string;
  title: string;
}

export interface Curriculum {
  chapters: Array<{ id: string; title: string; items: CurriculumItem[] }>;
}

export interface AttemptRow {
  knowledge_id: string;
  item_id: string;
  correct: boolean;
  answered_at: number;
}

/** 播放桥上报（src-tauri/src/player_bridge.js → Rust → 本界面事件 player-status） */
export interface PlayerStatus {
  ev: string;
  t: number;
  paused: boolean;
  duration: number;
  note: string;
}
