import { motion } from "motion/react";
import { Star } from "lucide-react";
import type { PlacedNode } from "@/content/layout";
import { STAGE_LABEL } from "@/content/catalog";
import type { PolarisNode } from "@/content/types";
import { useApp } from "@/state/store";
import { LevelBadge, MiniStrip } from "@/ui/RatingParts";
import { lensLevel, ratingVar } from "@/content/ratings";
import { CONTRACT_LABEL, CURRENT_LABEL, PRIORITY_LABEL, TRACK_LABEL, contractVar, currentVar, stageVar } from "@/ui/labels";

export type CardState = "idle" | "selected" | "near" | "dim";

interface Props {
  node: PolarisNode;
  placed: PlacedNode;
  state: CardState;
  /** 入场动画的延迟，按列与行错开，一张图像是被一层层点亮。 */
  delay: number;
  onSelect(): void;
  onHover(on: boolean): void;
}

const PRIORITY_STYLE = {
  essential: "bg-accent-soft text-accent",
  important: "bg-surface-2 text-muted",
  optional: "border border-dashed border-faint text-faint",
} as const;

export function NodeCard({ node, placed, state, delay, onSelect, onHover }: Props) {
  const stageColor = stageVar(node.stage);
  const selected = state === "selected";
  const rateBy = useApp((s) => s.rateBy);
  const rated = rateBy ? lensLevel(node, rateBy) : undefined;
  const tint = rated !== undefined ? ratingVar(rated) : undefined;
  return (
    <motion.button
      type="button"
      data-node-id={node.id}
      aria-pressed={selected}
      aria-label={node.title}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: state === "dim" ? 0.34 : 1, y: 0 }}
      transition={{ delay, duration: 0.38, ease: [0.2, 0.7, 0.2, 1] }}
      onPointerDown={(event) => event.stopPropagation()}
      onClick={(event) => {
        event.stopPropagation();
        onSelect();
      }}
      onMouseEnter={() => onHover(true)}
      onMouseLeave={() => onHover(false)}
      onFocus={() => onHover(true)}
      onBlur={() => onHover(false)}
      style={{
        left: placed.x,
        top: placed.y,
        width: placed.w,
        height: placed.h,
        ...(tint
          ? { background: `color-mix(in srgb, ${tint} 17%, var(--surface))`, borderColor: selected ? undefined : tint }
          : {}),
      }}
      className={[
        "absolute overflow-hidden rounded-2xl border bg-surface p-3 pl-[18px] text-left",
        "shadow-[var(--shadow-card)] transition-[box-shadow,transform,border-color] duration-200",
        "hover:-translate-y-0.5 hover:shadow-[var(--shadow-lift)]",
        selected ? "border-accent ring-2 ring-accent/30 shadow-[var(--shadow-lift)]" : "border-line",
      ].join(" ")}
    >
      <span className="absolute inset-y-0 left-0 w-[6px]" style={{ background: stageColor }} />
      <span className="flex items-center gap-1.5 text-[11px] font-medium leading-none">
        <span style={{ color: stageColor }}>{node.stage ? STAGE_LABEL[node.stage] : "—"}</span>
        {node.priority && (
          <span className={`rounded-full px-1.5 py-[3px] text-[10.5px] ${PRIORITY_STYLE[node.priority]}`}>
            {PRIORITY_LABEL[node.priority]}
          </span>
        )}
        {node.entry && (
          <span className="flex items-center gap-0.5 text-gold" title="推荐的入门起点">
            <Star size={11} fill="currentColor" strokeWidth={0} />
            <span className="text-[10.5px] text-muted">起点</span>
          </span>
        )}
      </span>
      {node.ratings && (
        <span className="absolute right-2.5 top-2.5">
          {rateBy && rated !== undefined ? <LevelBadge dim={rateBy} level={rated} /> : <MiniStrip ratings={node.ratings} />}
        </span>
      )}
      <span className="mt-2 line-clamp-2 text-[15px] font-semibold leading-snug">{node.title}</span>
      <span className="absolute inset-x-0 bottom-0 flex items-center gap-1.5 px-[18px] pb-2.5 text-[11px] text-muted">
        {node.contract ? (
          <span
            className="rounded-md px-1.5 py-[2px] font-medium"
            style={{ color: contractVar(node.contract), background: `color-mix(in srgb, ${contractVar(node.contract)} 12%, transparent)` }}
          >
            {CONTRACT_LABEL[node.contract]}
          </span>
        ) : (
          <span>{TRACK_LABEL[node.track] ?? node.track}</span>
        )}
        {node.current && (
          <span
            className="rounded-md px-1.5 py-[2px] font-medium"
            style={{ color: currentVar(node.current), background: `color-mix(in srgb, ${currentVar(node.current)} 12%, transparent)` }}
          >
            {CURRENT_LABEL[node.current]}
          </span>
        )}
        {node.chapters && node.chapters.length > 0 && <span className="ml-auto tabular-nums text-faint">{node.chapters.length} 章</span>}
      </span>
    </motion.button>
  );
}
