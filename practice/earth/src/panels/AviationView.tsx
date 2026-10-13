import { useMemo, useState } from "react";
import {
  atmosphereLayers,
  data,
  KEYPOINT_CATEGORY_NAMES,
  KEYPOINT_COLORS,
  sourceTitle,
  sourceUrl,
} from "../content/load";
import { openExternal } from "../ui/external";
import { useEarth } from "../state/store";

/**
 * 航空视角：0–50 km 的海拔剖面专题视图（不受 3D 场景比例束缚）。
 * 真实比例下 50 km 只是地球半径的 0.8%，3D 全球视图里挤在地表一圈；
 * 这里用分段比例尺把 0–12 km（飞行事务最密集的对流层）放大呈现，
 * 分界处显著标注放大系数——「真实比例」的诚实口径不丢。
 * 呈现范式取自 NOAA/UCAR 的大气分层教育信息图：层带背景 + 高度刻度 +
 * 对象按高度左右交替排图标（人造物右、自然物左，与 3D 场景的标尺分列一致）。
 */

// 纵向分段比例尺：0–12 km → 360px（30 px/km），12–50 km → 180px（4.74 px/km）。
const SEG_MAGNIFY = 30 / (180 / 38);
const GROUND_Y = 650;
const TOP_Y = 110;

function heightToY(km: number): number {
  if (km <= 12) return GROUND_Y - (km / 12) * (GROUND_Y - 290);
  return 290 - ((km - 12) / 38) * (290 - TOP_Y);
}

const MIN_GAP = 26;

interface Mark {
  name: string;
  heightKm: number;
  icon?: string;
  note: string;
  category?: string;
  country?: string;
  sourceIds?: string[];
}

/** 同侧条目从低到高排布，相邻间距不足 MIN_GAP 时向上顺延（3D 标尺同款策略）；
    最矮的条目也不压到海平面线上。 */
function layoutSide(entries: Mark[], toY: (km: number) => number): (Mark & { y: number })[] {
  const sorted = [...entries].sort((a, b) => toY(b.heightKm) - toY(a.heightKm));
  let prev = Number.POSITIVE_INFINITY;
  return sorted.map((mark) => {
    const y = Math.min(toY(mark.heightKm), prev - MIN_GAP, GROUND_Y - 22);
    prev = y;
    return { ...mark, y };
  });
}

