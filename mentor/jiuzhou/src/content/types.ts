export interface NameSpan {
  from: number;
  to?: number;
  name: string;
  also?: string[];
}

export interface Place {
  id: string;
  modern: string;
  lon: number;
  lat: number;
  tier: "capital" | "metropolis" | "pass" | "prefecture" | "other";
  /** 地理角色一句：为何在图上重要。 */
  role?: string;
  names: NameSpan[];
}

export interface Era {
  id: string;
  title: string;
  from: number;
  to: number;
  blurb: string;
  territoryId?: string;
}

export interface EventCompare {
  label: string;
  beforeYear: number;
  afterYear: number;
}

/** ADR 0001 事件类型枚举（中文）。 */
export type EventKind =
  | "政治"
  | "军事"
  | "经济"
  | "文化"
  | "科技"
  | "灾害"
  | "民族";

export interface EventItem {
  id: string;
  eraId: string;
  year: number;
  placeId: string;
  /** 多地点：首项须等于 placeId */
  placeIds?: string[];
  title: string;
  dynastyTag?: string;
  people: string[];
  personIds?: string[];
  /** 政治 / 军事 / 经济 / 文化 / 科技 / 灾害 / 民族 */
  kind?: EventKind;
  /** 一句话钩子，≤40 字（ADR 0001） */
  lede?: string;
  summary: string;
  impact: string;
  /** 地理因果（侧栏「地理说明」；highlights.why 可作补充） */
  geoWhy?: string;
  leadsTo: string[];
  /** 行军/事件折线 [lon, lat][] */
  route?: [number, number][];
  /** 杨利辉式模块提亮：相关地点 */
  highlightPlaceIds?: string[];
  /** 前后对照（如幽云） */
  compare?: EventCompare;
}

export interface Person {
  id: string;
  name: string;
  years?: string;
  blurb?: string;
  /** 别名（如刘邦→汉高祖刘邦），搜索与人物页共用 */
  aliases?: string[];
}

/** 七类事件配色（纸本低饱和） */
export const EVENT_KINDS = [
  "政治",
  "军事",
  "经济",
  "文化",
  "科技",
  "灾害",
  "民族",
] as const satisfies readonly EventKind[];

export const KIND_COLORS: Record<EventKind, string> = {
  政治: "#5c4a32",
  军事: "#8b4513",
  经济: "#6b7c5c",
  文化: "#6a5a7a",
  科技: "#4a6b7c",
  灾害: "#7a5a48",
  民族: "#5a6b5c",
};

export interface Atlas {
  eras: Era[];
  places: Place[];
  events: EventItem[];
  people: Person[];
}

/** features.json：会生长的地理要素（黄河改道、运河段、长城、工程）。 */
export type FeatureGroup = "yellow-river" | "canal" | "wall" | "works" | string;

export interface GeoFeature {
  id: string;
  group: FeatureGroup;
  name: string;
  from: number;
  to?: number;
  note: string;
  geometry: {
    type: "LineString";
    coordinates: [number, number][];
  };
}

export interface FeaturesDoc {
  features: GeoFeature[];
}

/** routes.json：行军/出使等，waypoints 按 year 逐段画出。 */
export type RouteKind =
  | "expedition"
  | "voyage"
  | "migration"
  | "campaign"
  | "flight"
  | string;

export interface RouteWaypoint {
  label: string;
  lon: number;
  lat: number;
  year?: number;
  placeId?: string;
}

export interface MarchRoute {
  id: string;
  group: string;
  name: string;
  kind: RouteKind;
  eventId?: string;
  from: number;
  to?: number;
  yearApprox?: boolean;
  note?: string;
  waypoints: RouteWaypoint[];
}

export interface RoutesDoc {
  routes: MarchRoute[];
}

/** highlights.json：事件 → 图层提亮 + 地理因果 why。 */
export interface LayerRefs {
  hydro?: string[];
  corridors?: string[];
  features?: string[];
  routes?: string[];
  places?: string[];
}

export interface EventHighlight extends LayerRefs {
  why: string;
}

export interface HighlightsDoc {
  highlights: Record<string, EventHighlight>;
}

/** stories.json：主题叙事镜头。 */
export interface StoryView {
  lon: number;
  lat: number;
  zoom: number;
}

export interface StoryStep {
  year: number;
  eventId?: string;
  view: StoryView;
  caption: string;
  show?: LayerRefs;
}

export interface Story {
  id: string;
  title: string;
  tagline: string;
  steps: StoryStep[];
}

export interface StoriesDoc {
  stories: Story[];
}

/** capitals.json：历代都城迁移 */
export type CapitalRole = "main" | "east" | "west" | "alt";

export interface Capital {
  id: string;
  state: string;
  name: string;
  placeId: string;
  from: number;
  to?: number;
  role: CapitalRole;
  note?: string;
}

export interface CapitalsDoc {
  capitals: Capital[];
}

export function capitalAliveAt(c: Capital, year: number): boolean {
  return year >= c.from && (c.to === undefined || year < c.to);
}

