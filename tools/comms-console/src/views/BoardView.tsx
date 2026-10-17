import { useState } from "react";
import type { BayInfo, Snapshot } from "../types";
import { PRIORITY_COLOR, STATUSES, STATUS_TEXT } from "../types";
import { membersOf, type AgentColor } from "../activity";

// 看板：默认按负责人分泳道（行 = 智能体，列 = 状态），谁手上压着什么、谁交付了什么一眼分开；
// 也可切回平铺（一列一个状态，不分人）。卡片左边条用负责人的颜色。
export default function BoardView({
  snap,
  bay,
  bayInfo,
  colorOf,
  onOpenTask,
}: {
  snap: Snapshot;
  bay: string;
  bayInfo?: BayInfo;
  colorOf: (name: string) => AgentColor;
  onOpenTask: (tid: string) => void;
}) {
  const [lanes, setLanes] = useState(true);
  const tasks = snap.tasks.filter((t) => t.bay === bay);
  const doneIds = new Set(tasks.filter((t) => t.status === "done").map((t) => t.tid));
  const order = { P0: 0, P1: 1, P2: 2 } as Record<string, number>;
  const leader = bayInfo?.leader ?? "";

  const sorted = (list: typeof tasks) =>
    list
      .slice()
      .sort(
        (a, b) =>
          (order[a.priority] ?? 9) - (order[b.priority] ?? 9) || a.tid.localeCompare(b.tid),
      );

  const card = (t: (typeof tasks)[number]) => {
    const waiting = t.depends
      .split(",")
      .map((d) => d.trim())
      .filter((d) => d !== "" && !doneIds.has(d));
    return (
      <button
        key={t.tid}
        onClick={() => onOpenTask(t.tid)}
        className={
          "rounded-xl border border-l-4 border-line bg-white p-3 text-left shadow-sm transition hover:border-brand-300 " +
          colorOf(t.owner).border
        }
      >
        <div className="flex items-center gap-2">
          <span className={"rounded px-1.5 py-0.5 text-xs font-medium " + (PRIORITY_COLOR[t.priority] ?? "")}>
            {t.priority}
          </span>
          <span className="font-mono text-xs text-ink-500">{t.tid}</span>
          <span className={"ml-auto rounded px-1.5 py-0.5 text-xs font-medium " + colorOf(t.owner).chip}>
            {t.owner}
          </span>
        </div>
        <div className="mt-1.5 line-clamp-2 text-sm leading-snug">{t.title}</div>
        {waiting.length > 0 && (
          <div className="mt-1.5 text-xs text-amber-600">等待 {waiting.join("、")}</div>
        )}
      </button>
    );
  };

  const toggle = (
    <div className="flex items-center gap-1 px-5 pt-4 text-sm">
      {[
        [true, "按成员分泳道"],
        [false, "平铺"],
      ].map(([v, label]) => (
        <button
          key={String(label)}
          onClick={() => setLanes(v as boolean)}
          className={
            "rounded-lg px-3 py-1 " +
            (lanes === v ? "bg-brand-500 text-white" : "text-ink-700 hover:bg-brand-50")
          }
        >
          {label as string}
        </button>
      ))}
    </div>
  );

  if (!lanes) {
    return (
      <div className="flex h-full flex-col">
        {toggle}
        <div className="flex min-h-0 flex-1 gap-4 overflow-x-auto p-5">
          {STATUSES.map((st) => {
            const cards = sorted(tasks.filter((t) => t.status === st));
            return (
              <div key={st} className="flex w-72 shrink-0 flex-col gap-2">
                <div className={"px-1 text-sm font-semibold " + (STATUS_TEXT[st] ?? "")}>
                  {st}
                  <span className="ml-1.5 text-ink-300">{cards.length}</span>
                </div>
                {cards.map(card)}
                {cards.length === 0 && <div className="px-1 text-xs text-ink-300">—</div>}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // 泳道只列「名下有任务」的成员；没有任务的成员（纯审阅者）在「成员」视图里看。
  const owners = membersOf(snap, bay, bayInfo).filter((n) => tasks.some((t) => t.owner === n));

  return (
    <div className="flex h-full flex-col">
      {toggle}
      <div className="min-h-0 flex-1 overflow-auto p-5">
        <div className="min-w-[1180px]">
          {/* 状态表头，滚动时钉在顶部 */}
          <div className="sticky top-0 z-10 grid grid-cols-[9rem_repeat(5,minmax(0,1fr))] gap-3 bg-paper pb-2">
            <div />
            {STATUSES.map((st) => (
              <div key={st} className={"px-1 text-sm font-semibold " + (STATUS_TEXT[st] ?? "")}>
                {st}
                <span className="ml-1.5 text-ink-300">
                  {tasks.filter((t) => t.status === st).length}
                </span>
              </div>
            ))}
          </div>
          {owners.map((name) => {
            const mine = tasks.filter((t) => t.owner === name);
            const c = colorOf(name);
            return (
              <div
                key={name}
                className="mb-3 grid grid-cols-[9rem_repeat(5,minmax(0,1fr))] gap-3 rounded-2xl border border-line bg-white/60 p-3"
              >
                <div className={"rounded-xl p-3 " + c.soft}>
                  <div className="flex items-center gap-2">
                    <span className={"inline-block h-2.5 w-2.5 rounded-full " + c.dot} />
                    <span className="font-semibold">{name}</span>
                  </div>
                  <div className="mt-0.5 text-xs text-ink-500">
                    {name === leader ? "leader" : "worker"} · {mine.length} 个任务
                  </div>
                </div>
                {STATUSES.map((st) => {
                  const cards = sorted(mine.filter((t) => t.status === st));
                  return (
                    <div key={st} className="flex flex-col gap-2">
                      {cards.map(card)}
                      {cards.length === 0 && <div className="px-1 text-xs text-ink-300">—</div>}
                    </div>
                  );
                })}
              </div>
            );
          })}
          {owners.length === 0 && (
            <div className="py-10 text-center text-ink-500">这个舱还没有任务</div>
          )}
        </div>
      </div>
    </div>
  );
}
