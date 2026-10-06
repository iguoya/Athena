import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Flag, Maximize2, Minus, Plus } from "lucide-react";
import type { Layout, PlacedEdge } from "@/content/layout";
import type { PolarisNode } from "@/content/types";
import { useApp } from "@/state/store";
import { EdgeLayer, type EdgeState } from "./EdgeLayer";
import { NodeCard, type CardState } from "./NodeCard";
import {
  ensureVisible,
  fitViewport,
  fitWidthViewport,
  sameViewport,
  zoomAt,
  type Size,
  type Viewport,
} from "./viewport";

export interface ColumnNote {
  /** 列头下方的一句话：这一阶段要做到什么。 */
  goal?: string;
  /** 列底的「验收」：这一阶段结束时能拿出什么。 */
  checkpoint?: string;
  /** 列头上方的小标签，如「第 2 阶段」。 */
  eyebrow?: string;
}

interface Props {
  layout: Layout;
  nodes: Map<string, PolarisNode>;
  selectedId?: string;
  /** 变化时重新「按宽度适配」，比如切了一张图或一条路线。 */
  fitKey: string;
  /** 被抽屉盖住的宽度，居中与可见性都要扣掉它。 */
  drawerInset: number;
  columnNotes?: Map<string, ColumnNote>;
  /** 点开连线编号时浮出的内容。 */
  edgeCard?(edge: PlacedEdge): ReactNode;
  onSelect(id: string | null): void;
}

const edgeKeyOf = (edge: PlacedEdge) => `${edge.edge.from}>${edge.edge.to}`;

