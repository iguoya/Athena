import { ExternalLink, X } from "lucide-react";
import type { Catalog } from "@/content/catalog";
import type { PlacedEdge } from "@/content/layout";
import { useApp } from "@/state/store";
import { openExternal } from "@/ui/external";
import { RELATION_LABEL } from "@/ui/labels";

interface Props {
  catalog: Catalog;
  placed: PlacedEdge;
}

/** 点开连线编号浮出的卡片：这条依赖为什么存在、凭什么成立（ADR 0002：每条边都要有出处）。 */
export function EdgeCard({ catalog, placed }: Props) {
  const setEdge = useApp((s) => s.setEdge);
  const { edge } = placed;
  const strong = edge.relation === "requires";
  const from = catalog.nodeById.get(edge.from)?.title ?? edge.from;
  const to = catalog.nodeById.get(edge.to)?.title ?? edge.to;
  return (
    <div className="rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-lift)]">
      <div className="flex items-start gap-2">
        <span className="grid size-6 shrink-0 place-items-center rounded-full bg-accent text-[11px] font-semibold text-accent-ink">{placed.number}</span>
        <div className="min-w-0 flex-1">
          <div className="text-[13px] font-semibold leading-snug">
            {from} <span className="text-faint">→</span> {to}
          </div>
          <span
            className={`mt-1 inline-block rounded-md px-1.5 py-[2px] text-[10.5px] font-semibold ${strong ? "bg-accent-soft text-accent" : "border border-dashed border-faint text-faint"}`}
          >
            {strong ? "强先修：没有它，这一课学不稳" : "虚线来路：帮助理解，但不是门槛"}
          </span>
        </div>
        <button type="button" aria-label="关闭" onClick={() => setEdge(null)} className="text-faint transition-colors hover:text-ink">
          <X size={16} />
        </button>
      </div>
      <p className="mt-3 text-[13px] leading-relaxed">{edge.rationale}</p>
      <ul className="mt-3 space-y-1.5 border-t border-line pt-3">
        {edge.evidence_refs.map((ref) => {
          const source = catalog.sources.get(ref.source_id);
          return (
            <li key={`${ref.source_id}-${ref.locator}`} className="flex items-start gap-1.5 text-[11.5px] leading-snug text-muted">
              <span className="shrink-0 rounded bg-surface-2 px-1 py-[1px] text-[10px] font-medium">{RELATION_LABEL[ref.relation] ?? ref.relation}</span>
              <span className="min-w-0 flex-1">
                {source?.title ?? ref.source_id} · {ref.locator}
              </span>
              {source && (
                <button type="button" aria-label="在浏览器里打开核对" title="在浏览器里打开核对" onClick={() => void openExternal(source.url)} className="shrink-0 text-faint hover:text-accent">
                  <ExternalLink size={13} />
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
