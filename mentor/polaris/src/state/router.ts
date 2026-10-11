// 哈希路由：深链接与浏览器后退都靠它。只有三类位置，所以不引入路由库。
//   #/                           总览（路线矩阵）
//   #/route/<routeId>[?node=id]  一条路线
//   #/base/<mapId>[?node=id]     底盘里的一张图

export type Location =
  | { view: "home" }
  | { view: "route"; routeId: string; nodeId?: string }
  | { view: "base"; mapId: string; nodeId?: string };

export const HOME: Location = { view: "home" };

export function formatHash(location: Location): string {
  const enc = encodeURIComponent;
  if (location.view === "home") return "#/";
  const node = location.nodeId ? `?node=${enc(location.nodeId)}` : "";
  return location.view === "route"
    ? `#/route/${enc(location.routeId)}${node}`
    : `#/base/${enc(location.mapId)}${node}`;
}

export function parseHash(hash: string): Location {
  const [path, query = ""] = hash.replace(/^#/, "").split("?");
  const parts = path.split("/").filter(Boolean).map(decodeURIComponent);
  const nodeId = new URLSearchParams(query).get("node") ?? undefined;
  if (parts[0] === "route" && parts[1]) return { view: "route", routeId: parts[1], nodeId };
  if (parts[0] === "base" && parts[1]) return { view: "base", mapId: parts[1], nodeId };
  return HOME;
}

export function sameLocation(a: Location, b: Location): boolean {
  return formatHash(a) === formatHash(b);
}
