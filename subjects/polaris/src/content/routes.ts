import type { Catalog } from "./catalog";
import { layoutColumns, type ColumnSpec, type Layout, type LayoutMetrics, DEFAULT_METRICS } from "./layout";
import type { Discipline, PolarisEdge, PolarisMap, Route, RouteBalance, RouteLens } from "./types";

export const LENSES: readonly RouteLens[] = ["direction", "stack", "artifact"];
export const BALANCES: readonly RouteBalance[] = ["software", "balanced", "hardware"];
/** 界面上的专业类顺序；cross 放最后（ADR 0021）。 */
export const DISCIPLINES: readonly Discipline[] = ["cs", "ei", "ee", "auto", "cross"];

/** 某个专业类的主干阶梯路线 id；cross 的阶梯是通才阶梯，不走这条命名。 */
export const disciplineLadderId = (discipline: Discipline): string => `route.${discipline}-ladder`;

/** 开放地图按专业类分组，保持内容里的顺序；没有地图的专业类不出现。 */
export function mapsByDiscipline(maps: readonly PolarisMap[]): { discipline: Discipline; maps: PolarisMap[] }[] {
  return DISCIPLINES.map((discipline) => ({ discipline, maps: maps.filter((map) => map.discipline === discipline) })).filter(
    (group) => group.maps.length > 0,
  );
}

/** 路线的列就是路线自己的阶段；列内顺序是路线里写的顺序（依赖深度只在同一列内微调）。 */
export function routeColumns(route: Route): ColumnSpec[] {
  return route.stages.map((stage, index) => ({
    key: `${route.id}#${index}`,
    label: stage.title,
    nodeIds: stage.nodes,
  }));
}

/**
 * 路线里能画出来的边：全部地图的边加上跨图关联，两端都在这条路线里的才算。
 * 路线不复制节点，也不复制边，只在已有的依赖上筛一遍（ADR 0016 决策 1）。
 */
export function routeEdges(catalog: Catalog, route: Route): PolarisEdge[] {
  const members = new Set(route.stages.flatMap((stage) => stage.nodes));
  const seen = new Set<string>();
  const edges: PolarisEdge[] = [];
  const all = [...catalog.allMaps.flatMap((map) => map.edges), ...catalog.crossEdges];
  for (const edge of all) {
    if (!members.has(edge.from) || !members.has(edge.to)) continue;
    const key = `${edge.from}\u001f${edge.to}`;
    if (seen.has(key)) continue;
    seen.add(key);
    edges.push(edge);
  }
  return edges;
}

/** 路线的列底部要放「验收」行，比底盘图多留一段高度。 */
export const ROUTE_METRICS: LayoutMetrics = { ...DEFAULT_METRICS, footerHeight: 132 };

export function layoutRoute(catalog: Catalog, route: Route, metrics: LayoutMetrics = ROUTE_METRICS): Layout {
  return layoutColumns(routeColumns(route), catalog.nodeById, routeEdges(catalog, route), metrics);
}

export function routesOfNode(catalog: Catalog, nodeId: string): Route[] {
  return catalog.routes.filter((route) => route.stages.some((stage) => stage.nodes.includes(nodeId)));
}

/** 路线总览的矩阵：行是角度，列是软硬权重。空格子也在，界面据此看出哪里还没有路线。 */
export function routeMatrix(catalog: Catalog, discipline?: Discipline): Record<RouteLens, Record<RouteBalance, Route[]>> {
  const matrix = Object.fromEntries(
    LENSES.map((lens) => [lens, Object.fromEntries(BALANCES.map((balance) => [balance, [] as Route[]]))]),
  ) as Record<RouteLens, Record<RouteBalance, Route[]>>;
  for (const route of catalog.routes) {
    if (discipline && route.discipline !== discipline) continue;
    matrix[route.lens][route.balance].push(route);
  }
  return matrix;
}

export function routeNodeCount(route: Route): number {
  return new Set(route.stages.flatMap((stage) => stage.nodes)).size;
}

/** 一条路线里所有节点的章节总数：路线本身不复制章节，只数它引用的节点（ADR 0019）。 */
export function routeChapterCount(catalog: Catalog, route: Route): number {
  let total = 0;
  for (const id of new Set(route.stages.flatMap((stage) => stage.nodes))) {
    total += catalog.nodeById.get(id)?.chapters?.length ?? 0;
  }
  return total;
}
