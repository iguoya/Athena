/**
 * T-029：路线通行成本——大圆距离 + 有出处的日行程估算。
 * 查不到原文的标「估计，待核对」；里制换算写明朝代。
 */

/** 秦汉一里 ≈ 415.8 m（常用考古/度量史取值，二手） */
export const LI_M_QIN_HAN = 415.8;
/** 唐一里取 535 m（约 530–540 m 中值，二手） */
export const LI_M_TANG = 535;

function liToKm(li: number, metersPerLi: number): number {
  return (li * metersPerLi) / 1000;
}

export type TravelMode =
  | "infantryNormal"
  | "infantryForced"
  | "cavalryTang"
  | "cartTang"
  | "courier"
  | "canalDown"
  | "canalUp";

export type TravelRate = {
  kmPerDay: number;
  label: string;
  /** 界面/注释用；必须写清出处或「估计，待核对」 */
  rangeNote: string;
  /** 有文献依据 vs 仅估计 */
  evidence: "cited" | "estimate";
};

/**
 * 日行程常数。步兵两档按「一舍三十里 / 倍道」；骑、车按《资治通鉴》所记唐制里数换算。
 * 驿传、漕运尚无核到原文，标估计。
 */
export const TRAVEL_RATES: Record<TravelMode, TravelRate> = {
  infantryNormal: {
    kmPerDay: liToKm(30, LI_M_QIN_HAN), // ≈12.47 → 展示约 12.5
    label: "步兵·常规",
    rangeNote:
      "一舍三十里≈12.5 km/日（秦汉里≈415.8 m）。《国语》「古者师行三十里而舍」；《后汉书·虞诩传》「兵法日行不过三十里」。原文待 zcode 核对。",
    evidence: "cited",
  },
  infantryForced: {
    kmPerDay: liToKm(60, LI_M_QIN_HAN), // ≈25
    label: "步兵·倍道",
    rangeNote:
      "倍道约六十里≈25 km/日（秦汉里）。张预注：过六十里为倍道、昼夜不息为兼行（二手转述，待核对）。",
    evidence: "cited",
  },
  cavalryTang: {
    kmPerDay: liToKm(70, LI_M_TANG), // ≈37.5
    label: "骑兵（唐制马）",
    rangeNote:
      "《资治通鉴》记唐制「马日七十里」；唐里≈535 m → 约 37 km/日。二手摘要，待核对原文。",
    evidence: "cited",
  },
  cartTang: {
    kmPerDay: liToKm(30, LI_M_TANG), // ≈16
    label: "车（唐制）",
    rangeNote:
      "《资治通鉴》记唐制「车三十里」；唐里≈535 m → 约 16 km/日。二手摘要，待核对原文。",
    evidence: "cited",
  },
  courier: {
    kmPerDay: 80,
    label: "驿传",
    rangeNote: "估计，待核对（尚无核到军制/驿程原文）。",
    evidence: "estimate",
  },
  canalDown: {
    kmPerDay: 40,
    label: "漕运顺水",
    rangeNote: "估计，待核对。",
    evidence: "estimate",
  },
  canalUp: {
    kmPerDay: 20,
    label: "漕运逆水",
    rangeNote: "估计，待核对。",
    evidence: "estimate",
  },
};

/** 出处条目（给人读；不是精确军制手册） */
export const TRAVEL_RATE_SOURCES = [
  {
    id: "she-30",
    title: "一舍三十里（步兵常规）",
    note: "《国语》师行三十里而舍；《后汉书·虞诩传》兵法日行不过三十里。秦汉里≈415.8 m → ≈12.5 km/日。",
  },
  {
    id: "forced-60",
    title: "倍道（步兵急行）",
    note: "六十里量级≈25 km/日（秦汉里）；与「兼行」区分见兵家注，原文待核对。",
  },
  {
    id: "tang-zizhi",
    title: "唐制马/步/车日行（《资治通鉴》记）",
    note: "马七十里、步及驴五十里、车三十里；唐里≈530–540 m，取 535 m 换算。",
  },
  {
    id: "estimate-pending",
    title: "驿传 / 漕运",
    note: "估计，待核对——尚无核到可引用的原文常数。",
  },
] as const;

const R_EARTH_KM = 6371;

/** 两点大圆距离（km） */
export function haversineKm(
  lon1: number,
  lat1: number,
  lon2: number,
  lat2: number,
): number {
  const toRad = (d: number) => (d * Math.PI) / 180;
  const φ1 = toRad(lat1);
  const φ2 = toRad(lat2);
  const Δφ = toRad(lat2 - lat1);
  const Δλ = toRad(lon2 - lon1);
  const a =
    Math.sin(Δφ / 2) ** 2 +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) ** 2;
  return 2 * R_EARTH_KM * Math.asin(Math.min(1, Math.sqrt(a)));
}

/** 折线累计大圆距离（km） */
export function pathLengthKm(coords: Array<[number, number]>): number {
  let sum = 0;
  for (let i = 1; i < coords.length; i++) {
    const a = coords[i - 1]!;
    const b = coords[i]!;
    sum += haversineKm(a[0], a[1], b[0], b[1]);
  }
  return sum;
}

export type TravelEstimate = {
  km: number;
  /** 一舍三十里 */
  daysInfantryNormal: number;
  /** 倍道 */
  daysInfantryForced: number;
  daysCavalry: number;
  daysCart: number;
  daysCourier: number;
  /** 兼容旧字段：等同倍道天数（勿单独展示为唯一答案） */
  daysInfantry: number;
  summary: string;
};

export function estimateTravel(km: number): TravelEstimate {
  const round1 = (n: number) => Math.round(n * 10) / 10;
  const days = (rate: number) => Math.max(0.1, round1(km / rate));
  const daysInfantryNormal = days(TRAVEL_RATES.infantryNormal.kmPerDay);
  const daysInfantryForced = days(TRAVEL_RATES.infantryForced.kmPerDay);
  const daysCavalry = days(TRAVEL_RATES.cavalryTang.kmPerDay);
  const daysCart = days(TRAVEL_RATES.cartTang.kmPerDay);
  const daysCourier = days(TRAVEL_RATES.courier.kmPerDay);
  const kmR = Math.round(km);
  return {
    km: kmR,
    daysInfantryNormal,
    daysInfantryForced,
    daysCavalry,
    daysCart,
    daysCourier,
    daysInfantry: daysInfantryForced,
    summary: `全程约 ${kmR} 公里 · 步常规约 ${daysInfantryNormal} 天 / 倍道约 ${daysInfantryForced} 天 · 骑约 ${daysCavalry} 天`,
  };
}

export function estimatePath(
  coords: Array<[number, number]>,
): TravelEstimate | null {
  if (coords.length < 2) return null;
  return estimateTravel(pathLengthKm(coords));
}