/** 主都迁移主线：重叠并存时只保留较早开端的一条，供轨迹折线。 */
export function mainCapitalTrail(capitals: Capital[]): Capital[] {
  const mains = capitals
    .filter((c) => c.role === "main")
    .sort((a, b) => a.from - b.from || a.id.localeCompare(b.id));
  const trail: Capital[] = [];
  let occupiedUntil = -Infinity;
  for (const c of mains) {
    if (c.from < occupiedUntil) continue;
    trail.push(c);
    occupiedUntil = c.to ?? 9999;
  }
  return trail;
}

/** 同组互斥（黄河历代河道同一时刻只留一条）。 */
export const EXCLUSIVE_FEATURE_GROUPS = new Set<string>(["yellow-river"]);

/**
 * 该年存活的地理要素；yellow-river 等同组互斥时取 from 最近的一条。
 * forceIds（提亮 / 主题 show）可强制并入，便于改道对照。
 */
export function featuresAtYear(
  features: GeoFeature[],
  year: number,
  forceIds?: Set<string>,
): GeoFeature[] {
  const alive = features.filter(
    (f) => year >= f.from && (f.to === undefined || year < f.to),
  );
  const byGroup = new Map<string, GeoFeature[]>();
  for (const f of alive) {
    const list = byGroup.get(f.group) ?? [];
    list.push(f);
    byGroup.set(f.group, list);
  }
  const out: GeoFeature[] = [];
  const seen = new Set<string>();
  for (const [group, list] of byGroup) {
    if (EXCLUSIVE_FEATURE_GROUPS.has(group) && list.length > 1) {
      list.sort((a, b) => b.from - a.from);
      const pick = list[0]!;
      out.push(pick);
      seen.add(pick.id);
    } else {
      for (const f of list) {
        out.push(f);
        seen.add(f.id);
      }
    }
  }
  if (forceIds?.size) {
    for (const f of features) {
      if (forceIds.has(f.id) && !seen.has(f.id)) {
        out.push(f);
        seen.add(f.id);
      }
    }
  }
  return out;
}

/** 行军线在 displayYear 已到达的折线（至少两点才画）。 */
export function routeLineAtYear(
  route: MarchRoute,
  year: number,
): [number, number][] | null {
  const pts: [number, number][] = [];
  for (const w of route.waypoints) {
    const wy = w.year ?? route.from;
    if (wy > year) break;
    pts.push([w.lon, w.lat]);
  }
  return pts.length >= 2 ? pts : null;
}

/** 当年份落在区间内、或绑定当前事件、或主题 show 点名时可见。 */
export function routesVisibleAt(
  routes: MarchRoute[],
  year: number,
  opts?: { eventId?: string | null; showIds?: Set<string> },
): MarchRoute[] {
  const eventId = opts?.eventId;
  const showIds = opts?.showIds;
  return routes.filter((r) => {
    if (showIds?.has(r.id)) return true;
    if (eventId && r.eventId === eventId) return true;
    const to = r.to ?? r.from;
    return year >= r.from && year <= to;
  });
}

export function emptyLayerRefs(): Required<LayerRefs> {
  return {
    hydro: [],
    corridors: [],
    features: [],
    routes: [],
    places: [],
  };
}

/** 合并事件提亮与主题 show。 */
export function mergeLayerRefs(
  ...parts: Array<LayerRefs | undefined | null>
): Required<LayerRefs> {
  const out = emptyLayerRefs();
  for (const p of parts) {
    if (!p) continue;
    for (const key of Object.keys(out) as (keyof LayerRefs)[]) {
      for (const id of p[key] ?? []) {
        if (!out[key].includes(id)) out[key].push(id);
      }
    }
  }
  return out;
}

/** 公元纪年：公元前为负。 */
export function formatYear(year: number): string {
  if (year < 0) return `前${-year}年`;
  if (year === 0) return "公元元年";
  return `${year}年`;
}

export function placeNameAt(place: Place, year: number): string {
  const hit = place.names.find(
    (n) => year >= n.from && (n.to === undefined || year < n.to),
  );
  return hit?.name ?? place.modern;
}

/** 该年是否已有历史名（from 已到、to 未过）。 */
export function placeAliveAt(place: Place, year: number): boolean {
  return place.names.some(
    (n) => year >= n.from && (n.to === undefined || year < n.to),
  );
}

export function eventsInEra(events: EventItem[], eraId: string): EventItem[] {
  return events.filter((e) => e.eraId === eraId).sort((a, b) => a.year - b.year);
}

/** 全史时间序列（跨阶段），自动播放的主轴之一。 */
export function chronologicalEvents(events: EventItem[]): EventItem[] {
  return [...events].sort((a, b) => a.year - b.year || a.id.localeCompare(b.id));
}

/** 落在某年的事件（同年多条）。 */
export function eventsAtYear(events: EventItem[], year: number): EventItem[] {
  return chronologicalEvents(events).filter((e) => e.year === year);
}

/** 不晚于 year 的最近一条事件。 */
export function nearestEventAtOrBefore(
  events: EventItem[],
  year: number,
): EventItem | undefined {
  const ordered = chronologicalEvents(events);
  let hit: EventItem | undefined;
  for (const e of ordered) {
    if (e.year <= year) hit = e;
    else break;
  }
  return hit ?? ordered[0];
}
