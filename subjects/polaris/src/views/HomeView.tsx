import { motion } from "motion/react";
import { ArrowUpRight, Flag, Footprints } from "lucide-react";
import type { Catalog } from "@/content/catalog";
import { coveredDomains, DOMAINS, LADDER_ID } from "@/content/coverage";
import { BALANCES, LENSES, routeMatrix, routeNodeCount } from "@/content/routes";
import type { Route } from "@/content/types";
import { openExternal } from "@/ui/external";
import { useApp } from "@/state/store";
import { BALANCE_LABEL, LENS_HINT, LENS_LABEL, balanceVar } from "@/ui/labels";

function RouteCard({ catalog, route, index }: { catalog: Catalog; route: Route; index: number }) {
  const go = useApp((s) => s.go);
  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 * index, duration: 0.4, ease: [0.2, 0.7, 0.2, 1] }}
      onClick={() => go({ view: "route", routeId: route.id })}
      className="group relative flex flex-col overflow-hidden rounded-2xl border border-line bg-surface p-4 text-left shadow-[var(--shadow-card)] transition-[transform,box-shadow,border-color] duration-200 hover:-translate-y-1 hover:border-accent hover:shadow-[var(--shadow-lift)]"
    >
      <span className="absolute inset-x-0 top-0 h-1" style={{ background: balanceVar(route.balance) }} />
      <span className="flex items-start gap-2">
        <span className="flex-1 text-[15.5px] font-semibold leading-snug">{route.title}</span>
        <ArrowUpRight size={16} className="mt-0.5 shrink-0 text-faint transition-colors group-hover:text-accent" />
      </span>
      <span className="mt-1.5 line-clamp-3 text-[12.5px] leading-relaxed text-muted">{route.summary}</span>
      <span className="mt-3 flex items-start gap-1.5 rounded-lg bg-surface-2/70 p-2 text-[12px] leading-snug">
        <Flag size={12} className="mt-0.5 shrink-0 text-gold" fill="currentColor" />
        <span className="line-clamp-2">{route.artifact}</span>
      </span>
      <span className="mt-3 flex items-center gap-2 text-[11.5px] text-faint">
        <span>{route.stages.length} 个阶段</span>·<span>{routeNodeCount(route)} 个知识点</span>·<span>碰到 {coveredDomains(catalog, route)}/{DOMAINS.length} 个域</span>
      </span>
    </motion.button>
  );
}

