import {
  POLICY_SCHEME,
  RATING_DIMS,
  RATING_SCHEME,
  dimDef,
  fieldKey,
  isFieldKey,
  levelName,
  lensLevels,
  lensQuestion,
  lensTitle,
  ratingVar,
  type LensKey,
} from "@/content/ratings";
import type { Ratings } from "@/content/types";
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
export function LevelBadge({ dim, level }: { dim: LensKey; level: number }) {
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

/** 各维度的迷你条：卡片上用，悬停看每一项。 */
export function MiniStrip({ ratings }: { ratings: Ratings }) {
  return (
    <span className="inline-flex gap-[2px]" role="img" aria-label="各维度的评级">
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

/** 「按哪个视角着色」的选择条：评级维度，或国家重点领域（节点对该领域的支撑程度）。选择记在本机浏览器里，是个人偏好。 */
export function RateBar() {
  const rateBy = useApp((s) => s.rateBy);
  const setRateBy = useApp((s) => s.setRateBy);
  const levels = rateBy ? lensLevels(rateBy) : [];
  const fields = [...POLICY_SCHEME.fields].sort((a, b) => Number(b.headline) - Number(a.headline));
  const pill = (active: boolean) =>
    `rounded-full px-2.5 py-[3px] text-[12px] font-medium transition-colors ${active ? "bg-accent text-accent-ink" : "bg-surface-2 text-muted hover:text-ink"}`;
  return (
    <div className="mt-2 flex flex-col gap-1.5" role="group" aria-label="按评级或国家重点领域着色">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
        <span className="text-[12px] font-semibold text-muted">着色</span>
        <div className="flex flex-wrap gap-1">
          <button type="button" aria-pressed={rateBy === null} onClick={() => setRateBy(null)} className={pill(rateBy === null)}>
            默认
          </button>
          {RATING_SCHEME.dimensions.map((def) => (
            <button key={def.id} type="button" aria-pressed={rateBy === def.id} title={def.question} onClick={() => setRateBy(def.id)} className={pill(rateBy === def.id)}>
              {def.title}
            </button>
          ))}
        </div>
      </div>
      {fields.length > 0 && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <span className="text-[12px] font-semibold text-muted" title="按节点对国家重点领域的支撑程度着色">国家重点领域</span>
          <div className="flex flex-wrap gap-1">
            {fields.map((field) => (
              <button
                key={field.id}
                type="button"
                aria-pressed={rateBy === fieldKey(field.id)}
                title={field.scope}
                onClick={() => setRateBy(fieldKey(field.id))}
                className={pill(rateBy === fieldKey(field.id))}
              >
                {field.title}
                {field.headline && <span className={`ml-1 text-[10px] ${rateBy === fieldKey(field.id) ? "opacity-80" : "text-faint"}`}>★</span>}
              </button>
            ))}
          </div>
        </div>
      )}
      {rateBy && (
        <div className="flex flex-wrap items-center gap-1.5" aria-label={`${lensTitle(rateBy)}的图例`}>
          {levels.map((lv) => (
            <span key={lv.level} title={lv.criterion} className="inline-flex">
              <LevelBadge dim={rateBy} level={lv.level} />
            </span>
          ))}
          <span className="text-[11px] text-faint">
            {isFieldKey(rateBy) ? "节点对该领域的支撑程度（编辑评估）" : dimDef(rateBy)?.basis === "derived" ? "由内容推导" : "编辑评估"} · {lensQuestion(rateBy)}
          </span>
        </div>
      )}
    </div>
  );
}
