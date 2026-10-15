// 与 Rust 侧 Snapshot 结构一一对应（lib.rs）。

export interface BayInfo {
  name: string;
  leader: string;
  agents: string[];
}

export interface TaskEvent {
  at: string;
  actor: string;
  from_status: string;
  to_status: string;
  note: string;
}

export interface TaskRow {
  bay: string;
  tid: string;
  title: string;
  owner: string;
  status: string;
  priority: string;
  depends: string;
  created: string;
  updated: string;
  body: string;
  events: TaskEvent[];
}

export interface MsgRow {
  bay: string;
  msg_id: string;
  from_a: string;
  to_a: string;
  subject: string;
  created: string;
  thread: string;
  task: string;
  body: string;
}

export interface ChatRow {
  bay: string;
  ts: string;
  sender: string;
  to_a: string;
  text: string;
  seq: number;
}

export interface Snapshot {
  source: "pg" | "files" | "none";
  note: string;
  bays: BayInfo[];
  tasks: TaskRow[];
  msgs: MsgRow[];
  chats: ChatRow[];
}

export const STATUSES = ["todo", "doing", "review", "blocked", "done"] as const;

export const STATUS_COLOR: Record<string, string> = {
  todo: "bg-ink-300",
  doing: "bg-blue-500",
  review: "bg-amber-500",
  blocked: "bg-rose-500",
  done: "bg-brand-500",
};

export const STATUS_TEXT: Record<string, string> = {
  todo: "text-ink-700",
  doing: "text-blue-600",
  review: "text-amber-600",
  blocked: "text-rose-600",
  done: "text-brand-600",
};

export const PRIORITY_COLOR: Record<string, string> = {
  P0: "bg-rose-100 text-rose-700",
  P1: "bg-amber-100 text-amber-700",
  P2: "bg-ink-300/30 text-ink-700",
};
