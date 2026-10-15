import { useMemo } from "react";
import type { Snapshot } from "../types";

interface Entry {
  key: string;
  at: string;
  sortKey: string;
  from: string;
  channel: "msg" | "chat";
  subject?: string;
  to?: string;
  thread?: string;
  task?: string;
  body: string;
}

// 对话流：正式消息与即时 chat 合并的统一时间线，线程折叠（同 thread 收进一张卡）。
export default function ChatView({
  snap,
  bay,
  bayInfo,
}: {
  snap: Snapshot;
  bay: string;
  bayInfo?: { leader: string; agents: string[] };
}) {
  const leader = bayInfo?.leader ?? "";

  const entries = useMemo<Entry[]>(() => {
    const msgs: Entry[] = snap.msgs
      .filter((m) => m.bay === bay)
      .map((m) => ({
        key: m.msg_id,
        at: m.created,
        sortKey: m.msg_id, // 文件名时间戳 20261015-182847，可排序
        from: m.from_a,
        channel: "msg",
        subject: m.subject,
        thread: m.thread || m.msg_id,
        task: m.task,
        body: m.body.trim(),
      }));
    const chats: Entry[] = snap.chats
      .filter((c) => c.bay === bay)
      .map((c) => ({
        key: `chat-${c.sender}-${c.seq}`,
        at: c.ts.slice(5, 16),
        sortKey: c.ts,
        from: c.sender,
        channel: "chat",
        to: c.to_a,
        body: c.text,
      }));
    return [...msgs, ...chats].sort((a, b) => a.sortKey.localeCompare(b.sortKey));
  }, [snap, bay]);

  // 线程分组：正式消息按 thread 聚合；即时消息各自独立。
  const groups = useMemo(() => {
    const out: { root: Entry; replies: Entry[] }[] = [];
    const byThread = new Map<string, { root: Entry; replies: Entry[] }>();
    for (const e of entries) {
      if (e.channel === "msg" && e.thread) {
        const g = byThread.get(e.thread);
        if (g) {
          g.replies.push(e);
        } else {
          const ng = { root: e, replies: [] };
          byThread.set(e.thread, ng);
          out.push(ng);
        }
      } else {
        out.push({ root: e, replies: [] });
      }
    }
    return out;
  }, [entries]);

  const badge = (from: string) =>
    from === leader
      ? "bg-brand-100 text-brand-700"
      : "bg-ink-300/25 text-ink-700";

  return (
    <div className="mx-auto max-w-4xl p-6">
      {groups.length === 0 && (
        <div className="flex h-40 items-center justify-center text-ink-500">这个舱还没有消息</div>
      )}
      {groups.map(({ root, replies }) => (
        <div key={root.key} className="mb-4">
          <div className="rounded-xl border border-line bg-white p-4">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className={"rounded px-1.5 py-0.5 text-xs font-medium " + badge(root.from)}>
                {root.from}
                {root.from === leader ? " · leader" : ""}
              </span>
              {root.channel === "msg" ? (
                <span className="font-medium">{root.subject}</span>
              ) : (
                <span className="text-xs text-ink-300">即时</span>
              )}
              {root.to && root.to !== "all" && <span className="text-xs text-ink-300">→ {root.to}</span>}
              {root.task && (
                <span className="rounded bg-brand-50 px-1.5 py-0.5 font-mono text-xs text-brand-700">
                  {root.task}
                </span>
              )}
              <span className="ml-auto text-xs text-ink-300">{root.at}</span>
            </div>
            <pre className="mt-2 whitespace-pre-wrap font-sans text-sm leading-relaxed text-ink-700">
              {root.body}
            </pre>
          </div>
          {replies.length > 0 && (
            <div className="ml-6 border-l-2 border-line pl-4 pt-2">
              {replies.map((r) => (
                <div key={r.key} className="mb-2 rounded-xl bg-white p-3 ring-1 ring-line">
                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    <span className={"rounded px-1.5 py-0.5 text-xs font-medium " + badge(r.from)}>
                      {r.from}
                      {r.from === leader ? " · leader" : ""}
                    </span>
                    <span className="font-medium text-ink-700">{r.subject}</span>
                    <span className="ml-auto text-xs text-ink-300">{r.at}</span>
                  </div>
                  <pre className="mt-1.5 whitespace-pre-wrap font-sans text-sm leading-relaxed text-ink-700">
                    {r.body}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
