import { useMemo } from "react";
import { AnimatePresence } from "motion/react";
import { LockOpen } from "lucide-react";
import { STAGES, STAGE_LABEL, stageRank, type Catalog } from "@/content/catalog";
import { layoutByStage, type PlacedColumn } from "@/content/layout";
import { GraphCanvas, type ColumnNote } from "@/graph/GraphCanvas";
import { EdgeCard } from "@/panels/EdgeCard";
import { NodeDrawer } from "@/panels/NodeDrawer";
import type { Stage } from "@/content/types";
import { useApp } from "@/state/store";
import { useDrawerWidth } from "@/ui/useDrawerWidth";

export function BaseView({ catalog, mapId, nodeId }: { catalog: Catalog; mapId: string; nodeId?: string }) {
  const go = useApp((s) => s.go);
  const selectNode = useApp((s) => s.selectNode);
  const aim = useApp((s) => s.aimByMap[mapId] ?? 0);
  const unlockNext = useApp((s) => s.unlockNext);
  const drawerWidth = useDrawerWidth();

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
  // 原则上一个阶段没解锁，不应该学更高的阶段（ADR 0014 决策 2）；解锁只在本次打开窗口里有效，不记进度。
  const lockedStage = (stage: Stage | undefined) => stageRank(stage) > aim;
  const nextToUnlock = (column: PlacedColumn) => column.stage !== undefined && stageRank(column.stage) === aim + 1;

  return (
    <div className="flex h-full flex-col">
      <div className="shrink-0 border-b border-line bg-surface px-6 py-3">
        <div className="flex flex-wrap items-center gap-2">
          {catalog.maps.map((m) => (
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
        <p className="mt-2 max-w-[1100px] text-[12.5px] leading-relaxed text-muted">{map.summary}</p>
      </div>

      <div className="relative min-h-0 flex-1">
        <GraphCanvas
          layout={layout}
          nodes={catalog.nodeById}
          selectedId={nodeId}
          fitKey={map.id}
          drawerInset={selected ? drawerWidth : 0}
          columnNotes={notes}
          isLocked={(node) => lockedStage(node.stage)}
          columnLocked={(column) => lockedStage(column.stage)}
          columnAction={(column) =>
            nextToUnlock(column) ? (
              <button
                type="button"
                onClick={() => unlockNext(map.id)}
                title="前一阶段的主干打完之后，再解锁这一阶段（只在本次打开窗口里有效，不记进度）"
                className="flex items-center gap-1 rounded-full border border-line bg-surface px-2.5 py-1 text-[11.5px] font-medium text-muted transition-colors hover:border-accent hover:text-accent"
              >
                <LockOpen size={12} /> 解锁{column.stage ? STAGE_LABEL[column.stage] : ""}
              </button>
            ) : null
          }
          edgeCard={(placed) => <EdgeCard catalog={catalog} placed={placed} />}
          onSelect={selectNode}
        />
        <AnimatePresence>
          {selected && (
            <NodeDrawer
              key={selected.id}
              catalog={catalog}
              node={selected}
              locked={lockedStage(selected.stage)}
              width={drawerWidth}
              onClose={() => selectNode(null)}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
