import { priorityRank, stageRank, STAGES } from "./catalog";
import type { PolarisEdge, PolarisMap, Stage } from "./types";

/**
 * 确定性分阶段布局（ADR 0015 决策 3）。同一份内容在任何平台得到同一个位置：
 * 不读字体、不量文字、不用随机数，排序一律带原顺序兜底。
 *
 * 阶段是列，自左向右读：初级 → 中级 → 资深（ADR 0014 决策 5）。列内按「同阶段内的依赖深度」，
 * 再按必要程度，再按原顺序排——先修在上、被依赖者在下，同一列里连线基本只向下走。
 * 旧 Qt 版（legacy-qt）是纵向分层，且阶段内只按必要程度排；其余不变。
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

export interface PlacedColumn {
  stage: Stage;
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
  columns: PlacedColumn[];
  nodes: PlacedNode[];
  byId: Map<string, PlacedNode>;
  edges: PlacedEdge[];
}

export function layoutByStage(map: PolarisMap, metrics: LayoutMetrics = DEFAULT_METRICS): Layout {
  const { nodeWidth: w, nodeHeight: h } = metrics;
  const indexOf = new Map(map.nodes.map((node, index) => [node.id, index]));

  // 1. 按阶段分桶；没有阶段的排最后一桶，与旧版一致。
  const buckets = STAGES.map(() => [] as number[]);
  map.nodes.forEach((node, index) => buckets[stageRank(node.stage)].push(index));

  // 2. 同阶段内的依赖深度。requires 是强先修，且已由契约保证无环。
  const depthOf = new Map<string, number>();
  const depth = (id: string): number => {
    const known = depthOf.get(id);
    if (known !== undefined) return known;
    const node = map.nodes[indexOf.get(id)!];
    let value = 0;
    for (const requiredId of node.requires ?? []) {
      const required = map.nodes[indexOf.get(requiredId) ?? -1];
      if (required && stageRank(required.stage) === stageRank(node.stage)) {
        value = Math.max(value, depth(requiredId) + 1);
      }
    }
    depthOf.set(id, value);
    return value;
  };

  const columns: PlacedColumn[] = [];
  const nodes: PlacedNode[] = [];
  let maxRows = 1;
  buckets.forEach((bucket, stageIndex) => {
    if (bucket.length === 0) return;
    bucket.sort((a, b) => {
      const na = map.nodes[a];
      const nb = map.nodes[b];
      return (
        depth(na.id) - depth(nb.id) ||
        priorityRank(na.priority) - priorityRank(nb.priority) ||
        a - b
      );
    });
    const column = columns.length;
    const x = metrics.padX + column * (w + metrics.columnGap);
    columns.push({ stage: STAGES[stageIndex], index: column, x, width: w, count: bucket.length });
    bucket.forEach((nodeIndex, row) => {
      const node = map.nodes[nodeIndex];
      nodes.push({
        id: node.id,
        x,
        y: metrics.padTop + metrics.headerHeight + row * (h + metrics.rowGap),
        w,
        h,
        column,
        row,
        depth: depth(node.id),
      });
    });
    maxRows = Math.max(maxRows, bucket.length);
  });

  const byId = new Map(nodes.map((node) => [node.id, node]));
  const width = metrics.padX * 2 + columns.length * w + Math.max(0, columns.length - 1) * metrics.columnGap;
  const height =
    metrics.padTop + metrics.headerHeight + maxRows * h + Math.max(0, maxRows - 1) * metrics.rowGap + metrics.padBottom;

  const edges = map.edges.map((edge, index) => routeEdge(edge, index + 1, byId));
  return { width, height, columns, nodes, byId, edges };
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
