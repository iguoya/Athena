import type { BayInfo, Snapshot } from "./types";

/** 进展记录里 actor 形如「zcode」或「zcode(代…)」，归属只认括号前的名字。 */
export function who(actor: string): string {
  return actor.split("(")[0].trim();
}

/** 智能体的行为分组。顺序即界面顺序：先决策类，再过程类，最后沟通类。 */
export const KINDS = [
  { id: "publish", label: "发布任务", tone: "bg-brand-700 text-white" },
  { id: "accept", label: "验收", tone: "bg-brand-700 text-white" },
  { id: "rework", label: "返工", tone: "bg-rose-100 text-rose-700" },
  { id: "block", label: "阻塞", tone: "bg-rose-100 text-rose-700" },
  { id: "start", label: "开工", tone: "bg-blue-100 text-blue-700" },
  { id: "deliver", label: "交付 review", tone: "bg-amber-100 text-amber-700" },
  { id: "finish", label: "直接完成", tone: "bg-brand-100 text-brand-700" },
  { id: "other", label: "其他流转", tone: "bg-ink-300/25 text-ink-700" },
  { id: "msg", label: "正式消息", tone: "bg-ink-300/25 text-ink-700" },
  { id: "chat", label: "即时消息", tone: "bg-ink-300/25 text-ink-700" },
] as const;

export type KindId = (typeof KINDS)[number]["id"];

export interface Action {
  kind: KindId;
  at: string; // 原始时间文本，用于展示
  sortKey: string; // 14 位数字，用于排序
  tid: string; // 关联任务，没有则空
  title: string; // 一行摘要
  detail: string; // 展开的全文
  to?: string;
}

export const stamp = (raw: string) => raw.replace(/\D/g, "").slice(0, 14).padEnd(14, "0");

/** 一次状态流转属于哪类行为。口径与 TaskView 的「验收 / 返工」判定一致。 */
export function classify(
  actor: string,
  from: string,
  to: string,
  note: string,
  leader: string,
): KindId {
  if (note.startsWith("返工：") || (from === "review" && to === "doing")) return "rework";
  if (from === "review" && to === "done" && who(actor) === leader) return "accept";
  if (to === "blocked") return "block";
  if (to === "done") return "finish";
  if (to === "review") return "deliver";
  if (to === "doing" && from === "todo") return "start";
  return "other";
}

/** 舱里出现过的所有成员：leader 在前，其后按配置，再补任务和消息里出现但配置没写的。 */
export function membersOf(snap: Snapshot, bay: string, info?: BayInfo): string[] {
  const names: string[] = [];
  const add = (n: string) => {
    const v = n.trim();
    if (v !== "" && v !== "all" && !names.includes(v)) names.push(v);
  };
  if (info) {
    add(info.leader);
    info.agents.forEach(add);
  }
  for (const t of snap.tasks) {
    if (t.bay !== bay) continue;
    add(t.owner);
    t.events.forEach((e) => add(who(e.actor)));
  }
  snap.msgs.filter((m) => m.bay === bay).forEach((m) => add(m.from_a));
  snap.chats.filter((c) => c.bay === bay).forEach((c) => add(c.sender));
  return names;
}

/** 按成员归集这个舱里的全部行为，每人内部按时间倒序（新的在前）。 */
export function actionsByMember(
  snap: Snapshot,
  bay: string,
  leader: string,
): Map<string, Action[]> {
  const out = new Map<string, Action[]>();
  const push = (name: string, a: Action) => {
    const list = out.get(name) ?? [];
    list.push(a);
    out.set(name, list);
  };
  for (const t of snap.tasks) {
    if (t.bay !== bay) continue;
    push(leader, {
      kind: "publish",
      at: t.created,
      sortKey: stamp(t.created),
      tid: t.tid,
      title: t.title,
      detail: "",
    });
    for (const e of t.events) {
      const kind = classify(e.actor, e.from_status, e.to_status, e.note, leader);
      push(who(e.actor), {
        kind,
        at: e.at,
        sortKey: stamp(e.at),
        tid: t.tid,
        title: `${e.from_status || "—"} → ${e.to_status}`,
        detail: e.note,
      });
    }
  }
  for (const m of snap.msgs) {
    if (m.bay !== bay) continue;
    push(m.from_a, {
      kind: "msg",
      at: m.created,
      sortKey: stamp(m.msg_id),
      tid: m.task,
      title: m.subject,
      detail: m.body.trim(),
      to: m.to_a,
    });
  }
  for (const c of snap.chats) {
    if (c.bay !== bay) continue;
    push(c.sender, {
      kind: "chat",
      at: c.ts.slice(5, 16),
      sortKey: stamp(c.ts),
      tid: "",
      title: c.text,
      detail: "",
      to: c.to_a,
    });
  }
  for (const list of out.values()) list.sort((a, b) => b.sortKey.localeCompare(a.sortKey));
  return out;
}

/**
 * 智能体配色：每个成员一种固定色，全界面同一个人同一种颜色。
 * 色相避开状态色（蓝 / 琥珀 / 玫红 / 青绿），免得「谁」和「什么状态」混淆。
 * Tailwind 要求类名是完整字面量，所以每档写全。
 */
export interface AgentColor {
  dot: string; // 实心色点 / 左边条
  chip: string; // 名字徽标：浅底深字
  soft: string; // 整块浅底（泳道标题、成员栏）
  border: string; // 卡片左边框
}

const PALETTE: AgentColor[] = [
  { dot: "bg-violet-500", chip: "bg-violet-100 text-violet-700", soft: "bg-violet-50", border: "border-l-violet-500" },
  { dot: "bg-orange-500", chip: "bg-orange-100 text-orange-700", soft: "bg-orange-50", border: "border-l-orange-500" },
  { dot: "bg-cyan-500", chip: "bg-cyan-100 text-cyan-700", soft: "bg-cyan-50", border: "border-l-cyan-500" },
  { dot: "bg-pink-500", chip: "bg-pink-100 text-pink-700", soft: "bg-pink-50", border: "border-l-pink-500" },
  { dot: "bg-lime-600", chip: "bg-lime-100 text-lime-800", soft: "bg-lime-50", border: "border-l-lime-600" },
  { dot: "bg-indigo-500", chip: "bg-indigo-100 text-indigo-700", soft: "bg-indigo-50", border: "border-l-indigo-500" },
  { dot: "bg-fuchsia-500", chip: "bg-fuchsia-100 text-fuchsia-700", soft: "bg-fuchsia-50", border: "border-l-fuchsia-500" },
  { dot: "bg-stone-500", chip: "bg-stone-200 text-stone-700", soft: "bg-stone-100", border: "border-l-stone-500" },
];

const FALLBACK = PALETTE[PALETTE.length - 1];

/** 按全部舱里首次出现的次序编号，成员不变则颜色不变，跨舱同名同色。 */
export function agentColors(snap: Snapshot): (name: string) => AgentColor {
  const order: string[] = [];
  const add = (n: string) => {
    const v = n.trim();
    if (v !== "" && v !== "all" && !order.includes(v)) order.push(v);
  };
  for (const b of snap.bays) {
    add(b.leader);
    b.agents.forEach(add);
  }
  for (const t of snap.tasks) {
    add(t.owner);
    t.events.forEach((e) => add(who(e.actor)));
  }
  snap.msgs.forEach((m) => add(m.from_a));
  snap.chats.forEach((c) => add(c.sender));
  return (name) => {
    const i = order.indexOf(name.trim());
    return i < 0 ? FALLBACK : PALETTE[i % PALETTE.length];
  };
}