export function GraphCanvas(props: Props) {
  const { layout, nodes, selectedId, fitKey, drawerInset, columnNotes, edgeCard, onSelect } =
    props;
  const hoverId = useApp((s) => s.hoverId);
  const setHover = useApp((s) => s.setHover);
  const edgeKey = useApp((s) => s.edgeKey);
  const setEdge = useApp((s) => s.setEdge);

  const wrapRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState<Size>({ w: 0, h: 0 });
  const [view, setView] = useState<Viewport>({ x: 0, y: 0, k: 1 });
  const [animate, setAnimate] = useState(false);
  const [dragging, setDragging] = useState(false);
  const animateTimer = useRef<number | undefined>(undefined);

  // —— 视口：尺寸、适配、程序化移动 ——
  useLayoutEffect(() => {
    const element = wrapRef.current;
    if (!element) return;
    const measure = () => setSize({ w: element.clientWidth, h: element.clientHeight });
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const moveTo = useCallback((next: Viewport, smooth: boolean) => {
    window.clearTimeout(animateTimer.current);
    setAnimate(smooth);
    setView((current) => (sameViewport(current, next) ? current : next));
    if (smooth) animateTimer.current = window.setTimeout(() => setAnimate(false), 420);
  }, []);

  const fittedKey = useRef<string>("");
  useLayoutEffect(() => {
    if (size.w === 0) return;
    if (fittedKey.current === fitKey) return;
    fittedKey.current = fitKey;
    moveTo(fitWidthViewport({ w: layout.width, h: layout.height }, { w: size.w - drawerInset, h: size.h }), false);
  }, [fitKey, size, layout.width, layout.height, drawerInset, moveTo]);

  // 选中变化（点节点、抽屉里跳转、深链接）后，保证它在可见区域里。
  useEffect(() => {
    if (!selectedId || size.w === 0) return;
    const placed = layout.byId.get(selectedId);
    if (!placed) return;
    setView((current) => {
      const next = ensureVisible(current, placed, size, drawerInset);
      if (sameViewport(current, next)) return current;
      setAnimate(true);
      window.clearTimeout(animateTimer.current);
      animateTimer.current = window.setTimeout(() => setAnimate(false), 420);
      return next;
    });
  }, [selectedId, layout, size, drawerInset]);

  // —— 滚轮：平移；Ctrl/⌘ + 滚轮（含触控板捏合）：缩放 ——
  useEffect(() => {
    const element = wrapRef.current;
    if (!element) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      setAnimate(false);
      if (event.ctrlKey || event.metaKey) {
        const rect = element.getBoundingClientRect();
        const factor = Math.exp(-event.deltaY * 0.01);
        setView((current) => zoomAt(current, factor, event.clientX - rect.left, event.clientY - rect.top));
      } else {
        setView((current) => ({ ...current, x: current.x - event.deltaX, y: current.y - event.deltaY }));
      }
    };
    element.addEventListener("wheel", onWheel, { passive: false });
    return () => element.removeEventListener("wheel", onWheel);
  }, []);

  // —— 拖动背景平移；没有拖动的点击算「点空白处」，取消选中 ——
  const drag = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  const onPointerDown = (event: React.PointerEvent) => {
    if (event.button !== 0) return;
    drag.current = { x: event.clientX, y: event.clientY, moved: false };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const onPointerMove = (event: React.PointerEvent) => {
    const state = drag.current;
    if (!state) return;
    const dx = event.clientX - state.x;
    const dy = event.clientY - state.y;
    if (!state.moved && Math.hypot(dx, dy) < 4) return;
    if (!state.moved) {
      state.moved = true;
      setDragging(true);
      setAnimate(false);
    }
    state.x = event.clientX;
    state.y = event.clientY;
    setView((current) => ({ ...current, x: current.x + dx, y: current.y + dy }));
  };
  const onPointerUp = (event: React.PointerEvent) => {
    const state = drag.current;
    drag.current = null;
    setDragging(false);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    if (state && !state.moved) {
      onSelect(null);
      setEdge(null);
    }
  };

  // —— 聚焦：悬停是预览，选中是钉住；与聚焦点相连的边与节点点亮，其余压暗 ——
  const focusId = hoverId ?? selectedId ?? null;
  const near = useMemo(() => {
    const set = new Set<string>();
    if (!focusId) return set;
    set.add(focusId);
    for (const placed of layout.edges) {
      if (placed.edge.from === focusId) set.add(placed.edge.to);
      if (placed.edge.to === focusId) set.add(placed.edge.from);
    }
    return set;
  }, [focusId, layout.edges]);

  const edgeState = useCallback(
    (placed: PlacedEdge): EdgeState => {
      if (edgeKey === edgeKeyOf(placed)) return "selected";
      if (!focusId) return "idle";
      return placed.edge.from === focusId || placed.edge.to === focusId ? "active" : "dim";
    },
    [edgeKey, focusId],
  );

  const cardState = (id: string): CardState => {
    if (id === selectedId) return "selected";
    if (!focusId) return "idle";
    return near.has(id) ? "near" : "dim";
  };

  const metrics = layout.metrics;
  const openEdge = layout.edges.find((placed) => edgeKeyOf(placed) === edgeKey);

  const zoomBy = (factor: number) => moveTo(zoomAt(view, factor, (size.w - drawerInset) / 2, size.h / 2), true);

  return (
    <div
      ref={wrapRef}
      className="canvas-surface relative h-full w-full overflow-hidden"
      data-dragging={dragging}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onDoubleClick={() => moveTo(fitWidthViewport({ w: layout.width, h: layout.height }, { w: size.w - drawerInset, h: size.h }), true)}
      style={{ backgroundSize: `${24 * view.k}px ${24 * view.k}px`, backgroundPosition: `${view.x}px ${view.y}px` }}
    >
      <div
        className="absolute left-0 top-0 origin-top-left"
        style={{
          width: layout.width,
          height: layout.height,
          transform: `translate(${view.x}px, ${view.y}px) scale(${view.k})`,
          transition: animate ? "transform 380ms cubic-bezier(0.2, 0.7, 0.2, 1)" : "none",
          willChange: "transform",
        }}
      >
        {/* 列底：每个阶段一条淡色的带，让「阶段是列」一眼可见 */}
        {layout.columns.map((column) => (
          <div
            key={`band-${column.key}`}
            className="absolute rounded-[28px] bg-surface-2/55"
            style={{ left: column.x - 18, top: metrics.padTop - 10, width: column.width + 36, height: layout.height - metrics.padTop - metrics.padBottom + 36 }}
          />
        ))}

        <EdgeLayer width={layout.width} height={layout.height} edges={layout.edges} stateOf={edgeState} />

        {layout.nodes.map((placed) => {
          const node = nodes.get(placed.id);
          if (!node) return null;
          return (
            <NodeCard
              key={placed.id}
              node={node}
              placed={placed}
              state={cardState(placed.id)}
              delay={0.04 * placed.column + 0.025 * placed.row}
              onSelect={() => {
                setEdge(null);
                onSelect(placed.id);
              }}
              onHover={(on) => setHover(on ? placed.id : null)}
            />
          );
        })}

        {/* 连线编号：只在连线被聚焦时出现，免得一张密图被几十个数字盖住；点开看这条依赖凭什么成立 */}
        {layout.edges.map((placed) => {
          const key = edgeKeyOf(placed);
          const state = edgeState(placed);
          const shown = state === "active" || state === "selected";
          return (
            <button
              key={`mark-${key}`}
              type="button"
              tabIndex={shown ? 0 : -1}
              aria-hidden={!shown}
              aria-label={`第 ${placed.number} 条依赖：${placed.edge.rationale}`}
              onPointerDown={(event) => event.stopPropagation()}
              onClick={(event) => {
                event.stopPropagation();
                setEdge(edgeKey === key ? null : key);
              }}
              className={[
                "absolute grid size-[22px] -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-accent bg-accent text-[10.5px] font-semibold tabular-nums text-accent-ink",
                "transition-[transform,opacity] duration-150 hover:scale-125",
                shown ? "opacity-100" : "pointer-events-none opacity-0",
              ].join(" ")}
              style={{ left: placed.mid.x, top: placed.mid.y }}
            >
              {placed.number}
            </button>
          );
        })}

        {layout.columns.map((column) => {
          const note = columnNotes?.get(column.key);
          return (
            <div
              key={`head-${column.key}`}
              className="absolute"
              style={{ left: column.x, top: metrics.padTop, width: column.width, height: metrics.headerHeight - 8 }}
            >
              {note?.eyebrow && <div className="text-[11px] font-medium tracking-wide text-faint">{note.eyebrow}</div>}
              <div className="flex items-center gap-2">
                <span className="size-2.5 rounded-full" style={{ background: column.stage ? `var(--stage-${column.stage})` : "var(--accent)" }} />
                <span className="text-[17px] font-semibold">{column.label}</span>
                <span className="text-[11px] text-faint">{column.count} 个</span>
              </div>
              {note?.goal && <div className="mt-0.5 line-clamp-2 text-[12px] leading-snug text-muted">{note.goal}</div>}
            </div>
          );
        })}

        {layout.metrics.footerHeight > 0 &&
          layout.columns.map((column) => {
            const note = columnNotes?.get(column.key);
            if (!note?.checkpoint) return null;
            return (
              <div
                key={`foot-${column.key}`}
                className="absolute rounded-2xl border border-dashed border-line bg-surface/80 p-3 text-[12px] leading-snug text-muted"
                style={{ left: column.x, top: layout.contentBottom + 24, width: column.width, height: metrics.footerHeight - 32 }}
              >
                <div className="mb-1 flex items-center gap-1 font-semibold text-ink">
                  <Flag size={12} className="text-gold" fill="currentColor" /> 阶段验收
                </div>
                <div className="line-clamp-4">{note.checkpoint}</div>
              </div>
            );
          })}

        {openEdge && edgeCard && (
          <div
            className="absolute z-20 w-[340px]"
            style={{ left: openEdge.mid.x + 16, top: openEdge.mid.y - 14 }}
            onPointerDown={(event) => event.stopPropagation()}
            onClick={(event) => event.stopPropagation()}
          >
            {edgeCard(openEdge)}
          </div>
        )}
      </div>

      {/* 缩放控件：抽屉打开时让开它 */}
      <div
        className="absolute bottom-4 flex flex-col overflow-hidden rounded-xl border border-line bg-surface shadow-[var(--shadow-card)]"
        style={{ left: 16 }}
        onPointerDown={(event) => event.stopPropagation()}
        onDoubleClick={(event) => event.stopPropagation()}
      >
        {[
          { label: "放大", icon: <Plus size={16} />, run: () => zoomBy(1.2) },
          { label: "缩小", icon: <Minus size={16} />, run: () => zoomBy(1 / 1.2) },
          {
            label: "整体适配",
            icon: <Maximize2 size={15} />,
            run: () => moveTo(fitViewport({ w: layout.width, h: layout.height }, { w: size.w - drawerInset, h: size.h }), true),
          },
        ].map((item) => (
          <button
            key={item.label}
            type="button"
            title={item.label}
            aria-label={item.label}
            onClick={item.run}
            className="grid size-9 place-items-center text-muted transition-colors hover:bg-surface-2 hover:text-ink"
          >
            {item.icon}
          </button>
        ))}
      </div>
      <div className="pointer-events-none absolute bottom-4 left-[68px] hidden text-[11px] text-faint md:block">
        悬停或点选节点，看它的依赖 · 点连线上的编号看理由 · 拖动平移 · Ctrl/⌘ + 滚轮缩放 · 双击空白处适配
      </div>
    </div>
  );
}

