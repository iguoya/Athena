import { useMemo, useState } from "react";
import { AnimatePresence } from "motion/react";
import { BookOpen, ChevronDown } from "lucide-react";
import { STAGES, type Catalog } from "@/content/catalog";
import { layoutByStage } from "@/content/layout";
import { mapsByDiscipline } from "@/content/routes";
import { GraphCanvas, type ColumnNote } from "@/graph/GraphCanvas";
import { EdgeCard } from "@/panels/EdgeCard";
import { NodeDrawer } from "@/panels/NodeDrawer";
import { useApp } from "@/state/store";
import { DISCIPLINE_LABEL } from "@/ui/labels";
import { RateBar } from "@/ui/RatingParts";
import { useDrawerWidth } from "@/ui/useDrawerWidth";

export function BaseView({ catalog, mapId, nodeId }: { catalog: Catalog; mapId: string; nodeId?: string }) {
  const go = useApp((s) => s.go);
  const selectNode = useApp((s) => s.selectNode);
  const drawerWidth = useDrawerWidth();
  const [theoryOpen, setTheoryOpen] = useState(false);

  const map = catalog.maps.find((m) => m.id === mapId);
  const layout = useMemo(() => (map ? layoutByStage(map) : null), [map]);
  const notes = useMemo(() => {
    const result = new Map<string, ColumnNote>();
    STAGES.forEach((stage) => result.set(stage, { eyebrow: "这一阶段学" }));
    return result;
  }, []);

  if (!map || !layout) {
    return (
      <div className="grid h-full place-items-center text-muted">
        <div className="text-center">
          <p>这张图不存在，或者它在参考层、不对外开放。</p>
          <button type="button" className="mt-3 text-accent underline" onClick={() => go({ view: "base", mapId: catalog.maps[0].id })}>
            回到第一张图
          </button>
        </div>
      </div>
    );
  }

  const selected = nodeId ? catalog.nodeById.get(nodeId) : undefined;
  return (
    <div className="flex h-full flex-col">
      <div className="shrink-0 border-b border-line bg-surface px-6 py-3">
        <div className="flex flex-wrap items-start gap-x-5 gap-y-2">
          {mapsByDiscipline(catalog.maps).map((group) => (
            <div key={group.discipline} className="flex flex-wrap items-center gap-2" role="group" aria-label={DISCIPLINE_LABEL[group.discipline]}>
              <span className="text-[11.5px] font-semibold tracking-wide text-faint">{DISCIPLINE_LABEL[group.discipline]}</span>
              {group.maps.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  aria-current={m.id === mapId ? "page" : undefined}
                  onClick={() => go({ view: "base", mapId: m.id })}
                  className={`rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors ${m.id === mapId ? "bg-accent text-accent-ink" : "bg-surface-2 text-muted hover:text-ink"}`}
                >
                  {m.title}
                  <span className={`ml-1.5 text-[11px] ${m.id === mapId ? "opacity-80" : "text-faint"}`}>{m.nodes.length}</span>
                </button>
              ))}
            </div>
          ))}
        </div>
        <RateBar />
        <p className="mt-2 max-w-[1100px] text-[12.5px] leading-relaxed text-muted">{map.summary}</p>
        {map.theory && map.theory.length > 0 && (
          <div className="mt-2">
            <button
              type="button"
              onClick={() => setTheoryOpen((v) => !v)}
              aria-expanded={theoryOpen}
              className="flex items-center gap-1.5 text-[12.5px] font-medium text-muted transition-colors hover:text-ink"
            >
              <BookOpen size={14} /> 不建节点的理论科目 · {map.theory.length}
              <ChevronDown size={14} className={`transition-transform ${theoryOpen ? "rotate-180" : ""}`} />
            </button>
            {theoryOpen && (
              <div className="mt-2 grid gap-2.5 md:grid-cols-2 xl:grid-cols-3">
                {map.theory.map((topic) => (
                  <div key={topic.name} className="rounded-xl border border-line bg-surface p-3 text-[12.5px] leading-relaxed">
                    <div className="font-semibold">{topic.name}</div>
                    <p className="mt-1 text-muted">{topic.content}</p>
                    <p className="mt-1.5"><span className="font-semibold">在大局里的作用：</span><span className="text-muted">{topic.role}</span></p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="relative min-h-0 flex-1">
        <GraphCanvas
          layout={layout}
          nodes={catalog.nodeById}
          selectedId={nodeId}
          fitKey={map.id}
          drawerInset={selected ? drawerWidth : 0}
          columnNotes={notes}
          edgeCard={(placed) => <EdgeCard catalog={catalog} placed={placed} />}
          onSelect={selectNode}
        />
        <AnimatePresence>
          {selected && (
            <NodeDrawer
              key={selected.id}
              catalog={catalog}
              node={selected}
              width={drawerWidth}
              onClose={() => selectNode(null)}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
