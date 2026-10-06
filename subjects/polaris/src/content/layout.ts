import { priorityRank, STAGE_LABEL, stageRank, STAGES } from "./catalog";
import type { PolarisEdge, PolarisMap, PolarisNode, Stage } from "./types";

/**
 * 确定性分阶段布局（ADR 0015 决策 3）。同一份内容在任何平台得到同一个位置：
 * 不读字体、不量文字、不用随机数，排序一律带原顺序兜底。
 *
 * 列是通用的：底盘图的列是阶段（初级 → 中级 → 资深，ADR 0014 决策 5），路线的列是路线自己的阶段
 * （ADR 0016）。列内按「同一列里的依赖深度」排——先修在上、被依赖者在下，同一列里连线基本只向下走；
 * 深度相同的，保持调用方给的顺序（底盘图里是必要程度再原顺序，路线里是路线里写的顺序）。
 * 旧 Qt 版（legacy-qt）是纵向分层，阶段内只按必要程度排；其余不变。
 */
export interface LayoutMetrics {
  nodeWidth: number;
  nodeHeight: number;
  columnGap: number;
  rowGap: number;
  padX: number;
  padTop: number;
  padBottom: number;
  headerHeight: number;
  /** 列底部留给「验收」行的高度；底盘图为 0。 */
  footerHeight: number;
}

export const DEFAULT_METRICS: LayoutMetrics = {
  nodeWidth: 264,
  nodeHeight: 104,
  columnGap: 132,
  rowGap: 20,
  padX: 56,
  padTop: 40,
  padBottom: 56,
  headerHeight: 64,
  footerHeight: 0,
};

export interface PlacedNode {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  column: number;
  row: number;
  /** 同一阶段内的依赖深度：0 表示本阶段内没有先修。 */
  depth: number;
}

export interface ColumnSpec {
  key: string;
  label: string;
  /** 底盘图的列带阶段；路线的列没有。 */
  stage?: Stage;
  nodeIds: string[];
}

export interface PlacedColumn {
  key: string;
  label: string;
  stage?: Stage;
  index: number;
  x: number;
  width: number;
  count: number;
}

export interface PlacedEdge {
  edge: PolarisEdge;
  /** 从 1 开始的航标编号，沿用旧版：点编号可以看这条边的理由。 */
  number: number;
  /** SVG 路径。 */
  path: string;
  /** 编号标记的位置：三次贝塞尔的中点。 */
  mid: { x: number; y: number };
  direction: "forward" | "same" | "back";
}

export interface Layout {
  width: number;
  height: number;
  /** 最高那一列的底边；验收行从这里往下放。 */
  contentBottom: number;
  metrics: LayoutMetrics;
  columns: PlacedColumn[];
  nodes: PlacedNode[];
  byId: Map<string, PlacedNode>;
  edges: PlacedEdge[];
}

/** 底盘图：阶段是列；阶段内先按必要程度、再按原顺序给出初始顺序，之后由依赖深度稳定重排。 */
export function layoutByStage(map: PolarisMap, metrics: LayoutMetrics = DEFAULT_METRICS): Layout {
  // 1. 按阶段分桶；没有阶段的排最后一桶，与旧版一致。
  const buckets = STAGES.map(() => [] as number[]);
  map.nodes.forEach((node, index) => buckets[stageRank(node.stage)].push(index));
  const columns: ColumnSpec[] = [];
  buckets.forEach((bucket, stageIndex) => {
    if (bucket.length === 0) return;
    bucket.sort(
      (a, b) => priorityRank(map.nodes[a].priority) - priorityRank(map.nodes[b].priority) || a - b,
    );
    columns.push({
      key: STAGES[stageIndex],
      label: STAGE_LABEL[STAGES[stageIndex]],
      stage: STAGES[stageIndex],
      nodeIds: bucket.map((index) => map.nodes[index].id),
    });
  });
  return layoutColumns(columns, new Map(map.nodes.map((node) => [node.id, node])), map.edges, metrics);
}

/**
 * 通用按列布局。`nodes` 要包含 columns 里出现的全部节点；`edges` 里两端不都在列里的边会被忽略，
 * 这样路线可以把全部地图的边一股脑交进来。
 */
