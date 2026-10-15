import { useMemo } from "react";
import type { Snapshot } from "../types";

// 活动统计：按日统计消息与任务流转事件，自绘 SVG 条形图（不引图表库）。
export default function StatsView({ snap, bay }: { snap: Snapshot; bay: string }) {
  const data = useMemo(() => {
    const perDay = new Map<string, { msgs: number; events: number; chats: number }>();
    const bump = (date: string, k: "msgs" | "events" | "chats") => {
      const d = normalizeDate(date);
      if (!d) return;
      const row = perDay.get(d) ?? { msgs: 0, events: 0, chats: 0 };
      row[k] += 1;
      perDay.set(d, row);
    };
    for (const m of snap.msgs) if (m.bay === bay) bump(m.created, "msgs");
    for (const c of snap.chats) if (c.bay === bay) bump(c.ts, "chats");
    for (const t of snap.tasks)
      if (t.bay === bay) for (const ev of t.events) bump(ev.at, "events");
    const days = [...perDay.keys()].sort();
    return days.slice(-21).map((d) => ({ day: d, ...perDay.get(d)! }));
  }, [snap, bay]);

  const max = Math.max(1, ...data.map((d) => d.msgs + d.events + d.chats));
  const totals = data.reduce(
    (a, d) => ({ msgs: a.msgs + d.msgs, events: a.events + d.events, chats: a.chats + d.chats }),
    { msgs: 0, events: 0, chats: 0 },
  );

  if (data.length === 0) {
    return <div className="flex h-full items-center justify-center text-ink-500">这个舱还没有活动</div>;
  }

  const W = 900;
  const H = 220;
  const bw = W / data.length;
  const bar = (n: number) => (n / max) * (H - 40);

  return (
    <div className="p-6">
      <div className="mb-4 flex gap-6 text-sm text-ink-500">
        <span>
          正式消息 <b className="text-ink-900">{totals.msgs}</b>
        </span>
        <span>
          即时消息 <b className="text-ink-900">{totals.chats}</b>
        </span>
        <span>
          任务流转 <b className="text-ink-900">{totals.events}</b>
        </span>
        <span className="ml-auto text-xs">最近 {data.length} 个有活动的日子</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full rounded-xl bg-white ring-1 ring-line">
        {data.map((d, i) => {
          const x = i * bw + bw * 0.18;
          const w = bw * 0.64;
          const hm = bar(d.msgs);
          const he = bar(d.events);
          const hc = bar(d.chats);
          return (
            <g key={d.day}>
              <rect x={x} y={H - 20 - hc} width={w} height={hc} fill="#9ab0aa" rx="2" />
              <rect x={x} y={H - 20 - hc - he} width={w} height={he} fill="#35b39a" rx="2" />
              <rect x={x} y={H - 20 - hc - he - hm} width={w} height={hm} fill="#0f7b6c" rx="2" />
              <text x={x + w / 2} y={H - 6} textAnchor="middle" fontSize="10" fill="#5c716c">
                {d.day.slice(5)}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="mt-3 flex gap-4 text-xs text-ink-500">
        <Legend color="#0f7b6c" label="正式消息" />
        <Legend color="#35b39a" label="任务流转" />
        <Legend color="#9ab0aa" label="即时消息" />
      </div>
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="inline-block h-2.5 w-2.5 rounded" style={{ background: color }} />
      {label}
    </span>
  );
}

/// 「2026-10-15 18:28」/「2026-10-15T18:28:47」→「2026-10-15」
function normalizeDate(s: string): string | null {
  const m = s.match(/^(\d{4}-\d{2}-\d{2})/);
  return m ? m[1] : null;
}
