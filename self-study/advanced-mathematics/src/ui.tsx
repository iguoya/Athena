import type { SourceRef } from "./types";

/** 出处角标：真题绿、改编黄、自编灰。判分内容必带（exam 档，ADR 0043、0089）。 */
export function SourceBadge({ refs }: { refs: SourceRef[] }) {
  if (!refs || refs.length === 0) return null;
  return (
    <span className="source-badge">
      {refs.map((r, i) => (
        <span key={i} className={`source rel-${r.relation}`} title={r.note ?? ""}>
          {r.relation === "verbatim"
            ? `真题 ${r.locator ?? ""}`
            : r.relation === "adapted"
              ? `改编 ${r.locator ?? ""}${r.note ? `（${r.note}）` : ""}`
              : `自编${r.note ? `：${r.note}` : ""}`}
        </span>
      ))}
    </span>
  );
}
