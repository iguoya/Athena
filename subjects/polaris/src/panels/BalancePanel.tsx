import { AlertTriangle, Check, X } from "lucide-react";
import type { Catalog } from "@/content/catalog";
import { DOMAINS, LADDER_ID, blindSpots, coveredDomains, routeCoverage } from "@/content/coverage";
import type { Route } from "@/content/types";
import { locationForNode } from "@/state/nav";
import { useApp } from "@/state/store";
import { RadarChart, sideColor } from "./RadarChart";

interface Props {
  catalog: Catalog;
  route: Route;
  onClose(): void;
}

/** 均衡度面板：这条路线碰到了哪些能力域、漏了哪些、该补什么，以及这个方向最常见的偏科（ADR 0018）。 */
export function BalancePanel({ catalog, route, onClose }: Props) {
  const go = useApp((s) => s.go);
  const loc = useApp((s) => s.loc);
  const coverage = routeCoverage(catalog, route);
  const spots = blindSpots(catalog, route);
  const isLadder = route.id === LADDER_ID;
  const ladder = catalog.routes.find((r) => r.id === LADDER_ID);

  return (
    <div className="absolute right-4 top-3 z-30 flex max-h-[calc(100%-24px)] w-[480px] flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-lift)]">
      <div className="flex items-center gap-2 border-b border-line px-4 py-3">
        <span className="text-[14px] font-semibold">均衡度</span>
        <span className="text-[12px] text-muted">碰到 {coveredDomains(catalog, route)} / {DOMAINS.length} 个能力域</span>
        <button type="button" aria-label="关闭" onClick={onClose} className="ml-auto text-faint transition-colors hover:text-ink">
          <X size={16} />
        </button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-4 pt-3">
        <div className="flex items-start gap-3">
          <div className="shrink-0">
            <RadarChart coverage={coverage} size={236} />
            <div className="mt-1 flex justify-center gap-3 text-[10.5px] text-faint">
              {(["software", "boundary", "hardware"] as const).map((side) => (
                <span key={side} className="flex items-center gap-1">
                  <span className="size-2 rounded-full" style={{ background: sideColor(side) }} />
                  {side === "software" ? "软件侧" : side === "boundary" ? "软硬交界" : "硬件侧"}
                </span>
              ))}
            </div>
          </div>
          <ul className="min-w-0 flex-1 space-y-1 pt-1 text-[12px]">
            {DOMAINS.map((domain, index) => {
              const entry = coverage[index];
              return (
                <li key={domain.id} className="flex items-center gap-1.5" title={domain.hint}>
                  {entry.covered > 0 ? <Check size={12} className="shrink-0 text-accent" /> : <span className="size-3 shrink-0 rounded-full border border-dashed border-faint" />}
                  <span className={entry.covered > 0 ? "" : "text-faint"}>{domain.label}</span>
                  <span className="ml-auto tabular-nums text-faint">
                    {entry.covered}/{entry.total}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>

        {isLadder ? (
          <p className="mt-3 rounded-xl bg-accent-soft/60 p-3 text-[12.5px] leading-relaxed">
            这条阶梯保证十二个能力域一个不缺——选定纵深方向之前，先走完它，就不会营养不良。
          </p>
        ) : spots.length > 0 ? (
          <div className="mt-3">
            <div className="flex items-center gap-1.5 text-[12.5px] font-semibold">
              <AlertTriangle size={14} className="text-gold" /> 这条路线没有碰到的域，建议补上
            </div>
            <ul className="mt-2 space-y-2">
              {spots.map((spot) => {
                const domain = DOMAINS.find((d) => d.id === spot.domain)!;
                return (
                  <li key={spot.domain} className="rounded-xl border border-line p-2.5 text-[12.5px]">
                    <div className="font-medium">{domain.label}</div>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {spot.suggestions.map((node) => {
                        const target = locationForNode(catalog, loc, node.id);
                        return (
                          <button
                            key={node.id}
                            type="button"
                            disabled={!target}
                            onClick={() => target && go(target)}
                            className="rounded-full bg-surface-2 px-2.5 py-1 text-[12px] text-muted transition-colors hover:bg-accent-soft hover:text-accent"
                          >
                            {node.title}
                          </button>
                        );
                      })}
                    </div>
                  </li>
                );
              })}
            </ul>
            {ladder && (
              <button
                type="button"
                onClick={() => go({ view: "route", routeId: ladder.id })}
                className="mt-2 text-[12px] text-accent underline underline-offset-4"
              >
                或者直接回到「{ladder.title}」，一次补齐
              </button>
            )}
          </div>
        ) : (
          <p className="mt-3 text-[12.5px] text-muted">十二个域都碰到了。</p>
        )}

        {route.pitfalls && route.pitfalls.length > 0 && (
          <div className="mt-4">
            <div className="text-[12.5px] font-semibold">这个方向最常见的偏科</div>
            <ul className="mt-2 space-y-1.5 text-[12.5px] leading-relaxed text-muted">
              {route.pitfalls.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="mt-[7px] size-1.5 shrink-0 rounded-full bg-gold" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
