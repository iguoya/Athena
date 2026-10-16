import { useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { BayInfo, Snapshot } from "./types";
import BoardView from "./views/BoardView";
import TaskView from "./views/TaskView";
import ChatView from "./views/ChatView";
import StatsView from "./views/StatsView";

type View = "board" | "tasks" | "chat" | "stats";

const VIEW_LABEL: Record<View, string> = {
  board: "看板",
  tasks: "任务与决策",
  chat: "对话流",
  stats: "活动统计",
};

export default function App() {
  const [snap, setSnap] = useState<Snapshot | null>(null);
  const [bay, setBay] = useState<string>("");
  const [view, setView] = useState<View>("board");
  const [selectedTid, setSelectedTid] = useState<string>("");
  const [error, setError] = useState<string>("");

  if (snap === null && error === "") {
    invoke<Snapshot>("load_snapshot")
      .then((s) => {
        setSnap(s);
        if (s.bays.length > 0) setBay(s.bays[0].name);
      })
      .catch((e) => setError(String(e)));
  }

  const bayInfo: BayInfo | undefined = useMemo(
    () => snap?.bays.find((b) => b.name === bay),
    [snap, bay],
  );

  if (error !== "") {
    return (
      <div className="flex h-full items-center justify-center text-ink-500">
        加载失败：{error}
      </div>
    );
  }
  if (snap === null) {
    return <div className="flex h-full items-center justify-center text-ink-500">读取协作记录…</div>;
  }
  if (snap.source === "none") {
    return (
      <div className="flex h-full items-center justify-center px-10 text-center text-ink-500">
        {snap.note}
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* 左栏：舱列表 + 数据来源 */}
      <aside className="flex w-56 shrink-0 flex-col border-r border-line bg-white">
        <div className="px-4 pt-5 pb-3">
          <div className="text-lg font-bold tracking-wide">协作观察台</div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-ink-500">
            <span
              className={
                "inline-block h-2 w-2 rounded-full " +
                (snap.source === "pg" ? "bg-brand-500" : "bg-amber-400")
              }
              title={snap.note}
            />
            <span className="truncate" title={snap.note}>
              {snap.source === "pg" ? "中心库 · 多机汇聚" : "本地文件"}
            </span>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto px-2">
          {snap.bays.map((b) => (
            <button
              key={b.name}
              onClick={() => {
                setBay(b.name);
                setSelectedTid("");
              }}
              className={
                "mb-1 w-full rounded-lg px-3 py-2 text-left " +
                (b.name === bay ? "bg-brand-50 text-brand-700" : "text-ink-700 hover:bg-paper")
              }
            >
              <div className="font-medium">{b.name}</div>
              <div className="text-xs text-ink-500">
                leader {b.leader} · {b.agents.length} 方
              </div>
            </button>
          ))}
        </nav>
        <div className="border-t border-line px-4 py-3 text-xs text-ink-300">
          只读观察：写走 comms.py（ADR 0166）
        </div>
      </aside>

      {/* 主区 */}
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-4 border-b border-line bg-white px-6 py-3">
          <h1 className="text-base font-bold">{bay || "—"}</h1>
          {bayInfo && (
            <span className="text-xs text-ink-500">
              leader：{bayInfo.leader} · 成员：{bayInfo.agents.join("、")}
            </span>
          )}
          <nav className="ml-auto flex gap-1">
            {(Object.keys(VIEW_LABEL) as View[]).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={
                  "rounded-lg px-3 py-1.5 text-sm " +
                  (view === v ? "bg-brand-500 text-white" : "text-ink-700 hover:bg-brand-50")
                }
              >
                {VIEW_LABEL[v]}
              </button>
            ))}
          </nav>
        </header>
        <section className="min-h-0 flex-1 overflow-auto">
          {bay === "" ? (
            <div className="flex h-full items-center justify-center text-ink-500">选一个舱</div>
          ) : view === "board" ? (
            <BoardView
              snap={snap}
              bay={bay}
              onOpenTask={(tid) => {
                setSelectedTid(tid);
                setView("tasks");
              }}
            />
          ) : view === "tasks" ? (
            <TaskView
              snap={snap}
              bay={bay}
              selectedTid={selectedTid}
              onSelect={setSelectedTid}
            />
          ) : view === "chat" ? (
            <ChatView snap={snap} bay={bay} bayInfo={bayInfo} />
          ) : (
            <StatsView snap={snap} bay={bay} />
          )}
        </section>
      </main>
    </div>
  );
}
