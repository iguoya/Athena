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
      /** 海面：略深偏青（Q1） */
      paint: { "background-color": "#cfd8d4" },
    },
  ],
};

export const MAP_TOKENS = {
  page: "#f3efe6",
  ink: "#2a2118",
  river: "#6a8fa8",
  canal: "#3d6b8c",
  corridor: "#a67c52",
  coast: "#5c4a32",
  /** 中国陆地纸色 */
  landFill: "#ece3d2",
  /** 邻国更淡 */
  neighborLand: "#e4dccb",
  sea: "#cfd8d4",
  territory: "#9a3412",
  highlight: "#c2410c",
  era: "#1e3a5f",
} as const;
