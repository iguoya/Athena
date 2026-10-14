/** MapLibre 纸本墨线底图（无外网字形 / 栅格）。陆/海/邻国面由应用叠 Source。
 * 地名用 DOM Marker + 碰撞，不依赖 glyphs（ADR 0157 离线；T-003/T-018）。
 */
export const PAPER_STYLE = {
  version: 8 as const,
  name: "athena-paper",
  sources: {},
  layers: [
    {
      id: "background",
      type: "background" as const,
      /** 海面：青蓝（T-019） */
      paint: { "background-color": "#a9c7cc" },
    },
  ],
};

export const MAP_TOKENS = {
  page: "#f3efe6",
  ink: "#2a2118",
  river: "#4f86a6",
  canal: "#2f6f8f",
  corridor: "#a67c52",
  coast: "#5c4a32",
  /** 中国陆地纸色（彩色地形之下的底） */
  landFill: "#ece3d2",
  /** 邻国更淡 */
  neighborLand: "#e4dccb",
  sea: "#a9c7cc",
  lake: "#a7cbd6",
  lakeLine: "#6b9bb0",
  countryLine: "#8b7d6b",
  territory: "#9a3412",
  highlight: "#c2410c",
  era: "#1e3a5f",
} as const;

/** 政权主色：同一势力跨快照一致（T-019） */
export const POWER_COLORS: Record<string, string> = {
  秦: "#b5483a",
  汉: "#e08a3c",
  西汉: "#e08a3c",
  东汉: "#d47830",
  魏: "#4f78b5",
  蜀: "#5f9e6e",
  吴: "#d1a93b",
  唐: "#c2564f",
  宋: "#8d63a8",
  北宋: "#8d63a8",
  南宋: "#7a5496",
  辽: "#3e8f9e",
  契丹: "#3e8f9e",
  金: "#d0a53e",
  西夏: "#7ea35a",
  大理: "#cf6f9a",
  南诏: "#cf6f9a",
  吐蕃: "#9a7d5b",
  乌斯藏: "#9a7d5b",
  匈奴: "#a98a5a",
  鲜卑: "#8f9a5a",
  柔然: "#b79a6a",
  回纥: "#a98a5a",
  蒙古: "#8f9a5a",
  蒙古诸部: "#8f9a5a",
  元: "#3f6fa8",
  明: "#b8423f",
  清: "#e0b13c",
  高丽: "#5a8f7a",
  陈朝: "#c4895a",
  渤海: "#4a7a9a",
};

const POWER_PALETTE = [
  "#b5483a",
  "#e08a3c",
  "#4f78b5",
  "#5f9e6e",
  "#d1a93b",
  "#c2564f",
  "#8d63a8",
  "#3e8f9e",
  "#d0a53e",
  "#7ea35a",
  "#cf6f9a",
  "#9a7d5b",
  "#a98a5a",
  "#3f6fa8",
  "#b8423f",
  "#e0b13c",
] as const;

/** 势力名 → 颜色；未登记则按名哈希取色盘 */
export function powerColor(power: string | undefined | null, fallback?: string): string {
  const name = (power ?? "").trim();
  if (!name) return fallback ?? MAP_TOKENS.territory;
  if (POWER_COLORS[name]) return POWER_COLORS[name]!;
  for (const [key, color] of Object.entries(POWER_COLORS)) {
    if (name.includes(key) || key.includes(name)) return color;
  }
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return POWER_PALETTE[h % POWER_PALETTE.length]!;
}

/** 同色系更深一档，作疆域边线 */
export function powerEdgeColor(fill: string, factor = 0.72): string {
  const m = /^#([0-9a-f]{6})$/i.exec(fill.trim());
  if (!m) return fill;
  const n = parseInt(m[1]!, 16);
  const r = Math.round(((n >> 16) & 255) * factor);
  const g = Math.round(((n >> 8) & 255) * factor);
  const b = Math.round((n & 255) * factor);
  return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1)}`;
}
