import { useState } from "react";
import { VizShell, Slider } from "./common";

function to8(n: number): string {
  return ((n < 0 ? n + 256 : n) & 0xff).toString(2).padStart(8, "0");
}
function group(s: string): string {
  return s.slice(0, 4) + " " + s.slice(4);
}

export function ComplementExplorer() {
  const [x, setX] = useState(-47);
  const isNeg = x < 0;
  const yuan = isNeg
    ? "1" + Math.abs(x).toString(2).padStart(7, "0").slice(-7)
    : to8(x);
  const fan = isNeg
    ? "1" +
      yuan
        .slice(1)
        .split("")
        .map((b) => (b === "1" ? "0" : "1"))
        .join("")
    : yuan;
  const bu = to8(x);
  const rows = [
    { name: "原码", bits: group(yuan), note: "符号位 + 绝对值" },
    { name: "反码", bits: group(fan), note: isNeg ? "原码数值位按位取反" : "正数三码相同" },
    { name: "补码", bits: group(bu), note: isNeg ? "反码 + 1" : "正数三码相同" },
  ];
  return (
    <VizShell
      title="补码 · 三码怎么变"
      controls={<Slider label="真值" value={x} min={-128} max={127} onChange={setX} />}
    >
      <div className="space-y-2">
        {rows.map((r) => (
          <div key={r.name} className={`flex items-center gap-4 rounded-xl px-4 py-2.5 ${r.name === "补码" ? "bg-brand-50 ring-1 ring-brand-200" : "bg-black/[0.03]"}`}>
            <span className="w-12 text-sm font-bold text-ink/70">{r.name}</span>
            <span className={`font-mono text-lg font-bold tracking-[0.18em] ${r.name === "补码" ? "text-brand-700" : "text-ink/75"}`}>
              {r.bits}
            </span>
            <span className="ml-auto text-[12.5px] text-ink/50">{r.note}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-3 text-[12.5px]">
        <span className="rounded-full bg-rose-50 px-3 py-1 text-rose-600 ring-1 ring-rose-200">
          8 位补码范围 −128 ~ +127:{x === -128 && "—— 你正停在 −128,它没有原码/反码!"}
        </span>
        <span className="rounded-full bg-brand-50 px-3 py-1 text-brand-700 ring-1 ring-brand-200">
          补码 1000 0000 = −128,按「取反加一」推不出来,按公式 −2⁷ 直接记。
        </span>
      </div>
    </VizShell>
  );
}
