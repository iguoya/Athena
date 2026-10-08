import { useMemo, useState } from "react";
import { VizShell, SegButton } from "./common";

interface Job {
  name: string;
  arrive: number;
  serve: number;
}
const JOBS: Job[] = [
  { name: "A", arrive: 0, serve: 4 },
  { name: "B", arrive: 1, serve: 2 },
  { name: "C", arrive: 2, serve: 6 },
  { name: "D", arrive: 3, serve: 3 },
];
type Algo = "fcfs" | "sjf" | "rr";
const ALGOS: { id: Algo; label: string }[] = [
  { id: "fcfs", label: "FCFS" },
  { id: "sjf", label: "SJF(非抢占)" },
  { id: "rr", label: "RR 片=1" },
];

const COLORS: Record<string, string> = { A: "#6D5AE6", B: "#0E8A6D", C: "#E0862F", D: "#C04FD1" };

/** 排甘特图:返回 {job, start, end} 片段序列。 */
function gantt(algo: Algo, jobs: Job[]): { name: string; start: number; end: number }[] {
  const segs: { name: string; start: number; end: number }[] = [];
  const remain = jobs.map((j) => ({ ...j, rest: j.serve }));
  const done: Job[] = [];
  let t = 0;
  if (algo === "rr") {
    const queue: typeof remain = [];
    const arrived = new Set<string>();
    while (done.length < jobs.length) {
      for (const j of remain) if (j.arrive <= t && !arrived.has(j.name) && j.rest > 0) { queue.push(j); arrived.add(j.name); }
      const cur = queue.shift();
      if (!cur) { t += 1; continue; }
      const run = Math.min(1, cur.rest);
      segs.push({ name: cur.name, start: t, end: t + run });
      cur.rest -= run;
      t += run;
      for (const j of remain) if (j.arrive <= t && !arrived.has(j.name) && j.rest > 0) { queue.push(j); arrived.add(j.name); }
      if (cur.rest > 0) queue.push(cur);
      else done.push(cur);
    }
    return segs;
  }
  while (done.length < jobs.length) {
    const ready = remain.filter((j) => j.arrive <= t && j.rest > 0);
    if (ready.length === 0) { t += 1; continue; }
    ready.sort((a, b) => (algo === "fcfs" ? a.arrive - b.arrive : a.serve - b.serve || a.arrive - b.arrive));
    const cur = ready[0];
    t += cur.rest;
    segs.push({ name: cur.name, start: t - cur.rest, end: t });
    cur.rest = 0;
    done.push(cur);
  }
  return segs;
}

export function ScheduleGantt() {
  const [algo, setAlgo] = useState<Algo>("fcfs");
  const segs = useMemo(() => gantt(algo, JOBS), [algo]);
  const finish = useMemo(() => {
    const f: Record<string, number> = {};
    for (const s of segs) f[s.name] = Math.max(f[s.name] ?? 0, s.end);
    return f;
  }, [segs]);
  const stats = JOBS.map((j) => {
    const turnaround = finish[j.name] - j.arrive;
    return { ...j, finish: finish[j.name], turnaround, weighted: turnaround / j.serve };
  });
  const avgT = stats.reduce((s, x) => s + x.turnaround, 0) / stats.length;
  const avgW = stats.reduce((s, x) => s + x.weighted, 0) / stats.length;
  const total = Math.max(...segs.map((s) => s.end));
  const cell = Math.min(46, 720 / (total + 2));

  return (
    <VizShell
      title="调度甘特图 · 同一批作业四种命运"
      controls={
        <>
          {ALGOS.map((a) => (
            <SegButton key={a.id} active={algo === a.id} onClick={() => setAlgo(a.id)}>
              {a.label}
            </SegButton>
          ))}
          <span className="ml-2 text-[11.5px] text-ink/45">A(0时达,4h)B(1,2)C(2,6)D(3,3)</span>
        </>
      }
    >
      <div className="overflow-x-auto pb-1">
        <svg viewBox={`0 0 ${total * cell + 20} 86`} className="min-w-[560px]">
          {segs.map((s, i) => (
            <g key={i}>
              <rect x={20 + s.start * cell} y={18} width={(s.end - s.start) * cell - 2} height={30} rx={6}
                fill={COLORS[s.name]} opacity={0.9} />
              <text x={20 + (s.start + (s.end - s.start) / 2) * cell} y={38} textAnchor="middle" fontSize={13} fontWeight="bold" fill="#fff">
                {s.name}
              </text>
            </g>
          ))}
          {Array.from({ length: total + 1 }, (_, t) => (
            <g key={t}>
              <line x1={20 + t * cell} y1={50} x2={20 + t * cell} y2={56} stroke="rgba(30,27,46,0.25)" />
              <text x={20 + t * cell} y={70} textAnchor="middle" fontSize={10.5} fill="rgba(30,27,46,0.5)">{t}</text>
            </g>
          ))}
        </svg>
      </div>
      <table className="mt-2 w-full max-w-[560px] text-left text-[12.5px]">
        <thead>
          <tr className="text-ink/50">
            <th className="py-1">作业</th><th>完成</th><th>周转</th><th>带权周转</th>
          </tr>
        </thead>
        <tbody>
          {stats.map((s) => (
            <tr key={s.name} className="border-t border-black/5">
              <td className="py-1.5 font-bold" style={{ color: COLORS[s.name] }}>{s.name}</td>
              <td className="font-mono">{s.finish}</td>
              <td className="font-mono">{s.turnaround}</td>
              <td className="font-mono">{s.weighted.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-2 flex gap-4 text-[13px]">
        <span className="rounded-lg bg-brand-50 px-3 py-1.5">平均周转 <b className="font-mono text-brand-700">{avgT.toFixed(2)}</b></span>
        <span className="rounded-lg bg-emerald-50 px-3 py-1.5">平均带权周转 <b className="font-mono text-emerald-700">{avgW.toFixed(2)}</b></span>
      </div>
    </VizShell>
  );
}
