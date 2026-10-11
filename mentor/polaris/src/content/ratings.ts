import polaris from "@content/polaris.json";
import type { Catalog } from "./catalog";
import type {
  PolarisDocument,
  PolarisNode,
  PolicyField,
  PolicyScheme,
  RatingDim,
  RatingDimDef,
  RatingLevelDef,
  RatingScheme,
  Ratings,
  Route,
  Verdict,
} from "./types";

// 评级口径（ADR 0022）唯一来源是内容里的 rating_scheme；这里只读它、不在代码里硬编码维度名与级别名。
const EMPTY: RatingScheme = { as_of: "", note: "", dimensions: [] };
export const RATING_SCHEME: RatingScheme = (polaris as unknown as PolarisDocument).rating_scheme ?? EMPTY;
export const RATING_DIMS: readonly RatingDim[] = RATING_SCHEME.dimensions.map((dim) => dim.id);

/** 等级的颜色变量：五级序列色，两套主题各自取值。颜色之外界面还显示数字与名称，不只靠颜色传达。 */
export const ratingVar = (level: number): string => `var(--rate-${Math.min(5, Math.max(1, Math.round(level)))})`;

// ---- 国家重点领域（ADR 0024） ----
const EMPTY_POLICY: PolicyScheme = { as_of: "", note: "", signal_kinds: [], fit_levels: [], fields: [] };
export const POLICY_SCHEME: PolicyScheme = (polaris as unknown as PolarisDocument).policy_scheme ?? EMPTY_POLICY;
export const FIELD_IDS: readonly string[] = POLICY_SCHEME.fields.map((field) => field.id);

/** 着色视角：评级维度，或「field:<领域 id>」——节点对某个国家重点领域的支撑程度。 */
export type LensKey = RatingDim | `field:${string}`;
export const fieldKey = (id: string): LensKey => `field:${id}`;
export const isFieldKey = (key: string): key is `field:${string}` => key.startsWith("field:");

export function fieldDef(id: string): PolicyField | undefined {
  return POLICY_SCHEME.fields.find((field) => field.id === id);
}

/** 视角的五级定义：领域视角是「1 无关」加上口径里的 2–5 级。 */
export function lensLevels(key: LensKey): RatingLevelDef[] {
  if (isFieldKey(key)) return [{ level: 1, name: "无关", criterion: "与这个领域没有明确关系。" }, ...POLICY_SCHEME.fit_levels];
  return dimDef(key)?.levels ?? [];
}

export function lensTitle(key: LensKey): string {
  return isFieldKey(key) ? (fieldDef(key.slice(6))?.title ?? key) : (dimDef(key)?.title ?? key);
}

export function lensQuestion(key: LensKey): string {
  return isFieldKey(key) ? (fieldDef(key.slice(6))?.scope ?? "") : (dimDef(key)?.question ?? "");
}

/** 节点在某个视角下的等级；没有评级的节点（参考层）返回 undefined，领域视角下未写的按 1。 */
export function lensLevel(node: PolarisNode, key: LensKey): number | undefined {
  if (!node.ratings) return undefined;
  if (isFieldKey(key)) return node.fields?.[key.slice(6)]?.level ?? 1;
  return node.ratings[key]?.level;
}

export function dimDef(dim: RatingDim): RatingDimDef | undefined {
  return RATING_SCHEME.dimensions.find((def) => def.id === dim);
}

export function levelName(dim: LensKey, level: number): string {
  return lensLevels(dim).find((def) => def.level === level)?.name ?? String(level);
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

/** 路线对某个领域的节点均值（未对应的按 1 计）；路线的领域契合等级是它四舍五入的结果，小数用来排序。 */
export function routeFieldMean(catalog: Catalog, route: Route, fid: string): number {
  const ids = new Set(route.stages.flatMap((stage) => stage.nodes));
  let total = 0;
  let count = 0;
  for (const id of ids) {
    const node = catalog.nodeById.get(id);
    if (!node?.ratings) continue;
    total += node.fields?.[fid]?.level ?? 1;
    count += 1;
  }
  return count === 0 ? 1 : total / count;
}

/** 与某个国家重点领域最契合的路线：按契合均值从高到低，同值按推荐等级。 */
export function routesByField(catalog: Catalog, routes: readonly Route[], fid: string, limit = 3): { route: Route; mean: number }[] {
  return routes
    .map((route) => ({ route, mean: routeFieldMean(catalog, route, fid) }))
    .sort(
      (a, b) =>
        b.mean - a.mean ||
        VERDICTS.indexOf(a.route.assessment?.verdict ?? "advanced") - VERDICTS.indexOf(b.route.assessment?.verdict ?? "advanced"),
    )
    .slice(0, limit);
}
