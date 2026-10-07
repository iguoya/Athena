import { RATING_DIMS, RATING_SCHEME, dimDef, levelName, ratingVar } from "@/content/ratings";
import type { RatingDim, Ratings } from "@/content/types";
import { useApp } from "@/state/store";

/** 五格等级条：填满到该级为止，颜色随等级变化；旁边总有数字与名称，不只靠颜色。 */
export function Pips({ level, size = 9 }: { level: number; size?: number }) {
  return (
    <span className="inline-flex gap-[3px]" aria-hidden>
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className="rounded-[3px]"
          style={{ width: size, height: size + 3, background: i <= level ? ratingVar(level) : "var(--line)" }}
        />
      ))}
    </span>
  );
}

/** 一个维度一个等级的小徽章：色块里是数字，旁边是等级名。 */
export function LevelBadge({ dim, level }: { dim: RatingDim; level: number }) {
  const color = ratingVar(level);
  return (
    <span
      className="inline-flex items-center gap-1 rounded-md py-[2px] pl-[2px] pr-1.5 text-[10.5px] font-semibold text-ink"
      style={{ background: `color-mix(in srgb, ${color} 22%, transparent)` }}
    >
      <span className="grid size-[15px] place-items-center rounded-[4px] text-[10px] text-white" style={{ background: color }}>
        {level}
      </span>
      {levelName(dim, level)}
    </span>
  );
}

/** 六个维度的迷你条：卡片上用，悬停看每一项。 */
export function MiniStrip({ ratings }: { ratings: Ratings }) {
  return (
    <span className="inline-flex gap-[2px]" role="img" aria-label="六个维度的评级">
      {RATING_DIMS.map((dim) => {
        const item = ratings[dim];
        return (
          <span
            key={dim}
            aria-hidden
            className="h-[9px] w-[5px] rounded-[2px]"
            style={{ background: ratingVar(item.level) }}
            title={`${dimDef(dim)?.title}：${levelName(dim, item.level)}（${item.level}/5）`}
          />
        );
      })}
    </span>
  );
}

/** 评级的逐行显示：维度、等级条、等级名、依据，并标出是推导还是编辑评估。 */
export function RatingRows({ ratings, showReason = true }: { ratings: Ratings; showReason?: boolean }) {
  return (
    <div className="grid gap-2">
      {RATING_DIMS.map((dim) => {
        const def = dimDef(dim);
        const item = ratings[dim];
        if (!def || !item) return null;
        return (
          <div key={dim} className="rounded-xl border border-line bg-surface px-3 py-2.5" title={def.question}>
            <div className="flex items-center gap-2">
              <span className="w-[78px] shrink-0 text-[12.5px] font-semibold">{def.title}</span>
              <Pips level={item.level} />
              <LevelBadge dim={dim} level={item.level} />
              <span className="ml-auto rounded-full bg-surface-2 px-2 py-[2px] text-[10.5px] text-faint">
                {def.basis === "derived" ? "由内容推导" : "编辑评估"}
              </span>
            </div>
            {showReason && <p className="mt-1.5 text-[12px] leading-relaxed text-muted">{item.reason}</p>}
          </div>
        );
      })}
      {RATING_SCHEME.as_of && (
        <p className="text-[11px] leading-relaxed text-faint">
          评估日期 {RATING_SCHEME.as_of}。{RATING_SCHEME.note}
        </p>
      )}
    </div>
  );
}

/** 「按哪个维度着色」的选择条，带当前维度的图例。选择记在本机浏览器里，是个人偏好。 */
export function RateBar() {
  const rateBy = useApp((s) => s.rateBy);
  const setRateBy = useApp((s) => s.setRateBy);
  const active = rateBy ? dimDef(rateBy) : undefined;
  return (
    <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5" role="group" aria-label="按评级着色">
      <span className="text-[12px] font-semibold text-muted">着色</span>
      <div className="flex flex-wrap gap-1">
        <button
          type="button"
          aria-pressed={rateBy === null}
          onClick={() => setRateBy(null)}
          className={`rounded-full px-2.5 py-[3px] text-[12px] font-medium transition-colors ${rateBy === null ? "bg-accent text-accent-ink" : "bg-surface-2 text-muted hover:text-ink"}`}
        >
          默认
        </button>
        {RATING_SCHEME.dimensions.map((def) => (
          <button
            key={def.id}
            type="button"
            aria-pressed={rateBy === def.id}
            title={def.question}
            onClick={() => setRateBy(def.id)}
            className={`rounded-full px-2.5 py-[3px] text-[12px] font-medium transition-colors ${rateBy === def.id ? "bg-accent text-accent-ink" : "bg-surface-2 text-muted hover:text-ink"}`}
          >
            {def.title}
          </button>
        ))}
      </div>
      {active && (
        <div className="flex flex-wrap items-center gap-1.5" aria-label={`${active.title}的图例`}>
          {active.levels.map((lv) => (
            <span key={lv.level} title={lv.criterion} className="inline-flex">
              <LevelBadge dim={active.id} level={lv.level} />
            </span>
          ))}
          <span className="text-[11px] text-faint">{active.basis === "derived" ? "由内容推导" : "编辑评估"} · {active.question}</span>
        </div>
      )}
    </div>
  );
}
