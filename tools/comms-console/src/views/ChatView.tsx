import { useMemo, useState, type ReactNode } from "react";
import type { Snapshot } from "../types";
import { dayHeading, dayKey, stampOf } from "../timeline";
import type { AgentColor } from "../activity";

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

function noisy(subject: string | undefined): boolean {
  return !!subject && (subject.startsWith("FYI") || subject.startsWith("联络"));
}

// 对话流：正式消息与即时 chat 按秒合并，线程折叠，按日分组。
export default function ChatView({
  snap,
  bay,
  bayInfo,
  colorOf,
}: {
  snap: Snapshot;
  bay: string;
  bayInfo?: { leader: string; agents: string[] };
  colorOf: (name: string) => AgentColor;
}) {
  const leader = bayInfo?.leader ?? "";
  const [openNoise, setOpenNoise] = useState<Record<string, boolean>>({});

  const groups = useMemo(() => {
    const msgs: Entry[] = snap.msgs
      .filter((m) => m.bay === bay)
      .map((m) => ({
        key: m.msg_id,
        at: m.created,
        sortKey: stampOf(m.msg_id),
        from: m.from_a,
        channel: "msg" as const,
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
        sortKey: stampOf(c.ts),
        from: c.sender,
        channel: "chat" as const,
        to: c.to_a,
        body: c.text,
      }));
    const entries = [...msgs, ...chats].sort((a, b) => {
      const byTime = a.sortKey.localeCompare(b.sortKey);
      if (byTime !== 0) return byTime;
      if (a.channel !== b.channel) return a.channel === "msg" ? -1 : 1;
      return a.key.localeCompare(b.key);
    });

    const buckets = new Map<string, Entry[]>();
    const order: string[] = [];
    for (const e of entries) {
      const id = e.channel === "msg" ? e.thread || e.key : e.key;
      if (!buckets.has(id)) {
        buckets.set(id, []);
        order.push(id);
      }
      buckets.get(id)!.push(e);
    }
    return order.map((id) => {
      const items = buckets.get(id)!;
      if (items[0].channel !== "msg") return { root: items[0], replies: [] as Entry[] };
      const root = items.find((e) => e.key === id) ?? items[0];
      return { root, replies: items.filter((e) => e !== root) };
    });
  }, [snap, bay]);

  const badge = (from: string) => colorOf(from).chip;

  const nodes: ReactNode[] = [];
  let lastDay = "";
  for (const { root, replies } of groups) {
    const day = dayKey(root.sortKey);
    if (day !== lastDay) {
      lastDay = day;
      nodes.push(
        <div key={`day-${day}`} className="mb-3 mt-6 text-center text-xs font-medium text-ink-500 first:mt-0">
          {dayHeading(root.sortKey)}
        </div>,
      );
    }
    const folded = noisy(root.subject) && !openNoise[root.key];
    nodes.push(
      <div key={root.key} className="mb-4">
        <div className={"rounded-xl border border-l-4 border-line bg-white p-4 " + colorOf(root.from).border}>
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
            {noisy(root.subject) && (
              <button
                className="text-xs text-brand-700"
                onClick={() => setOpenNoise((s) => ({ ...s, [root.key]: !s[root.key] }))}
              >
                {folded ? "展开" : "收起"}
              </button>
            )}
          </div>
          {!folded && (
            <pre className="mt-2 whitespace-pre-wrap font-sans text-sm leading-relaxed text-ink-700">
              {root.body}
            </pre>
          )}
        </div>
        {!folded && replies.length > 0 && (
          <div className="ml-6 border-l-2 border-line pl-4 pt-2">
            {replies.map((r) => (
              <div key={r.key} className={"mb-2 rounded-xl border-l-4 bg-white p-3 ring-1 ring-line " + colorOf(r.from).border}>
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
      </div>,
    );
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      {groups.length === 0 && (
        <div className="flex h-40 items-center justify-center text-ink-500">这个舱还没有消息</div>
      )}
      {nodes}
    </div>
  );
}
