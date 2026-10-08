import { useState } from "react";
import { VizShell, Slider } from "./common";

/** 按权展开:二进制各位与 2^i 的乘积列表。 */
function expansion(bits: string[]): string {
  const n = bits.length;
  const terms = bits
    .map((b, i) => (b === "1" ? `2^${n - 1 - i}` : null))
    .filter(Boolean) as string[];
  const value = parseInt(bits.join(""), 2);
  return `${terms.join(" + ") || "0"} = ${value}`;
}

export function BaseConverter() {
  const [value, setValue] = useState(173);
  const bin = value.toString(2).padStart(8, "0").slice(-8);
  return (
    <VizShell title="进制转换 · 按权展开看得见" controls={<Slider label="十进制" value={value} min={0} max={255} onChange={setValue} />}>
      <div className="grid gap-3 sm:grid-cols-4">
        {[
          { label: "二进制", text: bin, cls: "from-violet-500 to-violet-600" },
          { label: "八进制", text: value.toString(8), cls: "from-emerald-500 to-emerald-600" },
          { label: "十进制", text: String(value), cls: "from-brand-500 to-brand-600" },
          { label: "十六进制", text: value.toString(16).toUpperCase(), cls: "from-fuchsia-500 to-fuchsia-600" },
        ].map((c) => (
          <div key={c.label} className={`rounded-xl bg-gradient-to-br ${c.cls} p-3 text-center text-white shadow-lg`}>
            <div className="text-[11px] opacity-80">{c.label}</div>
            <div className="font-mono text-xl font-bold tracking-wide">{c.text}</div>
          </div>
        ))}
      </div>
      <div className="mt-4 rounded-xl bg-brand-50/70 px-4 py-3">
        <div className="mb-1 text-[12px] font-semibold text-brand-700">按权展开(十进制 → 二进制的逆过程)</div>
        <div className="font-mono text-[13px] text-ink/80">
          {bin.split("").map((b, i) => (
            <span key={i} className={`mx-0.5 inline-block rounded px-1 ${b === "1" ? "bg-brand-500/15 text-brand-700 font-bold" : "text-ink/30"}`}>
              {b}
            </span>
          ))}
          <span className="ml-3">{expansion(bin.split(""))}</span>
        </div>
      </div>
      <div className="mt-3 text-[12.5px] text-ink/50">
        顺手练:除基取余倒读 = 十进制转 R 进制;一位十六进制 = 四位二进制,分组即可。
      </div>
    </VizShell>
  );
}
