import type { ReactNode } from "react";
import { motion } from "motion/react";
import { ArrowRight, Cpu, ExternalLink, Gauge, Lock, Maximize2, Minimize2, Route as RouteIcon, ShieldAlert, Star, Target, Wrench, X, Code2 } from "lucide-react";
import type { Catalog } from "@/content/catalog";
import { STAGE_LABEL } from "@/content/catalog";
import { routesOfNode } from "@/content/routes";
import type { PolarisEdge, PolarisNode } from "@/content/types";
import { locationForNode } from "@/state/nav";
import { useApp } from "@/state/store";
import { openExternal } from "@/ui/external";
import {
  CONTRACT_LABEL,
  MASTERY_LABEL,
  PRIORITY_HINT,
  PRIORITY_LABEL,
  RELATION_LABEL,
  TRACK_LABEL,
  VALIDATION_LABEL,
  VOLATILITY_LABEL,
  contractVar,
  stageVar,
} from "@/ui/labels";

interface Props {
  catalog: Catalog;
  node: PolarisNode;
  locked: boolean;
  width: number;
  onClose(): void;
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-6">
      <h3 className="mb-2 text-[11.5px] font-semibold tracking-[0.08em] text-faint">{title}</h3>
      {children}
    </section>
  );
}

function Chip({ children, color }: { children: ReactNode; color?: string }) {
  return (
    <span
      className="rounded-full px-2 py-[3px] text-[11.5px] font-medium"
      style={color ? { color, background: `color-mix(in srgb, ${color} 13%, transparent)` } : { background: "var(--surface-2)", color: "var(--muted)" }}
    >
      {children}
    </span>
  );
}

/** 先修与来路：每一项都带理由，点标题可以跳过去。 */
function EdgeList({ catalog, edges, side }: { catalog: Catalog; edges: PolarisEdge[]; side: "from" | "to" }) {
  const go = useApp((s) => s.go);
  const loc = useApp((s) => s.loc);
  return (
    <ul className="space-y-2.5">
      {edges.map((edge) => {
        const peerId = side === "from" ? edge.from : edge.to;
        const peer = catalog.nodeById.get(peerId);
        const target = locationForNode(catalog, loc, peerId);
        const strong = edge.relation === "requires";
        return (
          <li key={`${edge.from}>${edge.to}`} className="rounded-xl border border-line bg-surface p-3">
            <div className="flex items-center gap-2">
              <span
                className={`rounded-md px-1.5 py-[2px] text-[10.5px] font-semibold ${strong ? "bg-accent-soft text-accent" : "border border-dashed border-faint text-faint"}`}
              >
                {strong ? "门槛" : "来路"}
              </span>
              {target ? (
                <button type="button" onClick={() => go(target, true)} className="text-left font-medium text-ink underline decoration-line decoration-2 underline-offset-4 hover:decoration-accent">
                  {peer?.title ?? peerId}
                </button>
              ) : (
                <span className="font-medium text-muted" title="这个节点在参考层，不提供跳转">
                  {peer?.title ?? peerId}
                </span>
              )}
            </div>
            <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted">{edge.rationale}</p>
          </li>
        );
      })}
    </ul>
  );
}

