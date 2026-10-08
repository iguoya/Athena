import { useReducer } from "react";
import { VizShell, SegButton } from "./common";

const N = 4; // 缓冲区容量

interface State {
  buf: number;
  mutex: number;
  empty: number;
  full: number;
  log: string[];
  running: "none" | "producer" | "consumer";
}

const init: State = { buf: 0, mutex: 1, empty: N, full: 0, log: ["初始:empty=n、full=0、mutex=1"], running: "none" };

type Action = { kind: "produce" } | { kind: "consume" };

function step(s: State, a: Action): State {
  const log = [...s.log];
  const fail = (msg: string): State => {
    log.push(`✗ ${msg}`);
    return { ...s, log: log.slice(-6), running: "none" };
  };
  if (a.kind === "produce") {
    if (s.empty <= 0) return fail("生产者 P(empty) 失败:缓冲区已满,阻塞");
    let { empty, mutex, full, buf } = s;
    log.push("生产者 P(empty) → empty−1");
    empty -= 1;
    if (mutex <= 0) return fail("生产者 P(mutex) 失败:另一人正在操作,阻塞(演示从简,未挂起)");
    log.push("生产者 P(mutex) → mutex−1,进入缓冲区");
    mutex -= 1;
    buf += 1;
    log.push("放入一件产品 → V(mutex) → V(full)");
    mutex += 1;
    full += 1;
    return { buf, mutex, empty, full, log: log.slice(-6), running: "producer" };
  }
  if (s.full <= 0) return fail("消费者 P(full) 失败:缓冲区空,阻塞");
  let { empty, mutex, full, buf } = s;
  log.push("消费者 P(full) → full−1");
  full -= 1;
  if (mutex <= 0) return fail("消费者 P(mutex) 失败:另一人正在操作,阻塞(演示从简)");
  log.push("消费者 P(mutex) → mutex−1,进入缓冲区");
  mutex -= 1;
  buf -= 1;
  log.push("取走一件产品 → V(mutex) → V(empty)");
  mutex += 1;
  empty += 1;
  return { buf, mutex, empty, full, log: log.slice(-6), running: "consumer" };
}

export function SemaphoreAnim() {
  const [s, dispatch] = useReducer(step, init);
  return (
    <VizShell
      title="生产者–消费者 · PV 操作逐步走"
      controls={
        <>
          <SegButton active={s.running === "producer"} color="#6D5AE6" onClick={() => dispatch({ kind: "produce" })}>
            生产者放一件
          </SegButton>
          <SegButton active={s.running === "consumer"} color="#0E8A6D" onClick={() => dispatch({ kind: "consume" })}>
            消费者取一件
          </SegButton>
        </>
      }
    >
      <div className="flex flex-wrap items-center gap-6">
        <div className="flex gap-1.5">
          {Array.from({ length: N }, (_, i) => (
            <div
              key={i}
              className={`flex h-12 w-10 items-center justify-center rounded-lg border-2 text-lg font-bold transition-all ${
                i < s.buf
                  ? "border-brand-400 bg-brand-500 text-white shadow-md"
                  : "border-dashed border-black/15 bg-black/[0.02] text-transparent"
              }`}
            >
              ●
            </div>
          ))}
          <div className="ml-1 self-center text-[12px] text-ink/50">缓冲区 {s.buf}/{N}</div>
        </div>
        <div className="flex gap-2">
          {[
            { label: "empty", v: s.empty, cls: "bg-violet-100 text-violet-700" },
            { label: "full", v: s.full, cls: "bg-emerald-100 text-emerald-700" },
            { label: "mutex", v: s.mutex, cls: "bg-amber-100 text-amber-700" },
          ].map((x) => (
            <div key={x.label} className={`rounded-xl px-3.5 py-2 text-center ${x.cls}`}>
              <div className="text-[10.5px] font-semibold opacity-70">{x.label}</div>
              <div className="font-mono text-xl font-bold">{x.v}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="mt-4 h-[104px] overflow-y-auto rounded-xl bg-ink/95 p-3 font-mono text-[12px] leading-6 text-[#d9f0e4]">
        {s.log.map((l, i) => (
          <div key={i} className={l.startsWith("✗") ? "text-rose-300" : ""}>{l}</div>
        ))}
      </div>
    </VizShell>
  );
}
