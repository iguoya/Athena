import { useMemo, useState } from "react";
import type { Snapshot } from "../types";
import { PRIORITY_COLOR, STATUS_TEXT } from "../types";

// 任务与决策：左列任务清单，右侧任务书 + 流转时间线 + 关联消息（裁决/返工/验收）。
export default function TaskView({ snap, bay }: { snap: Snapshot; bay: string }) {
  const bayInfo = snap.bays.find((b) => b.name === bay);
  const tasks = useMemo(
    () =>
      snap.tasks
        .filter((t) => t.bay === bay)
        .sort((a, b) => a.tid.localeCompare(b.tid)),
    [snap, bay],
  );
  const [tid, setTid] = useState<string>("");
  const task = tasks.find((t) => t.tid === (tid || tasks[0]?.tid));
  const relatedMsgs = useMemo(
    () => snap.msgs.filter((m) => m.bay === bay && !!task && m.task === task.tid),
    [snap, bay, task],
  );

  if (!task) {
    return <div className="flex h-full items-center justify-center text-ink-500">这个舱还没有任务</div>;
  }

  return (
    <div className="flex h-full">
      <div className="w-72 shrink-0 overflow-y-auto border-r border-line bg-white p-3">
        {tasks.map((t) => (
          <button
            key={t.tid}
            onClick={() => setTid(t.tid)}
            className={
              "mb-1 block w-full rounded-lg px-3 py-2 text-left " +
              (t.tid === task.tid ? "bg-brand-50" : "hover:bg-paper")
            }
          >
            <div className="flex items-center gap-2">
              <span className={"rounded px-1.5 py-0.5 text-xs " + (PRIORITY_COLOR[t.priority] ?? "")}>
                {t.priority}
              </span>
              <span className="font-mono text-xs text-ink-500">{t.tid}</span>
              <span className={"ml-auto text-xs font-medium " + (STATUS_TEXT[t.status] ?? "")}>
                {t.status}
              </span>
            </div>
            <div className="mt-1 line-clamp-1 text-sm">{t.title}</div>
          </button>
        ))}
      </div>

      <div className="min-w-0 flex-1 overflow-y-auto p-6">
        <div className="flex items-baseline gap-3">
          <h2 className="text-lg font-bold">
            {task.tid} · {task.title}
          </h2>
          <span className={"text-sm font-medium " + (STATUS_TEXT[task.status] ?? "")}>
            {task.status}
          </span>
        </div>
        <div className="mt-1 text-sm text-ink-500">
          负责人 {task.owner}
          {task.depends.trim() !== "" && ` · 依赖 ${task.depends}`}
          {` · 创建 ${task.created} · 更新 ${task.updated}`}
        </div>

        {/* 任务书 */}
        <div className="mt-5 rounded-xl border border-line bg-white p-5">
          <div className="mb-2 text-xs font-semibold tracking-wider text-ink-300">任务书</div>
          <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-ink-700">
            {task.body.trim()}
          </pre>
        </div>

        {/* 流转时间线 */}
        <div className="mt-5">
          <div className="mb-2 text-xs font-semibold tracking-wider text-ink-300">流转时间线</div>
          <ol className="relative ml-2 border-l-2 border-line pl-5">
            {task.events.length === 0 && (
              <li className="text-sm text-ink-300">还没有流转记录</li>
            )}
            {task.events.map((ev, i) => (
              <li key={i} className="relative pb-4">
                <span
                  className={
                    "absolute -left-[27px] top-1 h-3 w-3 rounded-full border-2 border-white " +
                    (ev.to_status === "done"
                      ? "bg-brand-500"
                      : ev.to_status === "review"
                        ? "bg-amber-500"
                        : ev.to_status === "blocked"
                          ? "bg-rose-500"
                          : "bg-blue-500")
                  }
                />
                <div className="text-sm">
                  <span className="font-medium">{ev.actor}</span>
                  <span className="text-ink-500">
                    {" "}
                    {ev.from_status || "—"} → <b>{ev.to_status}</b>
                  </span>
                  <span className="ml-2 text-xs text-ink-300">{ev.at}</span>
                </div>
                {ev.note !== "" && (
                  <div className="mt-1 whitespace-pre-wrap rounded-lg bg-white px-3 py-2 text-sm text-ink-700 ring-1 ring-line">
                    {ev.note}
                  </div>
                )}
              </li>
            ))}
          </ol>
        </div>

        {/* 关联消息（决策记录） */}
        <div className="mt-5">
          <div className="mb-2 text-xs font-semibold tracking-wider text-ink-300">
            关联消息（{relatedMsgs.length} 条）
          </div>
          {relatedMsgs.length === 0 && <div className="text-sm text-ink-300">没有关联消息</div>}
          {relatedMsgs
            .slice()
            .sort((a, b) => a.msg_id.localeCompare(b.msg_id))
            .map((m) => (
              <div key={m.msg_id} className="mb-3 rounded-xl border border-line bg-white p-4">
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span
                    className={
                      "rounded px-1.5 py-0.5 text-xs font-medium " +
                      (m.from_a === bayInfo?.leader
                        ? "bg-brand-100 text-brand-700"
                        : "bg-ink-300/25 text-ink-700")
                    }
                  >
                    {m.from_a}
                    {m.from_a === bayInfo?.leader ? " · leader" : ""}
                  </span>
                  <span className="font-medium">{m.subject}</span>
                  <span className="ml-auto text-xs text-ink-300">{m.created}</span>
                </div>
                <pre className="mt-2 whitespace-pre-wrap font-sans text-sm leading-relaxed text-ink-700">
                  {m.body.trim()}
                </pre>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
