import {
  atmosphereLayers,
  densityAt,
  EARTH_RADIUS_KM,
  interiorLayers,
  ussaTempAt,
  USSA_MAX_HEIGHT_KM,
} from "../content/load";
import { useEarth } from "../state/store";

// 两张联动图：大气温度–高度（US Standard Atmosphere 1976，0–86 km）与
// 密度–深度（PREM，0–6371 km）。折线由数据函数采样生成，探针位置画横线。

const WIDTH = 264;
const HEIGHT = 176;
const PAD = { left: 30, right: 8, top: 10, bottom: 22 };

function plotArea() {
  return {
    x0: PAD.left,
    x1: WIDTH - PAD.right,
    y0: PAD.top,
    y1: HEIGHT - PAD.bottom,
  };
}

export function AtmosphereChart() {
  const probeMode = useEarth((s) => s.probeMode);
  const probeKm = useEarth((s) => s.probeKm);
  const { x0, x1, y0, y1 } = plotArea();
  const tempMin = -100;
  const tempMax = 20;
  const xOf = (t: number) => x0 + ((t - tempMin) / (tempMax - tempMin)) * (x1 - x0);
  const yOf = (h: number) => y1 - (h / USSA_MAX_HEIGHT_KM) * (y1 - y0);

  const samples: string[] = [];
  for (let h = 0; h <= USSA_MAX_HEIGHT_KM; h += 1) {
    samples.push(`${h === 0 ? "M" : "L"}${xOf(ussaTempAt(h)).toFixed(1)},${yOf(h).toFixed(1)}`);
  }

  return (
    <figure>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="w-full"
        role="img"
        aria-label="大气温度随高度的变化（US Standard Atmosphere 1976）"
      >
        {/* 分层背景色带 */}
        {atmosphereLayers.map((layer) => {
          const top = layer.topHeightKm === null ? USSA_MAX_HEIGHT_KM : layer.topHeightKm;
          return (
            <rect
              key={layer.id}
              x={x0}
              y={yOf(top)}
              width={x1 - x0}
              height={Math.max(yOf(layer.bottomHeightKm) - yOf(top), 0)}
              fill={layer.colorHint}
              opacity={0.18}
            />
          );
        })}
        <line x1={x0} y1={y1} x2={x1} y2={y1} stroke="#cbd5e1" />
        <line x1={x0} y1={y0} x2={x0} y2={y1} stroke="#cbd5e1" />
        {[0, 20, 40, 60, 86].map((h) => (
          <g key={h}>
            <line x1={x0 - 3} y1={yOf(h)} x2={x0} y2={yOf(h)} stroke="#94a3b8" />
            <text x={x0 - 5} y={yOf(h) + 3} textAnchor="end" fontSize="8" fill="#64748b">
              {h}
            </text>
          </g>
        ))}
        {[-80, -40, 0].map((t) => (
          <g key={t}>
            <line x1={xOf(t)} y1={y1} x2={xOf(t)} y2={y1 + 3} stroke="#94a3b8" />
            <text x={xOf(t)} y={y1 + 12} textAnchor="middle" fontSize="8" fill="#64748b">
              {t}°C
            </text>
          </g>
        ))}
        <path d={samples.join(" ")} fill="none" stroke="#1d5fa8" strokeWidth="1.6" />
        {probeMode === "atmosphere" && probeKm <= USSA_MAX_HEIGHT_KM && (
          <line
            x1={x0}
            y1={yOf(probeKm)}
            x2={x1}
            y2={yOf(probeKm)}
            stroke="#d97706"
            strokeDasharray="3 2"
          />
        )}
      </svg>
      <figcaption className="text-xs text-slate-500">
        温度 – 高度（km），US Standard Atmosphere 1976，适用上限 86 km
      </figcaption>
    </figure>
  );
}

export function InteriorChart() {
  const probeMode = useEarth((s) => s.probeMode);
  const probeKm = useEarth((s) => s.probeKm);
  const { x0, x1, y0, y1 } = plotArea();
  const rhoMin = 2;
  const rhoMax = 14;
  const xOf = (rho: number) => x0 + ((rho - rhoMin) / (rhoMax - rhoMin)) * (x1 - x0);
  const yOf = (depth: number) => y0 + (depth / EARTH_RADIUS_KM) * (y1 - y0);

  // 按段采样：界面处自然出现竖直跳变线（PREM 界面间断的呈现）
  const samples: string[] = [];
  const steps = 200;
  for (let i = 0; i <= steps; i++) {
    const depth = (i / steps) * EARTH_RADIUS_KM;
    samples.push(`${i === 0 ? "M" : "L"}${xOf(densityAt(depth)).toFixed(1)},${yOf(depth).toFixed(1)}`);
  }

  return (
    <figure>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="w-full"
        role="img"
        aria-label="地球内部密度随深度的变化（PREM）"
      >
        {interiorLayers.map((layer) => (
          <rect
            key={layer.id}
            x={x0}
            y={yOf(layer.topDepthKm)}
            width={x1 - x0}
            height={Math.max(yOf(layer.bottomDepthKm) - yOf(layer.topDepthKm), 0)}
            fill={layer.colorHint}
            opacity={0.15}
          />
        ))}
        <line x1={x0} y1={y0} x2={x1} y2={y0} stroke="#cbd5e1" />
        <line x1={x0} y1={y0} x2={x0} y2={y1} stroke="#cbd5e1" />
        {[0, 2891, 5150, 6371].map((d) => (
          <g key={d}>
            <line x1={x0 - 3} y1={yOf(d)} x2={x0} y2={yOf(d)} stroke="#94a3b8" />
            <text x={x0 - 5} y={yOf(d) + 3} textAnchor="end" fontSize="8" fill="#64748b">
              {d}
            </text>
          </g>
        ))}
        {[4, 8, 12].map((rho) => (
          <g key={rho}>
            <line x1={xOf(rho)} y1={y0} x2={xOf(rho)} y2={y0 - 3} stroke="#94a3b8" />
            <text x={xOf(rho)} y={y0 - 5} textAnchor="middle" fontSize="8" fill="#64748b">
              {rho}
            </text>
          </g>
        ))}
        <path d={samples.join(" ")} fill="none" stroke="#b45309" strokeWidth="1.6" />
        {probeMode === "interior" && (
          <line
            x1={x0}
            y1={yOf(probeKm)}
            x2={x1}
            y2={yOf(probeKm)}
            stroke="#d97706"
            strokeDasharray="3 2"
          />
        )}
      </svg>
      <figcaption className="text-xs text-slate-500">
        密度（g/cm³）– 深度（km），PREM 界面值线性内插
      </figcaption>
    </figure>
  );
}

/** 视野宽度估算：真实比例的「尺子」——相机距离（R）× 视场角换算成公里（ADR 0128 决策 5）。 */
export function viewportWidthKm(distanceR: number, fovDeg: number): number {
  return 2 * distanceR * Math.tan((fovDeg * Math.PI) / 360) * EARTH_RADIUS_KM;
}

export function formatKm(km: number): string {
  if (km >= 10000) return `${(km / 10000).toFixed(1)} 万 km`;
  if (km >= 1000) return `${(km / 1000).toFixed(2)} 千 km`;
  return `${Math.round(km)} km`;
}