export function AviationView() {
  const points = useMemo(
    () => data.atmosphere.keyPoints.filter((p) => p.heightKm <= 50),
    [],
  );
  const left = useMemo(
    () =>
      layoutSide(
        points.filter(
          (p) => !(p.category === "aircraft" || p.category === "spacecraft"),
        ),
        heightToY,
      ),
    [points],
  );
  const right = useMemo(
    () =>
      layoutSide(
        points.filter(
          (p) => p.category === "aircraft" || p.category === "spacecraft",
        ),
        heightToY,
      ),
    [points],
  );

  const selectedLayerId = useEarth((s) => s.selectedLayerId);
  const [selectedName, setSelectedName] = useState<string | null>(null);
  const selected = points.find((p) => p.name === selectedName) ?? null;

  const ticks: number[] = [];
  for (let km = 0; km <= 50; km += 5) ticks.push(km);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-800/60 px-4 py-1.5 text-xs text-slate-400">
        航空视角 · 0–50 km 的空中事务 —— 0–12 km 放大 {SEG_MAGNIFY.toFixed(1)}×
        （对流层内容密集），12–50 km 线性；真实比例下 50 km 仅为地球半径的 0.8%。
        点条目看详情。
      </div>
      <div className="min-h-0 flex-1">
        <svg viewBox="0 0 940 700" className="h-full w-full" role="img" aria-label="航空视角海拔剖面图">
          {/* 层带背景 */}
          {atmosphereLayers.slice(0, 2).map((layer) => {
            const yBottom = heightToY(layer.bottomHeightKm);
            const yTop = heightToY(layer.topHeightKm ?? 50);
            const highlighted = selectedLayerId === layer.id;
            return (
              <g key={layer.id}>
                <rect
                  x={110}
                  y={yTop}
                  width={790}
                  height={yBottom - yTop}
                  fill={layer.colorHint}
                  opacity={highlighted ? 0.34 : 0.16}
                />
                {highlighted && (
                  <rect
                    x={110}
                    y={yTop}
                    width={790}
                    height={yBottom - yTop}
                    fill="none"
                    stroke={layer.colorHint}
                    strokeWidth={2}
                  />
                )}
                <text x={122} y={yBottom - 12} fill="#cbd5e1" fontSize={15} fontWeight={600}>
                  {layer.name} {layer.bottomHeightKm}–{layer.topHeightKm} km
                </text>
              </g>
            );
          })}
          {/* 高度刻度线 */}
          {ticks.map((km) => (
            <g key={km}>
              <line
                x1={110}
                y1={heightToY(km)}
                x2={900}
                y2={heightToY(km)}
                stroke="#94a3b8"
                strokeOpacity={0.18}
                strokeDasharray={km % 10 === 0 ? "none" : "2 6"}
              />
              <text x={100} y={heightToY(km) + 4} fill="#94a3b8" fontSize={11} textAnchor="end">
                {km}
              </text>
            </g>
          ))}
          {/* 层界虚线与 12 km 放大标记 */}
          <line x1={110} y1={290} x2={900} y2={290} stroke="#e2e8f0" strokeOpacity={0.5} strokeDasharray="6 4" />
          <text x={893} y={284} fill="#e2e8f0" fontSize={11} textAnchor="end">
            ↑ 以上比例缩小 {SEG_MAGNIFY.toFixed(1)}×
          </text>
          {/* 地表 */}
          <line x1={110} y1={GROUND_Y} x2={900} y2={GROUND_Y} stroke="#a7f3d0" strokeWidth={2} />
          <text x={116} y={GROUND_Y + 16} fill="#a7f3d0" fontSize={11}>
            海平面
          </text>
          {/* 居民条目：左 = 自然物与现象，右 = 人造物 */}
          {(
            [
              [left, 470, "end", -10],
              [right, 530, "start", 10],
            ] as const
          ).map(([entries, anchorX, anchor, dotDx]) =>
            entries.map((mark) => {
              const active = selectedName === mark.name;
              return (
                <g
                  key={mark.name}
                  onClick={() => setSelectedName(active ? null : mark.name)}
                  className="cursor-pointer"
                >
                  <line
                    x1={anchorX + dotDx}
                    y1={mark.y}
                    x2={505 + dotDx}
                    y2={mark.y}
                    stroke={KEYPOINT_COLORS[mark.category ?? "phenomenon"]}
                    strokeOpacity={active ? 0.9 : 0.35}
                  />
                  <circle
                    cx={505}
                    cy={heightToY(mark.heightKm)}
                    r={active ? 4 : 2.5}
                    fill={KEYPOINT_COLORS[mark.category ?? "phenomenon"]}
                  />
                  <text
                    x={anchorX}
                    y={mark.y + 4}
                    textAnchor={anchor}
                    fontSize={13}
                    fill={active ? "#f8fafc" : "#dbe4f0"}
                  >
                    {mark.icon} {mark.name}
                    <tspan fill="#94a3b8" fontSize={11}>
                      {" "}
                      · {mark.heightKm} km
                    </tspan>
                  </text>
                </g>
              );
            }),
          )}
        </svg>
      </div>
      {/* 选中详情条 */}
      <div className="min-h-[64px] border-t border-slate-800/60 px-4 py-2 text-xs">
        {selected ? (
          <div>
            <span className="text-sm font-semibold text-slate-100">
              {selected.icon} {selected.name}
            </span>
            <span className="ml-2 rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">
              {KEYPOINT_CATEGORY_NAMES[selected.category ?? "phenomenon"]}
              {selected.country ? ` · ${selected.country}` : ""}
            </span>
            <span className="ml-2 tabular-nums text-slate-400">{selected.heightKm} km</span>
            <p className="mt-1 leading-relaxed text-slate-400">{selected.note}</p>
            {selected.sourceIds && (
              <div className="mt-1 flex gap-3">
                {selected.sourceIds.map((id) => (
                  <button
                    key={id}
                    onClick={() => {
                      const url = sourceUrl(id);
                      if (url) void openExternal(url);
                    }}
                    className="text-sky-500 underline decoration-dotted hover:text-sky-300"
                    title={sourceTitle(id)}
                  >
                    出处：{id}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <p className="text-slate-500">
            点击图中条目查看详情。左列自然物与现象，右列人造飞行器；图标含义与 3D
            场景一致。
          </p>
        )}
      </div>
    </div>
  );
}