export function layoutColumns(
  columns: ColumnSpec[],
  nodes: Map<string, PolarisNode>,
  edges: PolarisEdge[],
  metrics: LayoutMetrics = DEFAULT_METRICS,
): Layout {
  const { nodeWidth: w, nodeHeight: h } = metrics;
  const columnOf = new Map<string, number>();
  columns.forEach((column, index) => column.nodeIds.forEach((id) => columnOf.set(id, index)));

  // 同一列内的依赖深度。requires 是强先修，且已由契约保证无环。
  const depthOf = new Map<string, number>();
  const depth = (id: string): number => {
    const known = depthOf.get(id);
    if (known !== undefined) return known;
    let value = 0;
    for (const requiredId of nodes.get(id)?.requires ?? []) {
      if (columnOf.get(requiredId) !== undefined && columnOf.get(requiredId) === columnOf.get(id)) {
        value = Math.max(value, depth(requiredId) + 1);
      }
    }
    depthOf.set(id, value);
    return value;
  };

  const placedColumns: PlacedColumn[] = [];
  const placed: PlacedNode[] = [];
  let maxRows = 1;
  columns.forEach((column, index) => {
    // Array.prototype.sort 是稳定的：深度相同保持调用方给的顺序。
    const ordered = [...column.nodeIds].sort((a, b) => depth(a) - depth(b));
    const x = metrics.padX + index * (w + metrics.columnGap);
    placedColumns.push({ key: column.key, label: column.label, stage: column.stage, index, x, width: w, count: ordered.length });
    ordered.forEach((id, row) => {
      placed.push({
        id,
        x,
        y: metrics.padTop + metrics.headerHeight + row * (h + metrics.rowGap),
        w,
        h,
        column: index,
        row,
        depth: depth(id),
      });
    });
    maxRows = Math.max(maxRows, ordered.length);
  });

  const byId = new Map(placed.map((node) => [node.id, node]));
  const width = metrics.padX * 2 + columns.length * w + Math.max(0, columns.length - 1) * metrics.columnGap;
  const contentBottom =
    metrics.padTop + metrics.headerHeight + maxRows * h + Math.max(0, maxRows - 1) * metrics.rowGap;
  const height = contentBottom + metrics.footerHeight + metrics.padBottom;

  const routed = edges
    .filter((edge) => byId.has(edge.from) && byId.has(edge.to))
    .map((edge, index) => routeEdge(edge, index + 1, byId));
  return { width, height, contentBottom, metrics, columns: placedColumns, nodes: placed, byId, edges: routed };
}

function routeEdge(edge: PolarisEdge, number: number, byId: Map<string, PlacedNode>): PlacedEdge {
  const from = byId.get(edge.from);
  const to = byId.get(edge.to);
  if (!from || !to) throw new Error(`边 ${edge.from} → ${edge.to} 的端点不在这张图里`);

  const y1 = from.y + from.h / 2;
  const y2 = to.y + to.h / 2;
  let p0: [number, number];
  let p1: [number, number];
  let p2: [number, number];
  let p3: [number, number];
  let direction: PlacedEdge["direction"];

  if (to.column > from.column) {
    // 向右：从来源右侧出，进目标左侧。
    direction = "forward";
    const x1 = from.x + from.w;
    const x2 = to.x;
    const dx = Math.max(48, (x2 - x1) / 2);
    p0 = [x1, y1];
    p1 = [x1 + dx, y1];
    p2 = [x2 - dx, y2];
    p3 = [x2, y2];
  } else if (to.column === from.column) {
    // 同列：都走右侧，绕出去再回来，避免穿过卡片。
    direction = "same";
    const x = from.x + from.w;
    const bulge = 44 + Math.min(40, Math.abs(to.row - from.row) * 6);
    p0 = [x, y1];
    p1 = [x + bulge, y1];
    p2 = [x + bulge, y2];
    p3 = [x, y2];
  } else {
    // 向左（虚线来路可能从高阶段指回低阶段）：从来源左侧出，进目标右侧。
    direction = "back";
    const x1 = from.x;
    const x2 = to.x + to.w;
    const dx = Math.max(48, (x1 - x2) / 2);
    p0 = [x1, y1];
    p1 = [x1 - dx, y1];
    p2 = [x2 + dx, y2];
    p3 = [x2, y2];
  }

  const path = `M ${p0[0]} ${p0[1]} C ${p1[0]} ${p1[1]}, ${p2[0]} ${p2[1]}, ${p3[0]} ${p3[1]}`;
  const mid = { x: (p0[0] + 3 * p1[0] + 3 * p2[0] + p3[0]) / 8, y: (p0[1] + 3 * p1[1] + 3 * p2[1] + p3[1]) / 8 };
  return { edge, number, path, mid, direction };
}
