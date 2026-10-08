import type { ReactNode } from "react";

export function VizShell({ title, children, controls }: { title: string; children: ReactNode; controls?: ReactNode }) {
  return (
    <div className="p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <span className="text-sm font-bold text-brand-800">{title}</span>
        <div className="flex flex-wrap items-center gap-3 text-[13px]">{controls}</div>
      </div>
      {children}
    </div>
  );
}

export function Slider({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="flex items-center gap-2">
      <span className="text-ink/60">{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-1.5 w-32 cursor-pointer appearance-none rounded-full bg-brand-100 accent-brand-500"
      />
      <span className="w-8 text-right font-mono font-semibold text-brand-700">{value}</span>
    </label>
  );
}

export function SegButton({
  active,
  children,
  onClick,
  color = "#6D5AE6",
}: {
  active: boolean;
  children: ReactNode;
  onClick: () => void;
  color?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-full border px-3 py-1 text-[12.5px] font-medium transition-colors"
      style={
        active
          ? { background: color, borderColor: color, color: "#fff" }
          : { borderColor: "rgba(0,0,0,0.1)", color: "rgba(30,27,46,0.65)" }
      }
    >
      {children}
    </button>
  );
}