export function NodeDrawer({ catalog, node, locked, width, onClose }: Props) {
  const wide = useApp((s) => s.drawerWide);
  const toggleWide = useApp((s) => s.toggleDrawerWide);
  const go = useApp((s) => s.go);
  const loc = useApp((s) => s.loc);

  const { inbound, outbound } = catalog.edgesOf(node.id);
  const cross = catalog.crossLinks(node.id);
  const routes = routesOfNode(catalog, node.id);
  const stageColor = stageVar(node.stage);

  return (
    <motion.aside
      role="complementary"
      aria-label={`${node.title} 的详情`}
      initial={{ x: 56, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 56, opacity: 0 }}
      transition={{ type: "spring", stiffness: 380, damping: 36 }}
      className="absolute inset-y-0 right-0 z-30 flex flex-col border-l border-line bg-[color:var(--bg)] shadow-[-24px_0_48px_-24px_rgb(0_0_0/0.18)]"
      style={{ width }}
    >
      <header className="relative shrink-0 border-b border-line bg-surface px-6 pb-4 pt-5">
        <span className="absolute inset-x-0 top-0 h-1" style={{ background: stageColor }} />
        <div className="flex items-start gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-1.5">
              {node.stage && <Chip color={stageColor}>{STAGE_LABEL[node.stage]}</Chip>}
              {node.priority && <Chip>{PRIORITY_LABEL[node.priority]}</Chip>}
              {node.contract && <Chip color={contractVar(node.contract)}>{CONTRACT_LABEL[node.contract]}契约</Chip>}
              {node.entry && (
                <span className="flex items-center gap-1 text-[11.5px] text-muted">
                  <Star size={12} className="text-gold" fill="currentColor" strokeWidth={0} /> 推荐的入门起点
                </span>
              )}
            </div>
            <h2 className="mt-2 text-[22px] font-bold leading-tight tracking-tight">{node.title}</h2>
            <p className="mt-1 font-mono text-[11px] text-faint">{node.id}</p>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <button
              type="button"
              onClick={toggleWide}
              title={wide ? "收窄" : "展开"}
              aria-label={wide ? "收窄" : "展开"}
              className="grid size-8 place-items-center rounded-lg text-muted transition-colors hover:bg-surface-2 hover:text-ink"
            >
              {wide ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>
            <button
              type="button"
              onClick={onClose}
              title="关闭（Esc）"
              aria-label="关闭"
              className="grid size-8 place-items-center rounded-lg text-muted transition-colors hover:bg-surface-2 hover:text-ink"
            >
              <X size={18} />
            </button>
          </div>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-6 pb-10">
        {locked && (
          <div className="mt-5 flex gap-2.5 rounded-xl border border-dashed border-faint bg-surface-2 p-3 text-[12.5px] leading-relaxed text-muted">
            <Lock size={15} className="mt-0.5 shrink-0" />
            <span>
              这一课还在没解锁的阶段里。可以查阅，但建议先打完上一阶段的主干——它是这一课的台阶（ADR 0014）。
            </span>
          </div>
        )}

        <p className="mt-5 text-[15px] leading-relaxed text-ink">{node.stable_definition}</p>

        {/* 指南针的三问：必要性、能力、产出（ADR 0012 决策 3） */}
        <Section title="三问">
          <div className="grid gap-2.5">
            {[
              {
                icon: <ShieldAlert size={15} />,
                title: "为什么必须学",
                body: node.priority_reason ?? node.stage_reason,
                note: node.priority ? PRIORITY_HINT[node.priority] : undefined,
              },
              { icon: <Wrench size={15} />, title: "学完能判断、设计什么", body: node.engineering_role },
              { icon: <Target size={15} />, title: "能交出什么", body: node.practice },
            ].map((item) => (
              <div key={item.title} className="rounded-xl border border-line bg-surface p-3.5">
                <div className="flex items-center gap-1.5 text-[12px] font-semibold text-accent">
                  {item.icon}
                  {item.title}
                </div>
                <p className="mt-1.5 text-[13.5px] leading-relaxed">{item.body}</p>
                {item.note && <p className="mt-1 text-[11.5px] text-faint">{item.note}</p>}
              </div>
            ))}
          </div>
          {node.stage_reason && node.priority_reason && (
            <p className="mt-2.5 text-[12.5px] leading-relaxed text-muted">
              <span className="font-semibold text-ink">为什么放在{node.stage ? STAGE_LABEL[node.stage] : "这一"}阶段：</span>
              {node.stage_reason}
            </p>
          )}
        </Section>

        {node.hw_side && node.sw_side && (
          <Section title="软硬两侧">
            <div className="grid grid-cols-2 gap-2.5">
              <div className="rounded-xl border border-line bg-surface p-3.5">
                <div className="flex items-center gap-1.5 text-[12px] font-semibold" style={{ color: "var(--balance-hardware)" }}>
                  <Cpu size={15} /> 硬件一侧
                </div>
                <p className="mt-1.5 text-[13px] leading-relaxed">{node.hw_side}</p>
              </div>
              <div className="rounded-xl border border-line bg-surface p-3.5">
                <div className="flex items-center gap-1.5 text-[12px] font-semibold" style={{ color: "var(--balance-software)" }}>
                  <Code2 size={15} /> 软件一侧
                </div>
                <p className="mt-1.5 text-[13px] leading-relaxed">{node.sw_side}</p>
              </div>
            </div>
          </Section>
        )}

        {node.pitfall && (
          <Section title="常见的坑">
            <p className="rounded-xl bg-accent-soft/60 p-3.5 text-[13.5px] leading-relaxed">{node.pitfall}</p>
          </Section>
        )}

        <Section title="怎么验证">
          <div className="flex flex-wrap items-center gap-1.5">
            <Chip>{VALIDATION_LABEL[node.validation] ?? node.validation}</Chip>
            <Chip>{VOLATILITY_LABEL[node.volatility] ?? node.volatility}</Chip>
            <Chip>{TRACK_LABEL[node.track] ?? node.track}</Chip>
          </div>
          {node.validation_note && <p className="mt-2 text-[13px] leading-relaxed text-muted">{node.validation_note}</p>}
        </Section>

        {inbound.length > 0 && (
          <Section title="先修与来路">
            <EdgeList catalog={catalog} edges={inbound} side="from" />
          </Section>
        )}
        {outbound.length > 0 && (
          <Section title="它为谁铺路">
            <EdgeList catalog={catalog} edges={outbound} side="to" />
          </Section>
        )}

        {cross.length > 0 && (
          <Section title="跨图关联">
            <ul className="space-y-2.5">
              {cross.map((link) => {
                const peer = catalog.nodeById.get(link.peerId);
                const target = locationForNode(catalog, loc, link.peerId);
                const peerMap = catalog.allMaps.find((m) => m.id === link.peerMapId);
                return (
                  <li key={`${link.edge.from}>${link.edge.to}`} className="rounded-xl border border-line bg-surface p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[11px] text-faint">{link.incoming ? "来自" : "通向"}</span>
                      {target ? (
                        <button type="button" onClick={() => go(target, true)} className="font-medium underline decoration-line decoration-2 underline-offset-4 hover:decoration-accent">
                          {peer?.title ?? link.peerId}
                        </button>
                      ) : (
                        <span className="font-medium text-muted">{peer?.title ?? link.peerId}</span>
                      )}
                      {peerMap && <span className="text-[11px] text-faint">· {peerMap.title}</span>}
                    </div>
                    <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted">{link.edge.rationale}</p>
                  </li>
                );
              })}
            </ul>
          </Section>
        )}

        {node.chapters && node.chapters.length > 0 && (
          <Section title={`细分学习流程 · ${node.chapters.length} 章`}>
            <ol className="space-y-2">
              {node.chapters.map((chapter, index) => (
                <li key={chapter.id} className="flex gap-3 rounded-xl border border-line bg-surface p-3">
                  <span className="grid size-6 shrink-0 place-items-center rounded-full bg-surface-2 text-[11px] font-semibold text-muted">{index + 1}</span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="font-medium">{chapter.title}</span>
                      <Chip>{MASTERY_LABEL[chapter.mastery]}</Chip>
                      {(chapter.kind === "practice" || chapter.hands_on) && <Chip color="var(--stage-junior)">实践</Chip>}
                    </div>
                    <p className="mt-1 text-[12.5px] leading-relaxed text-muted">{chapter.summary}</p>
                  </div>
                </li>
              ))}
            </ol>
          </Section>
        )}

        {routes.length > 0 && (
          <Section title="出现在这些路线里">
            <div className="flex flex-wrap gap-2">
              {routes.map((route) => (
                <button
                  key={route.id}
                  type="button"
                  onClick={() => go({ view: "route", routeId: route.id, nodeId: node.id })}
                  className="flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1.5 text-[12.5px] font-medium transition-colors hover:border-accent hover:text-accent"
                >
                  <RouteIcon size={13} /> {route.title}
                  <ArrowRight size={12} className="opacity-50" />
                </button>
              ))}
            </div>
          </Section>
        )}

        <Section title="出处">
          <ul className="space-y-2">
            {node.source_refs.map((ref) => {
              const source = catalog.sources.get(ref.source_id);
              return (
                <li key={`${ref.source_id}-${ref.locator}`} className="flex items-start gap-2 text-[12.5px] leading-relaxed">
                  <span className="mt-0.5 shrink-0 rounded-md bg-surface-2 px-1.5 py-[1px] text-[10.5px] font-medium text-muted">
                    {RELATION_LABEL[ref.relation] ?? ref.relation}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="font-medium">{source?.title ?? ref.source_id}</span>
                    <span className="text-muted"> · {ref.locator}</span>
                  </span>
                  {source && (
                    <button
                      type="button"
                      title="在浏览器里打开核对"
                      aria-label={`在浏览器里打开：${source.title}`}
                      onClick={() => void openExternal(source.url)}
                      className="mt-0.5 shrink-0 text-faint transition-colors hover:text-accent"
                    >
                      <ExternalLink size={14} />
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        </Section>

        <p className="mt-8 flex items-center gap-1.5 text-[11px] text-faint">
          <Gauge size={12} /> 具体语法、寄存器与操作步骤属于下游的学习应用，这里只回答大局。
        </p>
      </div>
    </motion.aside>
  );
}
