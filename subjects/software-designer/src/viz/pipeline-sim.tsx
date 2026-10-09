import { useState } from "react";
import { VizShell, Slider } from "./common";

const STAGE_COLORS = ["#6D5AE6", "#7C5FF0", "#8E66F5", "#A26BF7", "#B671F8", "#C878F5", "#D77FF0", "#E486EA"];

/** 5 段流水线时空图:k、n 可调;每格 = 一拍。 */
export function PipelineSim() {
  const [k, setK] = useState(5);
  const [n, setN] = useState(10);
  const dt = 1; // Δt 固定一拍,数值按拍数读
  const total = (k + n - 1) * dt;
  const serial = n * k * dt;
  const speedup = serial / total;
  const cell = 30;
  const width = Math.min(760, 80 + (k + n) * cell);
  const height = 46 + n * 26;

  return (
    <VizShell
      title="流水线时空图 · 加速比逼近段数"
      controls={
        <>
          <Slider label="段数 k" value={k} min={2} max={8} onChange={setK} />
          <Slider label="指令数 n" value={n} min={1} max={15} onChange={setN} />
        </>
      }
    >
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
        {/* 拍号 */}
        {Array.from({ length: k + n }, (_, t) => (
          <text key={t} x={80 + t * cell + cell / 2} y={18} textAnchor="middle" fontSize={11} fill="rgba(30,27,46,0.45)">
            {t + 1}
          </text>
        ))}
        {/* 指令行 */}
        {Array.from({ length: n }, (_, i) => (
          <g key={i}>
            <text x={44} y={40 + i * 26 + 16} textAnchor="middle" fontSize={11} fill="rgba(30,27,46,0.6)">
              I{i + 1}
            </text>
            {Array.from({ length: k }, (_, s) => {
              const t = i + s; // 指令 i 的段 s 在拍 t
              return (
                <rect
                  key={s}
                  x={80 + t * cell + 2}
                  y={40 + i * 26}
                  width={cell - 4}
                  height={20}
                  rx={4}
                  fill={STAGE_COLORS[s % STAGE_COLORS.length]}
                  opacity={0.25 + (0.75 * (s + 1)) / k}
                />
              );
            })}
          </g>
        ))}
      </svg>
      <div className="mt-3 grid gap-2 text-[13px] sm:grid-cols-3">
        <div className="rounded-xl bg-brand-50 px-4 py-2.5">
          总时间 <span className="font-mono font-bold text-brand-700">(k+n−1)Δt = {total}</span> 拍
        </div>
        <div className="rounded-xl bg-brand-50 px-4 py-2.5">
          吞吐率 <span className="font-mono font-bold text-brand-700">n/T = {(n / total).toFixed(2)}</span> /拍
        </div>
        <div className="rounded-xl bg-emerald-50 px-4 py-2.5">
          加速比 <span className="font-mono font-bold text-emerald-700">{speedup.toFixed(2)}</span>
          <span className="ml-1 text-[11px] text-emerald-600/70">(n→∞ 时趋近 k={k})</span>
        </div>
      </div>
    </VizShell>
  );
}
