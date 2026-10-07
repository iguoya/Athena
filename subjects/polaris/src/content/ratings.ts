import polaris from "@content/polaris.json";
import type { Catalog } from "./catalog";
import type { PolarisDocument, RatingDim, RatingDimDef, RatingScheme, Ratings, Route, Verdict } from "./types";

// 评级口径（ADR 0022）唯一来源是内容里的 rating_scheme；这里只读它、不在代码里硬编码维度名与级别名。
const EMPTY: RatingScheme = { as_of: "", note: "", dimensions: [] };
export const RATING_SCHEME: RatingScheme = (polaris as unknown as PolarisDocument).rating_scheme ?? EMPTY;
export const RATING_DIMS: readonly RatingDim[] = RATING_SCHEME.dimensions.map((dim) => dim.id);

/** 等级的颜色变量：五级序列色，两套主题各自取值。颜色之外界面还显示数字与名称，不只靠颜色传达。 */
export const ratingVar = (level: number): string => `var(--rate-${Math.min(5, Math.max(1, Math.round(level)))})`;

export function dimDef(dim: RatingDim): RatingDimDef | undefined {
  return RATING_SCHEME.dimensions.find((def) => def.id === dim);
}

export function levelName(dim: RatingDim, level: number): string {
  return dimDef(dim)?.levels.find((def) => def.level === level)?.name ?? String(level);
}

/** 评级里的强项（≥4 级）与弱项（≤2 级），按维度顺序；路线的强项弱项就是它所含知识的强项弱项。 */
export function strongAndWeak(ratings: Ratings | undefined): { strong: RatingDim[]; weak: RatingDim[] } {
  const strong: RatingDim[] = [];
  const weak: RatingDim[] = [];
  if (!ratings) return { strong, weak };
  for (const dim of RATING_DIMS) {
    const level = ratings[dim]?.level;
    if (level === undefined) continue;
    if (level >= 4) strong.push(dim);
    else if (level <= 2) weak.push(dim);
  }
  return { strong, weak };
}

/** 推荐等级的显示顺序：优先推荐在前，进阶在后（ADR 0022 决策 7）。 */
export const VERDICTS: readonly Verdict[] = ["priority", "recommended", "optional", "advanced"];

export const VERDICT_LABEL: Record<Verdict, string> = {
  priority: "优先推荐",
  recommended: "推荐",
  optional: "可选",
  advanced: "进阶",
};

export const VERDICT_HINT: Record<Verdict, string> = {
  priority: "需求高、验证客观、门槛适中，适合作为方向的起点",
  recommended: "值得走，但有明确的前置或条件",
  optional: "按兴趣或场景选，不是多数人的首选",
  advanced: "有明确前置，不宜作起点",
};

export const verdictVar = (verdict: Verdict): string =>
  verdict === "priority" ? "var(--gold)" : verdict === "recommended" ? "var(--accent)" : verdict === "optional" ? "var(--faint)" : "var(--stage-senior)";

export function routesByVerdict(routes: readonly Route[]): Record<Verdict, Route[]> {
  const result: Record<Verdict, Route[]> = { priority: [], recommended: [], optional: [], advanced: [] };
  for (const route of routes) if (route.assessment) result[route.assessment.verdict].push(route);
  return result;
}

/** 路线在某个维度上的节点均值（去重后的算术平均）；路线的评级等级就是它四舍五入的结果，这里留着小数用来排序。 */
export function routeDimMean(catalog: Catalog, route: Route, dim: RatingDim): number {
  const ids = new Set(route.stages.flatMap((stage) => stage.nodes));
  const levels: number[] = [];
  for (const id of ids) {
    const level = catalog.nodeById.get(id)?.ratings?.[dim]?.level;
    if (level !== undefined) levels.push(level);
  }
  return levels.length === 0 ? 0 : levels.reduce((sum, level) => sum + level, 0) / levels.length;
}

/** 技术前景最好的方向：路线的技术前景汇总评级 ≥4，按均值从高到低，同值按推荐等级（ADR 0023 决策 6）。只是已有评级的另一种排列。 */
export function routesByOutlook(catalog: Catalog, routes: readonly Route[]): { route: Route; mean: number }[] {
  return routes
    .filter((route) => (route.ratings?.outlook?.level ?? 0) >= 4)
    .map((route) => ({ route, mean: routeDimMean(catalog, route, "outlook") }))
    .sort(
      (a, b) =>
        b.mean - a.mean ||
        VERDICTS.indexOf(a.route.assessment?.verdict ?? "advanced") - VERDICTS.indexOf(b.route.assessment?.verdict ?? "advanced"),
    );
}
