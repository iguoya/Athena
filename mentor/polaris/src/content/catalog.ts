import type {
  PolarisDocument,
  PolarisEdge,
  PolarisMap,
  PolarisNode,
  Priority,
  Principle,
  Route,
  Source,
  Stage,
  ViewKind,
} from "./types";

/**
 * 开放地图：界面里可以打开的底盘（ADR 0012、ADR 0016 决策 3）。
 * 其余的 career / engineering / target 是参考层，一个节点也不删，但不进界面、不被路线引用。
 * scripts/contract.py 里有同一份定义，改这里要同步改那里。
 */
export const OPEN_VIEW_KINDS: readonly ViewKind[] = ["academic", "codesign", "frontier"];

export const STAGES: readonly Stage[] = ["junior", "intermediate", "senior"];

export const STAGE_LABEL: Record<Stage, string> = {
  junior: "初级",
  intermediate: "中级",
  senior: "资深",
};

const PRIORITY_RANK: Record<Priority, number> = { essential: 0, important: 1, optional: 2 };

/** 与 C++ 的 stageRank 同一约定：没有阶段的节点排在最后。 */
export function stageRank(stage: Stage | undefined): number {
  const index = stage ? STAGES.indexOf(stage) : -1;
  return index < 0 ? STAGES.length - 1 : index;
}

export function priorityRank(priority: Priority | undefined): number {
  return priority ? PRIORITY_RANK[priority] : PRIORITY_RANK.optional;
}

export interface CrossLink {
  edge: PolarisEdge;
  /** 对端节点 id 与所在地图 id；对端所在地图不开放时，界面不提供跳转。 */
  peerId: string;
  peerMapId: string;
  incoming: boolean;
}

export interface Catalog {
  title: string;
  subtitle: string;
  /** 全部地图，保持内容里的顺序（参考层也在，内容不删）。 */
  allMaps: PolarisMap[];
  /** 开放地图。 */
  maps: PolarisMap[];
  /** 顶层跨图关联：两端落在不同图里的先修与来路。 */
  crossEdges: PolarisEdge[];
  routes: Route[];
  principles: Principle[];
  sources: Map<string, Source>;
  nodeById: Map<string, PolarisNode>;
  mapIdOfNode: Map<string, string>;
  isOpenMap(mapId: string): boolean;
  /** 某节点在跨图关联里的另一端，用于「顺着先修跳到别的图」。 */
  crossLinks(nodeId: string): CrossLink[];
  /** 入边（谁是它的来路 / 先修）与出边（它为谁铺路），限同一张图内。 */
  edgesOf(nodeId: string): { inbound: PolarisEdge[]; outbound: PolarisEdge[] };
}

export function buildCatalog(document: PolarisDocument, sources: Source[]): Catalog {
  const nodeById = new Map<string, PolarisNode>();
  const mapIdOfNode = new Map<string, string>();
  for (const map of document.maps) {
    for (const node of map.nodes) {
      nodeById.set(node.id, node);
      mapIdOfNode.set(node.id, map.id);
    }
  }

  const maps = document.maps.filter((map) => OPEN_VIEW_KINDS.includes(map.view_kind));
  const openIds = new Set(maps.map((map) => map.id));

  const inbound = new Map<string, PolarisEdge[]>();
  const outbound = new Map<string, PolarisEdge[]>();
  for (const map of document.maps) {
    for (const edge of map.edges) {
      (outbound.get(edge.from) ?? outbound.set(edge.from, []).get(edge.from)!).push(edge);
      (inbound.get(edge.to) ?? inbound.set(edge.to, []).get(edge.to)!).push(edge);
    }
  }

  return {
    title: document.title,
    subtitle: document.subtitle,
    allMaps: document.maps,
    maps,
    crossEdges: document.cross_edges,
    routes: document.routes ?? [],
    principles: document.principles ?? [],
    sources: new Map(sources.map((source) => [source.id, source])),
    nodeById,
    mapIdOfNode,
    isOpenMap: (mapId) => openIds.has(mapId),
    crossLinks(nodeId) {
      const links: CrossLink[] = [];
      for (const edge of document.cross_edges) {
        if (edge.from === nodeId || edge.to === nodeId) {
          const incoming = edge.to === nodeId;
          const peerId = incoming ? edge.from : edge.to;
          links.push({ edge, peerId, peerMapId: mapIdOfNode.get(peerId) ?? "", incoming });
        }
      }
      return links;
    },
    edgesOf: (nodeId) => ({ inbound: inbound.get(nodeId) ?? [], outbound: outbound.get(nodeId) ?? [] }),
  };
}
