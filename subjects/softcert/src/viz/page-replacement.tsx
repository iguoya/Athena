import { useMemo, useState } from "react";
import { VizShell, Slider, SegButton } from "./common";

type Algo = "fifo" | "lru";
const DEFAULT_SEQ = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5];

interface FrameState {
  pages: (number | null)[][];
  hits: (boolean | null)[];
}

/** 逐页模拟,返回每一步的页框快照与命中标记。 */
function simulate(seq: number[], frames: number, algo: Algo): FrameState {
  const mem: number[] = [];
  const lastUsed = new Map<number, number>();
  const fifoOrder: number[] = [];
  const pages: (number | null)[][] = [];
  const hits: (boolean | null)[] = [];
  for (let i = 0; i < seq.length; i++) {
    const p = seq[i];
    let hit = mem.includes(p);
    if (!hit) {
      if (mem.length < frames) {
        mem.push(p);
        if (algo === "fifo") fifoOrder.push(p);
      } else {
        let victim: number;
        if (algo === "fifo") {
          victim = fifoOrder.shift()!;
        } else {
          victim = mem.reduce((a, b) => ((lastUsed.get(a) ?? -1) <= (lastUsed.get(b) ?? -1) ? a : b));
          mem.splice(mem.indexOf(victim), 1);
        }
        mem[mem.indexOf(victim)] = p;
      }
    } else if (algo === "fifo") {
      // FIFO 命中不改变替换顺序
    }
    lastUsed.set(p, i);
    const snap: (number | null)[] = [...mem];
    while (snap.length < frames) snap.push(null);
    pages.push(snap);
    hits.push(hit);
  }
  return { pages, hits };
}

export function PageReplacement() {
  const [seqText, setSeqText] = useState(DEFAULT_SEQ.join(" "));
  const [frames, setFrames] = useState(3);
  const [algo, setAlgo] = useState<Algo>("fifo");
  const [cursor, setCursor] = useState(DEFAULT_SEQ.length);
  const seq = useMemo(
    () => seqText.split(/[\s,]+/).filter(Boolean).map(Number).filter((n) => !Number.isNaN(n)),
    [seqText],
  );
  const result = useMemo(() => simulate(seq, frames, algo), [seq, frames, algo]);
  const step = Math.max(0, Math.min(cursor, seq.length));
  const shown = result.pages.slice(0, step);
  const faults = result.hits.slice(0, step).filter((h) => h === false).length;
  const rate = step > 0 ? faults / step : 0;

  return (
    <VizShell
      title="页置换 · 数一数缺页"
      controls={
        <>
          <SegButton active={algo === "fifo"} onClick={() => setAlgo("fifo")}>FIFO</SegButton>
          <SegButton active={algo === "lru"} color="#0E8A6D" onClick={() => setAlgo("lru")}>LRU</SegButton>
          <Slider label="页框" value={frames} min={2} max={5} onChange={setFrames} />
        </>
      }
    >
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-[13px]">
          <span className="text-ink/60">访问序列</span>
          <input
            value={seqText}
            onChange={(e) => { setSeqText(e.target.value); setCursor(99); }}
            className="w-56 rounded-lg border border-black/10 bg-white px-2.5 py-1 font-mono text-[13px] outline-none focus:border-brand-400"
          />
        </label>
        <input type="range" min={0} max={seq.length} value={step}
          onChange={(e) => setCursor(Number(e.target.value))}
          className="h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-brand-100 accent-brand-500" />
        <span className="font-mono text-[12.5px] text-ink/60">{step}/{seq.length}</span>
      </div>
      <div className="mt-3 overflow-x-auto">
        <table className="border-separate border-spacing-0.5 text-[12.5px]">
          <tbody>
            <tr>
              <td className="pr-2 text-ink/45">访问</td>
              {seq.map((p, i) => (
                <td key={i} className={`h-7 w-8 rounded-t-md text-center font-mono font-bold ${i < step ? "bg-ink text-white" : "bg-black/5 text-ink/30"}`}>
                  {p}
                </td>
              ))}
            </tr>
            {Array.from({ length: frames }, (_, f) => (
              <tr key={f}>
                <td className="pr-2 text-ink/45">框{f + 1}</td>
                {shown.map((snapshot, i) => {
                  const page = snapshot[f];
                  const hit = result.hits[i];
                  const isNew = page !== null && (f === 0 || snapshot.slice(0, f).every((x) => x !== page));
                  const mark = hit === false && isNew;
                  return (
                    <td key={i} className={`h-7 w-8 text-center font-mono ${
                      page === null ? "bg-black/[0.03] text-transparent"
                      : mark ? "bg-rose-100 text-rose-600 font-bold"
                      : hit ? "bg-emerald-100 text-emerald-700" : "bg-brand-50 text-brand-700"
                    }`}>
                      {page ?? "·"}
                    </td>
                  );
                })}
              </tr>
            ))}
            <tr>
              <td className="pr-2 text-ink/45">结果</td>
              {result.hits.slice(0, step).map((h, i) => (
                <td key={i} className={`h-5 text-center text-[10px] font-bold ${h ? "text-emerald-600" : "text-rose-500"}`}>
                  {h ? "中" : "缺"}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-[13px]">
        <span className="rounded-lg bg-rose-50 px-3 py-1.5 text-rose-600">缺页 <b className="font-mono">{faults}</b> 次</span>
        <span className="rounded-lg bg-brand-50 px-3 py-1.5">缺页率 <b className="font-mono text-brand-700">{rate.toFixed(2)}</b></span>
        <span className="self-center text-[12px] text-ink/50">提示:FIFO 换成序列 1 2 3 4 1 2 5 1 2 3 4 5,页框 3→4 缺页反而变多——Belady 异常。</span>
      </div>
    </VizShell>
  );
}
