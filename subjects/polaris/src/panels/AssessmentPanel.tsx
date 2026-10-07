import { ArrowRight, ThumbsDown, ThumbsUp, X } from "lucide-react";
import type { Catalog } from "@/content/catalog";
import { VERDICT_HINT, VERDICT_LABEL, dimDef, levelName, strongAndWeak, verdictVar } from "@/content/ratings";
import type { Route } from "@/content/types";
import { useApp } from "@/state/store";
import { DISCIPLINE_LABEL } from "@/ui/labels";
import { RatingRows } from "@/ui/RatingParts";

interface Props {
  catalog: Catalog;
  route: Route;
  onClose(): void;
}

/** 路线评估：各维度的汇总评级、优劣与推荐的后续方向（ADR 0022）。评级由节点汇总，优劣与推荐是编辑评估。 */
export function AssessmentPanel({ catalog, route, onClose }: Props) {
  const go = useApp((s) => s.go);
  const assessment = route.assessment;
  const { strong, weak } = strongAndWeak(route.ratings);
  if (!assessment || !route.ratings) return null;
  const color = verdictVar(assessment.verdict);

  return (
    <div className="absolute right-4 top-3 z-30 flex max-h-[calc(100%-24px)] w-[500px] flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-lift)]">
      <div className="flex items-center gap-2 border-b border-line px-4 py-3">
        <span className="text-[14px] font-semibold">路线评估</span>
        <span
          className="rounded-full px-2.5 py-[3px] text-[11.5px] font-semibold text-ink"
          style={{ background: `color-mix(in srgb, ${color} 26%, transparent)`, boxShadow: `inset 0 0 0 1.5px ${color}` }}
          title={VERDICT_HINT[assessment.verdict]}
        >
          {VERDICT_LABEL[assessment.verdict]}
        </span>
        <button type="button" aria-label="关闭" onClick={onClose} className="ml-auto text-faint transition-colors hover:text-ink">
          <X size={16} />
        </button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-4 pt-3">
        <p className="text-[13px] leading-relaxed">{assessment.verdict_reason}</p>
        <p className="mt-1 text-[11px] text-faint">编辑评估：参照下面的评级、起步门槛与方向的时效性，不是由评级算出的分数。</p>

        <h3 className="mb-2 mt-4 text-[11.5px] font-semibold tracking-[0.08em] text-faint">各维度（由所含知识点汇总）</h3>
        <RatingRows ratings={route.ratings} showReason={false} />
        {(strong.length > 0 || weak.length > 0) && (
          <p className="mt-2 text-[12px] leading-relaxed text-muted">
            {strong.length > 0 && (
              <span>
                <span className="font-semibold text-ink">评级强项　</span>
                {strong.map((dim) => `${dimDef(dim)?.title}（${levelName(dim, route.ratings![dim].level)}）`).join("、")}
              </span>
            )}
            {strong.length > 0 && weak.length > 0 && <br />}
            {weak.length > 0 && (
              <span>
                <span className="font-semibold text-ink">评级弱项　</span>
                {weak.map((dim) => `${dimDef(dim)?.title}（${levelName(dim, route.ratings![dim].level)}）`).join("、")}
              </span>
            )}
          </p>
        )}

        <div className="mt-4 grid grid-cols-2 gap-2.5">
          <div className="rounded-xl border border-line bg-surface-2/50 p-3">
            <div className="flex items-center gap-1.5 text-[12px] font-semibold" style={{ color: "var(--rate-3)" }}>
              <ThumbsUp size={14} /> 优势
            </div>
            <ul className="mt-1.5 list-disc space-y-1 pl-4 text-[12.5px] leading-relaxed">
              {assessment.strengths.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl border border-line bg-surface-2/50 p-3">
            <div className="flex items-center gap-1.5 text-[12px] font-semibold" style={{ color: "var(--rate-5)" }}>
              <ThumbsDown size={14} /> 代价与局限
            </div>
            <ul className="mt-1.5 list-disc space-y-1 pl-4 text-[12.5px] leading-relaxed">
              {assessment.weaknesses.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <h3 className="mb-2 mt-4 text-[11.5px] font-semibold tracking-[0.08em] text-faint">推荐的后续方向</h3>
        <ul className="grid gap-2">
          {assessment.next.map((item) => {
            const target = catalog.routes.find((r) => r.id === item.route_id);
            if (!target) return null;
            const targetColor = target.assessment ? verdictVar(target.assessment.verdict) : "var(--faint)";
            return (
              <li key={item.route_id}>
                <button
                  type="button"
                  onClick={() => go({ view: "route", routeId: target.id })}
                  className="group flex w-full items-start gap-2 rounded-xl border border-line bg-surface p-3 text-left transition-colors hover:border-accent"
                >
                  <ArrowRight size={15} className="mt-0.5 shrink-0 text-accent" />
                  <span className="min-w-0 flex-1">
                    <span className="flex flex-wrap items-center gap-1.5 text-[13px] font-semibold">
                      {target.title}
                      <span className="rounded-full bg-surface-2 px-1.5 py-[2px] text-[10.5px] font-medium text-muted">{DISCIPLINE_LABEL[target.discipline]}</span>
                      {target.assessment && (
                        <span className="rounded-full px-1.5 py-[2px] text-[10.5px] font-medium text-ink" style={{ background: `color-mix(in srgb, ${targetColor} 24%, transparent)` }}>
                          {VERDICT_LABEL[target.assessment.verdict]}
                        </span>
                      )}
                    </span>
                    <span className="mt-0.5 block text-[12.5px] leading-relaxed text-muted">{item.reason}</span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

