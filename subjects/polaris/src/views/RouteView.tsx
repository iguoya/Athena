import { useMemo, useState } from "react";
import { AnimatePresence } from "motion/react";
import { ChevronDown, ChevronLeft, Flag, Users } from "lucide-react";
import type { Catalog } from "@/content/catalog";
import { layoutRoute } from "@/content/routes";
import { GraphCanvas, type ColumnNote } from "@/graph/GraphCanvas";
import { EdgeCard } from "@/panels/EdgeCard";
import { NodeDrawer } from "@/panels/NodeDrawer";
import { useApp } from "@/state/store";
import { BALANCE_LABEL, LENS_LABEL, balanceVar } from "@/ui/labels";
import { useDrawerWidth } from "@/ui/useDrawerWidth";

export function RouteView({ catalog, routeId, nodeId }: { catalog: Catalog; routeId: string; nodeId?: string }) {
  const go = useApp((s) => s.go);
  const selectNode = useApp((s) => s.selectNode);
  const drawerWidth = useDrawerWidth();
  const [open, setOpen] = useState(true);

  const route = catalog.routes.find((r) => r.id === routeId);
  const layout = useMemo(() => (route ? layoutRoute(catalog, route) : null), [catalog, route]);
  const notes = useMemo(() => {
    const map = new Map<string, ColumnNote>();
    route?.stages.forEach((stage, index) => {
      map.set(`${route.id}#${index}`, { eyebrow: `第 ${index + 1} 阶段`, goal: stage.goal, checkpoint: stage.checkpoint });
    });
    return map;
  }, [route]);

  if (!route || !layout) {
    return (
      <div className="grid h-full place-items-center text-muted">
        <div className="text-center">
          <p>找不到这条路线。</p>
          <button type="button" className="mt-3 text-accent underline" onClick={() => go({ view: "home" })}>
            回到总览
          </button>
        </div>
      </div>
    );
  }

  const selected = nodeId ? catalog.nodeById.get(nodeId) : undefined;

  return (
    <div className="flex h-full flex-col">
      <div className="shrink-0 border-b border-line bg-surface px-6 py-3.5">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => go({ view: "home" })}
            className="flex items-center gap-0.5 text-[12.5px] text-muted transition-colors hover:text-ink"
          >
            <ChevronLeft size={15} /> 总览
          </button>
          <h1 className="text-[20px] font-bold tracking-tight">{route.title}</h1>
          <span className="rounded-full bg-surface-2 px-2.5 py-[3px] text-[11.5px] font-medium text-muted">{LENS_LABEL[route.lens]}</span>
          <span
            className="rounded-full px-2.5 py-[3px] text-[11.5px] font-medium"
            style={{ color: balanceVar(route.balance), background: `color-mix(in srgb, ${balanceVar(route.balance)} 13%, transparent)` }}
          >
            {BALANCE_LABEL[route.balance]}
          </span>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            className="ml-auto flex items-center gap-1 text-[12px] text-muted transition-colors hover:text-ink"
          >
            {open ? "收起说明" : "展开说明"}
            <ChevronDown size={14} className={`transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        </div>
        {open && (
          <div className="mt-2.5 grid grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1.1fr)] gap-5 text-[12.5px] leading-relaxed">
            <p className="text-muted">{route.summary}</p>
            <p className="flex gap-1.5 text-muted">
              <Users size={14} className="mt-0.5 shrink-0 text-faint" />
              <span>
                <span className="font-semibold text-ink">适合谁　</span>
                {route.audience}
              </span>
            </p>
            <p className="flex gap-1.5 rounded-lg bg-accent-soft/60 px-2.5 py-1.5">
              <Flag size={14} className="mt-0.5 shrink-0 text-gold" fill="currentColor" />
              <span>
                <span className="font-semibold">终点产物　</span>
                {route.artifact}
              </span>
            </p>
          </div>
        )}
      </div>

      <div className="relative min-h-0 flex-1">
        <GraphCanvas
          layout={layout}
          nodes={catalog.nodeById}
          selectedId={nodeId}
          fitKey={route.id}
          drawerInset={selected ? drawerWidth : 0}
          columnNotes={notes}
          edgeCard={(placed) => <EdgeCard catalog={catalog} placed={placed} />}
          onSelect={selectNode}
        />
        <AnimatePresence>
          {selected && (
            <NodeDrawer key={selected.id} catalog={catalog} node={selected} locked={false} width={drawerWidth} onClose={() => selectNode(null)} />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
