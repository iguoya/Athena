// operator（使用者本人）收件箱（ADR 0181）：聚合所有舱发给使用者的消息（--to operator）。
// 跨舱显示；「标为已处理」调 Rust 侧 operator_ack（执行 `comms.py ack operator`），
// 本视图自己不写任何 comms/ 文件——写走 CLI 的铁律不变。
import { useMemo } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { MsgRow } from "../types";

export default function InboxView({
  msgs,
  acked,
  onAcked,
}: {
  msgs: MsgRow[];
  acked: Set<string>;
  onAcked: (next: Set<string>) => void;
}) {
  const mine = useMemo(
    () =>
      msgs
        .filter((m) => m.to_a === "operator")
        .sort((a, b) => (a.created + a.msg_id < b.created + b.msg_id ? 1 : -1)),
    [msgs],
  );
  const byBay = useMemo(() => {
    const map = new Map<string, MsgRow[]>();
    for (const m of mine) {
      const list = map.get(m.bay) ?? [];
      list.push(m);
      map.set(m.bay, list);
    }
    return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [mine]);

  const key = (m: MsgRow) => `${m.bay}/${m.msg_id}`;
  const pending = mine.filter((m) => !acked.has(key(m)));

  async function ackBay(bay: string, rows: MsgRow[]) {
    try {
      await invoke("operator_ack", { bay });
      onAcked(new Set([...acked, ...rows.map(key)]));
    } catch (e) {
      alert(`标记失败：${e}`);
    }
  }

  if (mine.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-ink-500">
        <div>没有发给你的消息。</div>
        <div className="text-xs text-ink-300">
          代理向你求助时用 <code>send --to operator</code>，就会出现在这里并弹系统通知。
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-5">
      <div className="mb-4 flex items-baseline gap-3">
        <h2 className="text-base font-bold">需要你的消息</h2>
        <span className="text-xs text-ink-500">
          未处理 {pending.length} / 共 {mine.length} 条，跨 {byBay.length} 个舱
        </span>
      </div>
      {byBay.map(([bayName, rows]) => {
        const unackedRows = rows.filter((m) => !acked.has(key(m)));
        return (
          <section key={bayName} className="mb-6">
            <div className="mb-2 flex items-center gap-3">
              <h3 className="text-sm font-bold text-brand-700">{bayName}</h3>
              <span className="text-xs text-ink-500">{rows.length} 条</span>
              {unackedRows.length > 0 && (
                <button
                  onClick={() => ackBay(bayName, unackedRows)}
                  className="rounded-lg border border-line px-2.5 py-1 text-xs text-ink-700 hover:bg-brand-50"
                >
                  全部标为已处理（{unackedRows.length}）
                </button>
              )}
            </div>
            <div className="space-y-2">
              {rows.map((m) => {
                const done = acked.has(key(m));
                return (
                  <article
                    key={m.msg_id}
                    className={
                      "rounded-xl border bg-white p-4 " +
                      (done ? "border-line opacity-60" : "border-brand-200 shadow-sm")
                    }
                  >
                    <header className="mb-1 flex flex-wrap items-baseline gap-2">
                      <span className="text-sm font-bold">{m.subject}</span>
                      <span className={"text-xs font-medium " + (done ? "text-ink-300" : "text-brand-600")}>
                        {done ? "已处理" : "待处理"}
                      </span>
                      <span className="ml-auto text-xs text-ink-500">
                        {m.from_a} · {m.created}
                        {m.task ? ` · ${m.task}` : ""}
                      </span>
                    </header>
                    <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-ink-700">
                      {m.body.trim()}
                    </pre>
                  </article>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
