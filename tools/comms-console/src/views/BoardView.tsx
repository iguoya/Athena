import type { Snapshot } from "../types";
import { PRIORITY_COLOR, STATUSES, STATUS_TEXT } from "../types";

// 看板泳道：一列一个状态，任务卡按优先级排序。依赖未完成的任务标出等待。
export default function BoardView({
  snap,
  bay,
  onOpenTask,
}: {
  snap: Snapshot;
  bay: string;
  onOpenTask: (tid: string) => void;
}) {
  const tasks = snap.tasks.filter((t) => t.bay === bay);
  const doneIds = new Set(tasks.filter((t) => t.status === "done").map((t) => t.tid));
  const order = { P0: 0, P1: 1, P2: 2 } as Record<string, number>;
  const rank = { todo: 0, doing: 1, blocked: 2, review: 3, done: 4 } as Record<string, number>;

  return (
    <div className="flex h-full gap-4 overflow-x-auto p-5">
      {STATUSES.map((st) => {
        const cards = tasks
          .filter((t) => t.status === st)
          .sort(
            (a, b) =>
              (order[a.priority] ?? 9) - (order[b.priority] ?? 9) || a.tid.localeCompare(b.tid),
          );
        return (
          <div key={st} className="flex w-72 shrink-0 flex-col gap-2">
            <div className={"px-1 text-sm font-semibold " + (STATUS_TEXT[st] ?? "")}>
              {st}
              <span className="ml-1.5 text-ink-300">{cards.length}</span>
            </div>
            {cards.map((t) => {
              const waiting = t.depends
                .split(",")
                .map((d) => d.trim())
                .filter((d) => d !== "" && !doneIds.has(d));
              return (
                <button
                  key={t.tid}
                  onClick={() => onOpenTask(t.tid)}
                  className="rounded-xl border border-line bg-white p-3 text-left shadow-sm transition hover:border-brand-300"
                >
                  <div className="flex items-center gap-2">
                    <span className={"rounded px-1.5 py-0.5 text-xs font-medium " + (PRIORITY_COLOR[t.priority] ?? "")}>
                      {t.priority}
                    </span>
                    <span className="font-mono text-xs text-ink-500">{t.tid}</span>
                    <span className="ml-auto text-xs text-ink-500">{t.owner}</span>
                  </div>
                  <div className="mt-1.5 line-clamp-2 text-sm leading-snug">{t.title}</div>
                  {waiting.length > 0 && (
                    <div className="mt-1.5 text-xs text-amber-600">等待 {waiting.join("、")}</div>
                  )}
                </button>
              );
            })}
            {cards.length === 0 && <div className="px-1 text-xs text-ink-300">—</div>}
          </div>
        );
      })}
      <div className="w-2 shrink-0" />
      {tasks.length === 0 && rank && null}
    </div>
  );
}
