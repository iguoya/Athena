import raw from "@content/earth.json";
import type { AtmosphereLayer, EarthData, InteriorLayer } from "./types";

// JSON 导入的类型断言只做一次：数据结构由 catalog.test.ts 对照 types.ts 核对。
// tuple 字段（经纬度对）在 JSON 推断里是 number[]，需要经过 unknown 中转。
export const data = raw as unknown as EarthData;

/** 场景单位：1 = 地球平均半径（ADR 0128 决策 5）。所有真实长度经它换算，比例关系保持真实。 */
export const EARTH_RADIUS_KM = data.shape.meanRadiusKm;

export function kmToScene(km: number): number {
  return km / EARTH_RADIUS_KM;
}

/** 深度（从地表向下）→ 球半径 */
export function depthToRadiusKm(depthKm: number): number {
  return EARTH_RADIUS_KM - depthKm;
}

export const interiorLayers = data.interior.layers;
export const atmosphereLayers = data.atmosphere.layers;

export function interiorLayerRadii(layer: InteriorLayer): {
  innerSceneR: number;
  outerSceneR: number;
} {
  return {
    innerSceneR: kmToScene(depthToRadiusKm(layer.bottomDepthKm)),
    outerSceneR: kmToScene(depthToRadiusKm(layer.topDepthKm)),
  };
}

/** 大气层壳半径；外逸层上界不封闭，返回 null */
export function atmosphereLayerTopRadius(layer: AtmosphereLayer): number | null {
  if (layer.topHeightKm === null) return null;
  return kmToScene(EARTH_RADIUS_KM + layer.topHeightKm);
}

/** 外逸层的渲染渐隐上界（呈现决定，不是物理值；数据文件 note 已说明上界不封闭） */
export const EXOSPHERE_FADE_KM = 10000;

// ---------- PREM 密度：分段线性内插 ----------

export function densityAt(depthKm: number): number {
  const segments = data.interior.premSegments;
  if (depthKm <= 0) return segments[0].topDensity;
  if (depthKm >= EARTH_RADIUS_KM) {
    const last = segments[segments.length - 1];
    return last.bottomDensity;
  }
  for (const segment of segments) {
    if (depthKm > segment.bottomDepthKm) continue;
    const span = segment.bottomDepthKm - segment.topDepthKm;
    const t = (depthKm - segment.topDepthKm) / span;
    return segment.topDensity + (segment.bottomDensity - segment.topDensity) * t;
  }
  return segments[segments.length - 1].bottomDensity;
}

/** 密度 → viridis 近似色（剖面着色由数据算出来的，ADR 0056）。量程取地球实况 1–13.5 g/cm³。 */
const VIRIDIS_STOPS: [number, number, number, number][] = [
  [0.0, 0x44, 0x01, 0x54],
  [0.25, 0x3b, 0x52, 0x8b],
  [0.5, 0x21, 0x91, 0x8c],
  [0.75, 0x5e, 0xc9, 0x62],
  [1.0, 0xfd, 0xe7, 0x25],
];

export function densityColor(density: number): string {
  const lo = 1;
  const hi = 13.5;
  const t = Math.min(1, Math.max(0, (density - lo) / (hi - lo)));
  let upper = VIRIDIS_STOPS[VIRIDIS_STOPS.length - 1];
  let lower = VIRIDIS_STOPS[0];
  for (let i = 1; i < VIRIDIS_STOPS.length; i++) {
    if (VIRIDIS_STOPS[i][0] >= t) {
      lower = VIRIDIS_STOPS[i - 1];
      upper = VIRIDIS_STOPS[i];
      break;
    }
  }
  const span = upper[0] - lower[0] || 1;
  const k = (t - lower[0]) / span;
  const channel = (a: number, b: number) => Math.round(a + (b - a) * k);
  const r = channel(lower[1], upper[1]);
  const g = channel(lower[2], upper[2]);
  const b = channel(lower[3], upper[3]);
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
}

// ---------- 地球内部温度：界面共识值的线性内插（示意参考，rangeC 是文献区间） ----------

export function interiorTempAt(depthKm: number): number {
  const points = data.interior.tempProfile;
  if (depthKm <= 0) return points[0].tempC;
  for (let i = 1; i < points.length; i++) {
    if (depthKm <= points[i].depthKm) {
      const a = points[i - 1];
      const b = points[i];
      const t = (depthKm - a.depthKm) / (b.depthKm - a.depthKm);
      return a.tempC + (b.tempC - a.tempC) * t;
    }
  }
  return points[points.length - 1].tempC;
}

// ---------- US Standard Atmosphere 1976：分段线性 ----------

export const USSA_MAX_HEIGHT_KM = 86;

export function ussaTempAt(heightKm: number): number {
  const points = data.atmosphere.ussa1976.tempPointsC;
  return interpolateTable(points.map((p) => [p.heightKm, p.tempC]), heightKm);
}

export function ussaPressureAt(heightKm: number): number {
  const points = data.atmosphere.ussa1976.pressurePointsHPa;
  return interpolateTable(points.map((p) => [p.heightKm, p.pressureHPa]), heightKm);
}

function interpolateTable(table: [number, number][], x: number): number {
  if (x <= table[0][0]) return table[0][1];
  for (let i = 1; i < table.length; i++) {
    if (x <= table[i][0]) {
      const [x0, y0] = table[i - 1];
      const [x1, y1] = table[i];
      return y0 + ((y1 - y0) * (x - x0)) / (x1 - x0);
    }
  }
  return table[table.length - 1][1];
}

// ---------- 按位置找层 ----------

export function interiorLayerAtDepth(depthKm: number): InteriorLayer | null {
  return (
    interiorLayers.find(
      (layer) => depthKm >= layer.topDepthKm && depthKm < layer.bottomDepthKm,
    ) ?? null
  );
}

export function atmosphereLayerAtHeight(heightKm: number): AtmosphereLayer | null {
  return (
    atmosphereLayers.find(
      (layer) =>
        heightKm >= layer.bottomHeightKm &&
        (layer.topHeightKm === null || heightKm < layer.topHeightKm),
    ) ?? null
  );
}

// ---------- 源头目录 ----------

export function sourceTitle(sourceId: string): string {
  return data.sources[sourceId]?.title ?? sourceId;
}

export function sourceUrl(sourceId: string): string | undefined {
  return data.sources[sourceId]?.url;
}
