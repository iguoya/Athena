import type { Catalog } from "@/content/catalog";
import type { Location } from "./router";

/**
 * 跳到一个节点，选最贴近当前上下文的去处：
 * - 在路线里且这个节点也在这条路线里：留在路线，只换选中；
 * - 否则去它所在的开放地图；节点在参考层（地图不开放）时返回 null，界面不提供跳转。
 */
export function locationForNode(catalog: Catalog, current: Location, nodeId: string): Location | null {
  if (current.view === "route") {
    const route = catalog.routes.find((r) => r.id === current.routeId);
    if (route?.stages.some((stage) => stage.nodes.includes(nodeId))) return { ...current, nodeId };
  }
  if (current.view === "base") {
    const mapId = catalog.mapIdOfNode.get(nodeId);
    if (mapId === current.mapId) return { ...current, nodeId };
  }
  const mapId = catalog.mapIdOfNode.get(nodeId);
  if (!mapId || !catalog.isOpenMap(mapId)) return null;
  return { view: "base", mapId, nodeId };
}
