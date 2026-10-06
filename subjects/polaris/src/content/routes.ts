import type { Catalog } from "./catalog";
import { layoutColumns, type ColumnSpec, type Layout, type LayoutMetrics, DEFAULT_METRICS } from "./layout";
import type { PolarisEdge, Route, RouteBalance, RouteLens } from "./types";

export const LENSES: readonly RouteLens[] = ["direction", "stack", "artifact"];
export const BALANCES: readonly RouteBalance[] = ["software", "balanced", "hardware"];

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
export function routeMatrix(catalog: Catalog): Record<RouteLens, Record<RouteBalance, Route[]>> {
  const matrix = Object.fromEntries(
    LENSES.map((lens) => [lens, Object.fromEntries(BALANCES.map((balance) => [balance, [] as Route[]]))]),
  ) as Record<RouteLens, Record<RouteBalance, Route[]>>;
  for (const route of catalog.routes) matrix[route.lens][route.balance].push(route);
  return matrix;
}

export function routeNodeCount(route: Route): number {
  return new Set(route.stages.flatMap((stage) => stage.nodes)).size;
}