export function HomeView({ catalog }: { catalog: Catalog }) {
  const go = useApp((s) => s.go);
  const matrix = routeMatrix(catalog);
  const codesign = catalog.allMaps.find((map) => map.view_kind === "codesign");
  const ladder = catalog.routes.find((r) => r.id === LADDER_ID);
  let counter = 0;

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-[1280px] px-8 pb-16 pt-9">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
          <h1 className="text-[34px] font-bold leading-tight tracking-tight">
            同一块知识底盘，<span className="text-accent">走出不同的路线</span>
          </h1>
          <p className="mt-2 max-w-[760px] text-[15px] leading-relaxed text-muted">
            先选一个角度和技术方向，沿它的阶段走下去；每条路线都有一个能检查的终点产物。
            软硬结合是主线——软件看见的硬件、硬件承诺给软件的东西，被当作一等知识来讲。
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-[12.5px] text-muted">
            <span className="rounded-full bg-surface px-3 py-1 shadow-[var(--shadow-card)]">{catalog.routes.length} 条路线</span>
            <span className="rounded-full bg-surface px-3 py-1 shadow-[var(--shadow-card)]">
              {catalog.maps.reduce((sum, map) => sum + map.nodes.length, 0)} 个知识点在底盘里
            </span>
            {codesign && (
              <button
                type="button"
                onClick={() => go({ view: "base", mapId: codesign.id })}
                className="rounded-full bg-accent-soft px-3 py-1 font-medium text-accent transition-colors hover:bg-accent hover:text-accent-ink"
              >
                {codesign.nodes.length} 个软硬接口节点 →
              </button>
            )}
          </div>
        </motion.div>

        {ladder && (
          <button
            type="button"
            onClick={() => go({ view: "route", routeId: ladder.id })}
            className="mt-8 flex w-full items-center gap-5 rounded-2xl border border-accent/40 bg-accent-soft/50 p-5 text-left transition-[transform,box-shadow] hover:-translate-y-0.5 hover:shadow-[var(--shadow-lift)]"
          >
            <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-accent text-accent-ink">
              <Footprints size={22} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="text-[12px] font-semibold tracking-wide text-accent">先走这条，再选方向</span>
              <span className="mt-0.5 block text-[18px] font-bold">{ladder.title}</span>
              <span className="mt-1 block text-[13px] leading-relaxed text-muted">{ladder.summary}</span>
            </span>
            <span className="hidden shrink-0 text-right text-[12px] text-muted md:block">
              {ladder.stages.length} 个阶段 · {routeNodeCount(ladder)} 个知识点
              <br />
              十二个能力域一个不缺
            </span>
            <ArrowUpRight size={20} className="shrink-0 text-accent" />
          </button>
        )}

        {/* 软硬权重轴：路线按「偏软件 ↔ 偏硬件」放在三列里，行是划分角度 */}
        <div className="mt-8 grid grid-cols-[168px_repeat(3,minmax(0,1fr))] gap-x-5 gap-y-5">
          <div />
          {BALANCES.map((balance) => (
            <div key={balance} className="flex flex-col gap-2">
              <span className="text-[13px] font-semibold" style={{ color: balanceVar(balance) }}>
                {BALANCE_LABEL[balance]}
              </span>
              <span
                className="h-1.5 rounded-full"
                style={{ background: `linear-gradient(90deg, ${balanceVar(balance)}, color-mix(in srgb, ${balanceVar(balance)} 25%, transparent))` }}
              />
            </div>
          ))}

          {LENSES.map((lens) => (
            <div key={lens} className="contents">
              <div className="pt-1">
                <div className="text-[14px] font-semibold">{LENS_LABEL[lens]}</div>
                <p className="mt-1 text-[12px] leading-snug text-muted">{LENS_HINT[lens]}</p>
              </div>
              {BALANCES.map((balance) => {
                const routes = matrix[lens][balance];
                return (
                  <div key={balance} className="flex flex-col gap-3">
                    {routes.length === 0 ? (
                      <div className="grid min-h-[72px] place-items-center rounded-2xl border border-dashed border-line text-[12px] text-faint">
                        这里还没有路线
                      </div>
                    ) : (
                      routes.map((route) => <RouteCard key={route.id} catalog={catalog} route={route} index={counter++} />)
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>

        {catalog.principles.length > 0 && (
          <section className="mt-12">
            <h2 className="text-[15px] font-semibold">几条被反复验证的学习原则</h2>
            <p className="mt-1 text-[12.5px] text-muted">来自资深从业者的文章、体系结构领域的权威论述与真实的高端岗位描述，每条都带出处，可以点开核对。</p>
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {catalog.principles.map((principle) => (
                <div key={principle.id} className="flex flex-col rounded-2xl border border-line bg-surface p-4">
                  <div className="text-[14px] font-semibold leading-snug">{principle.title}</div>
                  <p className="mt-1.5 flex-1 text-[12.5px] leading-relaxed text-muted">{principle.body}</p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {principle.source_refs.map((ref) => {
                      const source = catalog.sources.get(ref.source_id);
                      return (
                        <button
                          key={`${ref.source_id}-${ref.locator}`}
                          type="button"
                          title={`${source?.title ?? ref.source_id} · ${ref.locator}`}
                          onClick={() => source && void openExternal(source.url)}
                          className="max-w-full truncate rounded-full bg-surface-2 px-2.5 py-1 text-[11px] text-muted transition-colors hover:bg-accent-soft hover:text-accent"
                        >
                          {source?.title.split(/[：:（(]/)[0] ?? ref.source_id}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <h2 className="mb-3 mt-12 text-[15px] font-semibold">想直接看全景？底盘里的图</h2>
        <div className="flex flex-wrap gap-2.5">
          {catalog.maps.map((map) => (
            <button
              key={map.id}
              type="button"
              onClick={() => go({ view: "base", mapId: map.id })}
              className="rounded-xl border border-line bg-surface px-4 py-2.5 text-left text-[13px] transition-[border-color,box-shadow] hover:border-accent hover:shadow-[var(--shadow-card)]"
            >
              <span className="font-medium">{map.title}</span>
              <span className="ml-2 text-faint">{map.nodes.length} 个</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
