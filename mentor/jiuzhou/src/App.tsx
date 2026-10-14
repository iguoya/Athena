import { useEffect, useMemo, useRef, useState } from "react";
import MapGl, {
  Layer,
  Marker,
  NavigationControl,
  Source,
  type MapRef,
} from "react-map-gl/maplibre";
import { AnimatePresence, motion } from "motion/react";
import { cn } from "@/lib/utils";
import {
  PAPER_STYLE,
  MAP_TOKENS,
  powerColor,
  powerEdgeColor,
} from "@athena/maps/index.ts";
import coastlineJson from "../../../packages/maps/geo/coastline.json";
import landJson from "../../../packages/maps/geo/land.json";
import countriesJson from "../../../packages/maps/geo/countries.json";
import lakesJson from "../../../packages/maps/geo/lakes.json";
import reliefUrl from "../../../packages/maps/geo/relief-east-asia.webp";
import reliefMeta from "../../../packages/maps/geo/relief-east-asia.json";
import atlasJson from "@content/atlas.json";
/** T-017：陆地面裁剪后的疆域（源数据仍在 content/territories.json，归 zcode） */
import territoriesJson from "../../../packages/maps/geo/territories-clipped.json";
import hydroJson from "@content/hydro.json";
import corridorsJson from "@content/corridors.json";
import featuresJson from "@content/features.json";
import routesJson from "@content/routes.json";
import highlightsJson from "@content/highlights.json";
import storiesJson from "@content/stories.json";
import capitalsJson from "@content/capitals.json";
import landmarksJson from "@content/landmarks.json";
import { featuresCollection, routesCollection } from "@/content/layer-geo";
import { CompareMaps } from "@/CompareMaps";
import {
  academicAtYear,
  academicBelongingAt,
  belongingRowActiveAt,
  type AcademicProps,
  type BelongingResult,
} from "@/academic-layers";
import { powerAtPoint } from "@/geo-pip";
import {
  PlaceGlyph,
  PLACE_GLYPH_LEGEND,
  placeGlyphKind,
} from "@/PlaceGlyph";
import {
  estimatePath,
  estimateTravel,
  haversineKm,
  TRAVEL_RATE_SOURCES,
  type TravelEstimate,
} from "@/travel-cost";
import {
  type Atlas,
  type Capital,
  type CapitalsDoc,
  type EventItem,
  type EventKind,
  type FeaturesDoc,
  type HighlightsDoc,
  type MarchRoute,
  type Place,
  type RoutesDoc,
  type StoriesDoc,
  EVENT_KINDS,
  KIND_COLORS,
  capitalAliveAt,
  chronologicalEvents,
  eventsInEra,
  formatYear,
  mainCapitalTrail,
  mergeLayerRefs,
  nearestEventAtOrBefore,
  placeAliveAt,
  placeNameAt,
  routePieceAtYear,
  routesVisibleAt,
} from "@/content/types";

type Fc = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties?: Record<string, unknown>;
    geometry: object;
  }>;
};

const atlas = atlasJson as Atlas;
const territories = territoriesJson as Fc;
const coastline = coastlineJson as Fc;
const land = landJson as Fc;
const countries = countriesJson as Fc;
const lakes = lakesJson as Fc;
const hydro = hydroJson as Fc;
const corridors = corridorsJson as Fc;
const geoFeatures = (featuresJson as unknown as FeaturesDoc).features;
const marchRoutes = (routesJson as unknown as RoutesDoc).routes;
const eventHighlights = (highlightsJson as unknown as HighlightsDoc)
  .highlights;
const stories = (storiesJson as unknown as StoriesDoc).stories;
const allCapitals = (capitalsJson as unknown as CapitalsDoc).capitals;
const capitalTrail = mainCapitalTrail(allCapitals);

type LandmarkKind =
  | "mountain"
  | "plateau"
  | "basin"
  | "plain"
  | "desert"
  | "lake"
  | "sea";
type Landmark = {
  id: string;
  name: string;
  kind: LandmarkKind;
  lon: number;
  lat: number;
  size: 1 | 2 | 3;
  rotate?: number;
};
const landmarks = (
  landmarksJson as { landmarks: Landmark[] }
).landmarks;

/** size → 最低缩放：3@3.5、2@4.5、1@5.5 */
function landmarkMinZoom(size: number): number {
  if (size >= 3) return 3.5;
  if (size >= 2) return 4.5;
  return 5.5;
}

const CHINA_VIEW = { longitude: 105.5, latitude: 35.5, zoom: 3.45 };

/** T-028：历代归属列表 */
function BelongingList({
  result,
  year,
}: {
  result: BelongingResult;
  year: number;
}) {
  const hitCount = result.rows.filter((r) => r.kind === "hit").length;
  return (
    <>
      <p className="mt-1 text-[11px] text-muted">
        {result.lon.toFixed(2)}°E · {result.lat.toFixed(2)}°N · 命中 {hitCount}/
        {result.rows.length} 切片
      </p>
      <ul className="mt-2 max-h-72 space-y-1 overflow-y-auto text-[12px]">
        {result.rows.map((row) => {
          const active = belongingRowActiveAt(row, year);
          const key = row.kind === "hit" ? row.hit.sliceId : row.sliceId;
          if (row.kind === "empty") {
            return (
              <li
                key={key}
                className={cn(
                  "rounded px-2 py-1.5 text-muted",
                  active && "bg-accent-soft/40 font-semibold text-ink",
                )}
              >
                <span className="text-era">{row.sliceTitle}</span>
                <span className="text-[10px] text-muted">
                  {" "}
                  {formatYear(row.fromYear)}–{formatYear(row.toYear)}
                  {row.approximate ? " · 近似" : ""}
                </span>
                <span className="mt-0.5 block">该时期学术层无覆盖</span>
              </li>
            );
          }
          const h = row.hit;
          return (
            <li
              key={key}
              className={cn(
                "rounded px-2 py-1.5",
                active ? "bg-accent-soft font-semibold text-accent" : "text-ink",
              )}
            >
              <span className="text-era">{h.sliceTitle}</span>
              {" · "}
              {h.name}
              {h.type_ch ? `（${h.type_ch}）` : ""}
              <span className="mt-0.5 block text-[10px] font-normal text-muted">
                {formatYear(h.fromYear)}–{formatYear(h.toYear)}
                {h.approximate ? " · 近似（Hartwell）" : ""}
              </span>
            </li>
          );
        })}
      </ul>
    </>
  );
}

/** T-020：精度三档（前端推出，不改 content） */
type PrecisionTier = "academic" | "snapshot" | "schematic";
const PRECISION_META: Record<
  PrecisionTier,
  { label: string; tip: string; border: string }
> = {
  academic: {
    label: "学术",
    tip: "来自学术政区层（CHGIS / Hartwell）。Hartwell 切片为县域拼接近似，边界勿当考据。",
    border: "solid",
  },
  snapshot: {
    label: "快照示意",
    tip: "多势力手绘快照：大体方位可信，边界不是考据线。",
    border: "solid",
  },
  schematic: {
    label: "阶段示意",
    tip: "阶段框示意：虚线边 +「示意」水印，仅标范围。",
    border: "dashed",
  },
};

/** GeoJSON 外包矩形 [west, south, east, north]；无坐标则 null */
function bboxOfFeatures(
  features: Array<{ geometry?: object | null }>,
): [number, number, number, number] | null {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  function walk(node: unknown, depth: number) {
    if (!Array.isArray(node)) return;
    if (depth === 0 && typeof node[0] === "number" && typeof node[1] === "number") {
      const x = node[0] as number;
      const y = node[1] as number;
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
      return;
    }
    for (const child of node) walk(child, depth - 1);
  }
  for (const f of features) {
    const g = f.geometry as { type?: string; coordinates?: unknown } | null;
    if (!g?.coordinates) continue;
    const depth =
      g.type === "Point"
        ? 0
        : g.type === "MultiPoint" || g.type === "LineString"
          ? 1
          : g.type === "MultiLineString" || g.type === "Polygon"
            ? 2
            : 3;
    walk(g.coordinates, depth);
  }
  if (!Number.isFinite(minX)) return null;
  return [minX, minY, maxX, maxY];
}

/** 自动播放：秒→年（ADR 0001 / T-006） */
const YEAR_RATES = [
  { id: "1", label: "1年/秒", yearsPerSec: 1 },
  { id: "5", label: "5年/秒", yearsPerSec: 5 },
  { id: "10", label: "10年/秒", yearsPerSec: 10 },
  { id: "50", label: "50年/秒", yearsPerSec: 50 },
] as const;

type AxisMode = "year" | "event";

const DENSITY_BINS = 64;
const ERA_BAND_COLORS = [
  "#c4b5a0",
  "#b8a890",
  "#a89878",
  "#9a8a6e",
  "#8c7c62",
  "#7e6e56",
  "#70604a",
];

function placeById(id: string): Place | undefined {
  return atlas.places.find((p) => p.id === id);
}

function eventById(id: string): EventItem | undefined {
  return atlas.events.find((e) => e.id === id);
}

function eventKindOf(e: EventItem): EventKind {
  return e.kind ?? "政治";
}

type NameMode = "historic" | "modern" | "both";

function formatPlaceLabel(
  place: Place,
  year: number,
  mode: NameMode,
): { primary: string; secondary?: string } {
  const historic = placeNameAt(place, year);
  const modern = place.modern;
  if (mode === "modern") return { primary: modern };
  if (mode === "both") {
    if (historic === modern) return { primary: historic };
    return { primary: historic, secondary: modern };
  }
  return { primary: historic };
}

/** 两地之间的二次贝塞尔弧（同点则画小环）；供 leadsTo 影响链（T-008） */
function arcLineCoords(
  a: [number, number],
  b: [number, number],
  steps = 40,
): [number, number][] {
  const same = Math.abs(a[0] - b[0]) < 1e-6 && Math.abs(a[1] - b[1]) < 1e-6;
  if (same) {
    const r = 1.2;
    const out: [number, number][] = [];
    for (let i = 0; i <= steps; i++) {
      const t = (i / steps) * Math.PI * 1.6;
      out.push([a[0] + r * Math.cos(t), a[1] + r * Math.sin(t) * 0.7]);
    }
    return out;
  }
  const mx = (a[0] + b[0]) / 2;
  const my = (a[1] + b[1]) / 2;
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const len = Math.hypot(dx, dy) || 1;
  const bulge = Math.min(10, Math.max(1.5, len * 0.28));
  const cx = mx - (dy / len) * bulge;
  const cy = my + (dx / len) * bulge;
  const out: [number, number][] = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const u = 1 - t;
    out.push([
      u * u * a[0] + 2 * u * t * cx + t * t * b[0],
      u * u * a[1] + 2 * u * t * cy + t * t * b[1],
    ]);
  }
  return out;
}

export default function App() {
  const timelineAll = useMemo(() => chronologicalEvents(atlas.events), []);
  const yearMin = timelineAll[0]?.year ?? -2000;
  const yearMax = timelineAll[timelineAll.length - 1]?.year ?? 2000;

  const [axis, setAxis] = useState<AxisMode>("year");
  const [index, setIndex] = useState(() => {
    const i = timelineAll.findIndex((e) => e.eraId === "qin-han");
    return i >= 0 ? i : 0;
  });
  const [year, setYear] = useState(() => timelineAll[index]?.year ?? 0);
  const [playing, setPlaying] = useState(false);
  const [speedId, setSpeedId] =
    useState<(typeof YEAR_RATES)[number]["id"]>("10");
  const [compareAfter, setCompareAfter] = useState(true);
  const [query, setQuery] = useState("");
  const [focusPlaceId, setFocusPlaceId] = useState<string | null>(null);
  const [storyId, setStoryId] = useState<string | null>(null);
  const [storyStep, setStoryStep] = useState(0);
  const [showCapitals, setShowCapitals] = useState(true);
  /** T-022：山川湖海注记，默认开 */
  const [showLandmarks, setShowLandmarks] = useState(true);
  const [compareMode, setCompareMode] = useState(false);
  const [leftYear, setLeftYear] = useState(-260);
  const [rightYear, setRightYear] = useState(-221);
  const [kindOn, setKindOn] = useState<Set<EventKind>>(
    () => new Set(EVENT_KINDS),
  );
  /** 遇事件暂停弹卡倒计时剩余秒（T-006） */
  const [eventHoldLeft, setEventHoldLeft] = useState(0);
  /** 古名（默认）/ 今名 / 双显（T-009） */
  const [nameMode, setNameMode] = useState<NameMode>("historic");
  const mapRef = useRef<MapRef>(null);
  const mapBoxRef = useRef<HTMLDivElement>(null);
  const [academicPick, setAcademicPick] = useState<AcademicProps | null>(null);
  /** T-028：点图历代归属 */
  const [belonging, setBelonging] = useState<BelongingResult | null>(null);
  /** T-019：暗角与纸纹，默认开 */
  const [paperAmbience, setPaperAmbience] = useState(true);
  /** T-030：学术层不透明度倍率，1 = 现状（0.2 / 近似 0.14） */
  const [academicOpacity, setAcademicOpacity] = useState(1);
  /** T-030：仅在选事件/切轴/故事时取景，纯拖年不抢镜头 */
  const frameKeyRef = useRef<string | null>(null);
  /** 势力名标签随缩放淡出 */
  const [mapZoom, setMapZoom] = useState(CHINA_VIEW.zoom);
  /** T-020：点击疆域 / 学术面卡片 */
  const [precisionPick, setPrecisionPick] = useState<{
    title: string;
    tier: PrecisionTier;
    note?: string;
  } | null>(null);
  /** T-020：悬停角落提示 */
  const [precisionHover, setPrecisionHover] = useState<{
    tier: PrecisionTier;
    title: string;
  } | null>(null);
  /** T-021：点击政权后浏览其境内事件；与选中事件的宿主政权共用高亮 */
  const [powerBrowse, setPowerBrowse] = useState<string | null>(null);
  const yearRef = useRef(year);
  const holdUntilRef = useRef(0);
  const territoryModeRef = useRef<string | null>(null);
  const territoryDataRef = useRef<Fc | null>(null);
  yearRef.current = year;
  const yearsPerSec =
    YEAR_RATES.find((s) => s.id === speedId)?.yearsPerSec ?? 10;

  const timeline = useMemo(
    () => timelineAll.filter((e) => kindOn.has(eventKindOf(e))),
    [timelineAll, kindOn],
  );

  const densityBins = useMemo(() => {
    const span = Math.max(1, yearMax - yearMin);
    const bins = Array.from({ length: DENSITY_BINS }, () => {
      const stack: Partial<Record<EventKind, number>> = {};
      for (const k of EVENT_KINDS) stack[k] = 0;
      return stack as Record<EventKind, number>;
    });
    for (const e of timelineAll) {
      if (!kindOn.has(eventKindOf(e))) continue;
      const i = Math.min(
        DENSITY_BINS - 1,
        Math.max(0, Math.floor(((e.year - yearMin) / span) * DENSITY_BINS)),
      );
      bins[i][eventKindOf(e)] += 1;
    }
    const maxH = Math.max(
      1,
      ...bins.map((b) => EVENT_KINDS.reduce((s, k) => s + b[k], 0)),
    );
    return { bins, maxH };
  }, [timelineAll, kindOn, yearMin, yearMax]);

  const activeStory = storyId
    ? (stories.find((s) => s.id === storyId) ?? null)
    : null;
  const activeStoryStep =
    activeStory?.steps[storyStep] ?? activeStory?.steps[0] ?? null;

  const selected =
    axis === "event"
      ? (timeline[Math.min(index, Math.max(0, timeline.length - 1))] ??
        timeline[0])
      : (() => {
          const near = nearestEventAtOrBefore(atlas.events, year);
          if (near && kindOn.has(eventKindOf(near))) return near;
          return (
            [...timelineAll]
              .reverse()
              .find((e) => e.year <= year && kindOn.has(eventKindOf(e))) ??
            timeline[0]
          );
        })();

  const displayYear =
    axis === "year"
      ? selected?.compare
        ? compareAfter
          ? selected.compare.afterYear
          : selected.compare.beforeYear
        : Math.round(year)
      : (selected?.year ?? Math.round(year));

  /** T-010：包内学术层按年筛选 */
  const academicData = useMemo(
    () => academicAtYear(displayYear),
    [displayYear],
  );

  const era =
    atlas.eras.find((e) => e.id === selected?.eraId) ??
    atlas.eras.find((e) => displayYear >= e.from && displayYear <= e.to) ??
    atlas.eras[0];

  const eraEvents = useMemo(
    () =>
      eventsInEra(atlas.events, era.id).filter((e) =>
        kindOn.has(eventKindOf(e)),
      ),
    [era.id, kindOn],
  );

  function toggleKind(k: EventKind) {
    setKindOn((prev) => {
      const next = new Set(prev);
      if (next.has(k)) {
        if (next.size <= 1) return prev;
        next.delete(k);
      } else {
        next.add(k);
      }
      return next;
    });
  }

  const eventHl = selected ? eventHighlights[selected.id] : undefined;
  const lit = useMemo(
    () => mergeLayerRefs(eventHl, activeStoryStep?.show),
    [eventHl, activeStoryStep],
  );
  const litHydro = useMemo(() => new Set(lit.hydro), [lit]);
  const litCorridors = useMemo(() => new Set(lit.corridors), [lit]);
  const litFeatures = useMemo(() => new Set(lit.features), [lit]);
  const litRoutes = useMemo(() => new Set(lit.routes), [lit]);
  const showRouteIds = useMemo(() => new Set(lit.routes), [lit]);

  const highlightIds = useMemo(() => {
    const ids = new Set<string>();
    if (selected?.placeId) ids.add(selected.placeId);
    for (const id of selected?.placeIds ?? []) ids.add(id);
    for (const id of selected?.highlightPlaceIds ?? []) ids.add(id);
    for (const id of lit.places) ids.add(id);
    if (focusPlaceId) ids.add(focusPlaceId);
    return ids;
  }, [selected, focusPlaceId, lit.places]);

  const visiblePlaces = useMemo(() => {
    const eventIds = new Set(eraEvents.map((e) => e.placeId));
    if (selected) eventIds.add(selected.placeId);
    for (const id of highlightIds) eventIds.add(id);
    return atlas.places
      .filter((p) => placeAliveAt(p, displayYear) || eventIds.has(p.id))
      .sort((a, b) => {
        const rank = (t: Place["tier"]) =>
          ({ capital: 0, metropolis: 1, pass: 2, prefecture: 3, other: 4 })[t] ??
          5;
        return rank(a.tier) - rank(b.tier);
      });
  }, [eraEvents, selected, displayYear, highlightIds]);

  type SearchHit =
    | { kind: "place"; place: Place; label: string }
    | { kind: "event"; event: EventItem; label: string }
    | { kind: "person"; personId: string; name: string; label: string }
    | { kind: "route"; route: MarchRoute; label: string };

  const searchHits = useMemo(() => {
    const q = query.trim();
    if (!q) return [] as SearchHit[];
    const places: SearchHit[] = [];
    const events: SearchHit[] = [];
    const people: SearchHit[] = [];
    const routes: SearchHit[] = [];
    for (const p of atlas.places) {
      const hist = p.names.find(
        (n) => n.name.includes(q) || (n.also ?? []).some((a) => a.includes(q)),
      );
      if (p.modern.includes(q) || p.id.includes(q) || hist) {
        places.push({
          kind: "place",
          place: p,
          label: hist
            ? `${hist.name} · 今${p.modern}`
            : `${placeNameAt(p, displayYear)} · 今${p.modern}`,
        });
      }
      if (places.length >= 8) break;
    }
    for (const e of timelineAll) {
      if (
        e.title.includes(q) ||
        (e.lede?.includes(q) ?? false) ||
        (e.people ?? []).some((n) => n.includes(q))
      ) {
        events.push({
          kind: "event",
          event: e,
          label: `${formatYear(e.year)} · ${e.title}`,
        });
      }
      if (events.length >= 8) break;
    }
    for (const person of atlas.people) {
      const aliasHit = (person.aliases ?? []).some((a) => a.includes(q));
      if (person.name.includes(q) || aliasHit) {
        people.push({
          kind: "person",
          personId: person.id,
          name: person.name,
          label: person.name,
        });
      }
      if (people.length >= 6) break;
    }
    if (!people.some((h) => h.kind === "person" && h.name.includes(q))) {
      const names = new Set<string>();
      for (const e of timelineAll) {
        for (const n of e.people ?? []) {
          if (n.includes(q)) names.add(n);
        }
      }
      for (const n of names) {
        people.push({
          kind: "person",
          personId: "",
          name: n,
          label: n,
        });
        if (people.length >= 6) break;
      }
    }
    for (const r of marchRoutes) {
      if (r.name.includes(q) || r.group.includes(q)) {
        routes.push({
          kind: "route",
          route: r,
          label: r.name,
        });
      }
      if (routes.length >= 6) break;
    }
    // 人物命中时补上同名 group 的路线（搜「张骞」）
    if (routes.length < 6) {
      const personNames = new Set(
        people
          .filter((h): h is Extract<SearchHit, { kind: "person" }> => h.kind === "person")
          .map((h) => h.name),
      );
      for (const r of marchRoutes) {
        if (routes.some((h) => h.kind === "route" && h.route.id === r.id)) continue;
        const hitByPerson =
          personNames.has(r.group) ||
          [...personNames].some((n) => r.name.includes(n) || r.group.includes(n));
        if (!hitByPerson) continue;
        routes.push({ kind: "route", route: r, label: r.name });
        if (routes.length >= 6) break;
      }
    }
    return [...places, ...people, ...events, ...routes].slice(0, 20);
  }, [query, displayYear, timelineAll]);

  const [focusPersonId, setFocusPersonId] = useState<string | null>(null);
  const [focusPersonName, setFocusPersonName] = useState<string | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  const focusPerson = focusPersonId
    ? (atlas.people.find((p) => p.id === focusPersonId) ?? null)
    : null;

  const personEvents = useMemo(() => {
    if (focusPersonId) {
      return timelineAll.filter((e) =>
        (e.personIds ?? []).includes(focusPersonId),
      );
    }
    if (focusPersonName) {
      return timelineAll.filter((e) => (e.people ?? []).includes(focusPersonName));
    }
    return [];
  }, [focusPersonId, focusPersonName, timelineAll]);

  const personRoutes = useMemo(() => {
    const name = focusPerson?.name ?? focusPersonName;
    if (!name) return [];
    return marchRoutes.filter(
      (r) => r.group === name || r.name.includes(name),
    );
  }, [focusPerson, focusPersonName]);

  type TerrProps = {
    id?: string;
    kind?: string;
    snapshot?: string;
    fromYear?: number;
    toYear?: number;
    color?: string;
    power?: string;
    capital?: string;
    capitalPlaceId?: string;
  };

  /** T-002：有 snapshot 只画快照；否则示意虚线+水印，绝不两套叠画 */
  const territoryView = useMemo(() => {
    const inYear = territories.features.filter((f) => {
      const p = (f.properties ?? {}) as TerrProps;
      const from = typeof p.fromYear === "number" ? p.fromYear : -9999;
      const to = typeof p.toYear === "number" ? p.toYear : 9999;
      return displayYear >= from && displayYear <= to;
    });
    const snaps = inYear.filter(
      (f) => (f.properties as TerrProps).kind === "snapshot",
    );
    if (snaps.length) {
      const groups = new Map<string, typeof snaps>();
      for (const f of snaps) {
        const sid = String((f.properties as TerrProps).snapshot ?? "?");
        const list = groups.get(sid) ?? [];
        list.push(f);
        groups.set(sid, list);
      }
      const best = [...groups.values()].sort((a, b) => b.length - a.length)[0]!;
      return {
        mode: "snapshot" as const,
        data: { type: "FeatureCollection" as const, features: best },
      };
    }
    const schematics = inYear.filter((f) => {
      const k = (f.properties as TerrProps).kind;
      return k === "schematic" || k === undefined || k === "";
    });
    if (schematics.length) {
      return {
        mode: "schematic" as const,
        data: { type: "FeatureCollection" as const, features: schematics },
      };
    }
    const tid = era.territoryId;
    if (!tid) return null;
    const fallback = territories.features.filter(
      (f) => (f.properties as TerrProps).id === tid,
    );
    if (!fallback.length) return null;
    return {
      mode: "schematic" as const,
      data: { type: "FeatureCollection" as const, features: fallback },
    };
  }, [displayYear, era.territoryId]);

  const territoryData = territoryView?.data ?? null;
  const territoryMode = territoryView?.mode ?? null;
  territoryModeRef.current = territoryMode;
  territoryDataRef.current = territoryData;

  /** 当前快照年：各国都城（B 交接：capitalPlaceId 标都城） */
  const snapshotCapitals = useMemo(() => {
    if (!territoryData) return [];
    const out: Array<{
      place: Place;
      power: string;
      color: string;
      capitalName: string;
    }> = [];
    for (const f of territoryData.features) {
      const p = (f.properties ?? {}) as TerrProps;
      if (p.kind !== "snapshot" || !p.capitalPlaceId) continue;
      const place = placeById(p.capitalPlaceId);
      if (!place) continue;
      out.push({
        place,
        power: p.power ?? "",
        color: powerColor(p.power, p.color ?? MAP_TOKENS.territory),
        capitalName: p.capital ?? placeNameAt(place, displayYear),
      });
    }
    return out;
  }, [territoryData, displayYear]);

  /** T-003：地点改 GeoJSON + symbol，碰撞检测 */
  const placesGeo = useMemo(() => {
    const tierRank: Record<Place["tier"], number> = {
      capital: 0,
      metropolis: 1,
      pass: 2,
      prefecture: 3,
      other: 4,
    };
    const touches = (ev: EventItem, pid: string) =>
      ev.placeId === pid || (ev.placeIds ?? []).includes(pid);
    const features = visiblePlaces.map((place) => {
      const active =
        selected?.placeId === place.id ||
        (selected ? touches(selected, place.id) : false);
      const lit = highlightIds.has(place.id);
      const focused = focusPlaceId === place.id;
      const capital = snapshotCapitals.some((c) => c.place.id === place.id);
      const inEvent = eraEvents.some((e) => touches(e, place.id));
      const mustShow =
        active || lit || focused || capital || inEvent ? 1 : 0;
      const sortKey = mustShow ? -1 : (tierRank[place.tier] ?? 5);
      const label = formatPlaceLabel(place, displayYear, nameMode);
      const alive = placeAliveAt(place, displayYear);
      return {
        type: "Feature" as const,
        properties: {
          id: place.id,
          name: label.primary,
          modern: place.modern,
          secondary: label.secondary ?? "",
          tier: place.tier,
          glyph: placeGlyphKind(place),
          sortKey,
          mustShow,
          alive: alive ? 1 : 0,
          active: active || lit || focused || capital ? 1 : 0,
        },
        geometry: {
          type: "Point" as const,
          coordinates: [place.lon, place.lat],
        },
      };
    });
    return { type: "FeatureCollection" as const, features };
  }, [
    visiblePlaces,
    selected,
    highlightIds,
    focusPlaceId,
    snapshotCapitals,
    eraEvents,
    displayYear,
    nameMode,
  ]);

  /** T-003 / T-022：城邑优先；再插 size≥3 自然注记；再补其余城邑与小注记 */
  const [placeLabelIds, setPlaceLabelIds] = useState<string[]>([]);
  const [landmarkLabelIds, setLandmarkLabelIds] = useState<string[]>([]);
  useEffect(() => {
    const map = mapRef.current?.getMap();
    if (!map) return;
    const mapInst = map;
    function overlaps(
      box: { x0: number; y0: number; x1: number; y1: number },
      taken: Array<{ x0: number; y0: number; x1: number; y1: number }>,
    ) {
      return taken.some(
        (t) =>
          !(
            box.x1 < t.x0 ||
            box.x0 > t.x1 ||
            box.y1 < t.y0 ||
            box.y0 > t.y1
          ),
      );
    }
    function recompute() {
      const m = mapInst;
      const feats = [...placesGeo.features].sort(
        (a, b) =>
          Number(a.properties?.sortKey ?? 9) -
          Number(b.properties?.sortKey ?? 9),
      );
      const zoom = m.getZoom();
      const taken: Array<{ x0: number; y0: number; x1: number; y1: number }> =
        [];
      const ids: string[] = [];
      const lmIds: string[] = [];

      function tryPlace(f: (typeof feats)[0]): boolean {
        const props = f.properties as {
          id: string;
          name: string;
          tier: string;
          mustShow: number;
        };
        if (
          zoom < 5.2 &&
          props.tier !== "capital" &&
          props.tier !== "metropolis" &&
          !props.mustShow
        ) {
          return false;
        }
        const coords = f.geometry.coordinates as [number, number];
        const pt = m.project(coords);
        const w = Math.min(140, 14 + props.name.length * 10);
        const h = 18;
        const box = {
          x0: pt.x - w / 2,
          y0: pt.y + 8,
          x1: pt.x + w / 2,
          y1: pt.y + 8 + h,
        };
        if (overlaps(box, taken)) return false;
        taken.push(box);
        ids.push(props.id);
        return true;
      }

      function tryLandmark(lm: Landmark): boolean {
        if (zoom < landmarkMinZoom(lm.size)) return false;
        const pt = m.project([lm.lon, lm.lat]);
        const fontPx = lm.size >= 3 ? 13 : lm.size >= 2 ? 11 : 10;
        const w = Math.min(160, 10 + lm.name.length * (fontPx * 0.85));
        const h = fontPx + 6;
        const box = {
          x0: pt.x - w / 2,
          y0: pt.y - h / 2,
          x1: pt.x + w / 2,
          y1: pt.y + h / 2,
        };
        if (overlaps(box, taken)) return false;
        taken.push(box);
        lmIds.push(lm.id);
        return true;
      }

      /** 1) 事件/都城等 mustShow 与高等级城邑 */
      for (const f of feats) {
        const props = f.properties as { mustShow: number; tier: string };
        if (
          props.mustShow ||
          props.tier === "capital" ||
          props.tier === "metropolis"
        ) {
          tryPlace(f);
          if (ids.length >= 24) break;
        }
      }

      /** 2) 大号自然注记（秦岭/太行/高原/黄海等） */
      if (showLandmarks) {
        for (const lm of [...landmarks].sort((a, b) => b.size - a.size)) {
          if (lm.size < 3) continue;
          tryLandmark(lm);
          if (lmIds.length >= 16) break;
        }
      }

      /** 3) 其余城邑 */
      for (const f of feats) {
        if (ids.includes(String(f.properties?.id ?? ""))) continue;
        tryPlace(f);
        if (ids.length >= 40) break;
      }

      /** 4) 中小号自然注记 */
      if (showLandmarks) {
        for (const lm of [...landmarks].sort((a, b) => b.size - a.size)) {
          if (lmIds.includes(lm.id)) continue;
          tryLandmark(lm);
          if (lmIds.length >= 36) break;
        }
      }

      setPlaceLabelIds(ids);
      setLandmarkLabelIds(lmIds);
    }
    map.on("load", recompute);
    map.on("moveend", recompute);
    map.on("zoomend", recompute);
    const t = window.setTimeout(recompute, 120);
    return () => {
      window.clearTimeout(t);
      map.off("load", recompute);
      map.off("moveend", recompute);
      map.off("zoomend", recompute);
    };
  }, [placesGeo, showLandmarks]);

  /** 快照势力名：多边形质心 */
  const powerCentroids = useMemo(() => {
    if (!territoryData) return [];
    const out: Array<{ lon: number; lat: number; power: string; color: string }> =
      [];
    for (const f of territoryData.features) {
      const p = (f.properties ?? {}) as TerrProps;
      if (p.kind !== "snapshot" || !p.power) continue;
      const g = f.geometry as {
        type?: string;
        coordinates?: unknown;
      };
      let ring: number[][] | null = null;
      if (g.type === "Polygon") {
        ring = (g.coordinates as number[][][])[0] ?? null;
      } else if (g.type === "MultiPolygon") {
        ring = (g.coordinates as number[][][][])[0]?.[0] ?? null;
      }
      if (!ring?.length) continue;
      let sx = 0;
      let sy = 0;
      let n = 0;
      for (const c of ring) {
        if (c.length < 2) continue;
        sx += c[0];
        sy += c[1];
        n += 1;
      }
      if (n < 1) continue;
      out.push({
        lon: sx / n,
        lat: sy / n,
        power: p.power,
        color: powerColor(p.power, p.color ?? MAP_TOKENS.territory),
      });
    }
    return out;
  }, [territoryData]);

  /** T-021：选中事件地点落在哪个快照政权内 */
  const hostPower = useMemo(() => {
    if (!territoryData || territoryMode !== "snapshot" || !selected) {
      return null;
    }
    const place = placeById(selected.placeId);
    if (!place) return null;
    return powerAtPoint(place.lon, place.lat, territoryData.features);
  }, [territoryData, territoryMode, selected]);

  const litPower = powerBrowse ?? hostPower;

  /** 点政权：当前快照时间窗内、地点落在该色块内的事件 */
  const powerEvents = useMemo(() => {
    if (!powerBrowse || !territoryData || territoryMode !== "snapshot") {
      return [] as EventItem[];
    }
    const feats = territoryData.features.filter(
      (f) => (f.properties as TerrProps).power === powerBrowse,
    );
    if (!feats.length) return [];
    const p0 = feats[0]!.properties as TerrProps;
    const from = typeof p0.fromYear === "number" ? p0.fromYear : -9999;
    const to = typeof p0.toYear === "number" ? p0.toYear : 9999;
    /** 快照窗再向前后各放宽，便于点到秦时能看到拔郢/灭巴蜀等同境事件 */
    const softFrom = from - 100;
    const softTo = to + 40;
    const out: EventItem[] = [];
    for (const e of timelineAll) {
      if (e.year < softFrom || e.year > softTo) continue;
      const ids = [e.placeId, ...(e.placeIds ?? [])];
      let hit = false;
      for (const pid of ids) {
        const pl = placeById(pid);
        if (!pl) continue;
        if (powerAtPoint(pl.lon, pl.lat, feats) === powerBrowse) {
          hit = true;
          break;
        }
      }
      if (hit) out.push(e);
    }
    return out.sort((a, b) => a.year - b.year || a.id.localeCompare(b.id));
  }, [powerBrowse, territoryData, territoryMode, timelineAll]);

  const hostPowerRef = useRef<string | null>(null);
  const powerBrowseRef = useRef<string | null>(null);
  const powerEventsRef = useRef<EventItem[]>([]);
  const selectedRef = useRef<EventItem | undefined>(undefined);
  hostPowerRef.current = hostPower;
  powerBrowseRef.current = powerBrowse;
  powerEventsRef.current = powerEvents;
  selectedRef.current = selected;

  /** T-019 / T-021：注入颜色与 lit 高亮 */
  const territoryPaintData = useMemo(() => {
    if (!territoryData) return null;
    return {
      type: "FeatureCollection" as const,
      features: territoryData.features.map((f) => {
        const p = (f.properties ?? {}) as TerrProps;
        const color = powerColor(p.power, p.color ?? MAP_TOKENS.territory);
        const lit = litPower && p.power === litPower ? 1 : 0;
        return {
          ...f,
          properties: {
            ...p,
            color,
            edge: powerEdgeColor(color),
            lit,
            dim: litPower && !lit ? 1 : 0,
          },
        };
      }),
    };
  }, [territoryData, litPower]);

  const [drawerLeft, setDrawerLeft] = useState(false);
  const [drawerRight, setDrawerRight] = useState(false);
  /** 阶段说明默认折叠一行；事件条默认收起，给地图让高度（T-004） */
  const [eraBlurbOpen, setEraBlurbOpen] = useState(false);
  const [eventDrawerOpen, setEventDrawerOpen] = useState(false);

  /** 地点剖面：主 placeId 或 placeIds 命中的事件（B 交接 #7） */
  const placeRelatedEvents = useMemo(() => {
    if (!focusPlaceId) return [];
    return chronologicalEvents(atlas.events).filter((e) => {
      if (e.placeId === focusPlaceId) return true;
      return (e.placeIds ?? []).includes(focusPlaceId);
    });
  }, [focusPlaceId]);

  /** P1 都城迁移：当年主都 / 陪都 */
  const liveCapitals = useMemo(() => {
    const mains: Array<{ cap: Capital; place: Place }> = [];
    const alts: Array<{ cap: Capital; place: Place }> = [];
    for (const cap of allCapitals) {
      if (!capitalAliveAt(cap, displayYear)) continue;
      const place = placeById(cap.placeId);
      if (!place) continue;
      if (cap.role === "main") mains.push({ cap, place });
      else alts.push({ cap, place });
    }
    return { mains, alts };
  }, [displayYear]);

  /** 主都轨迹：已过实线 / 未到虚线 / 当前段高亮 */
  const capitalTrailGeo = useMemo(() => {
    type Pt = { lon: number; lat: number; from: number; id: string };
    const pts: Pt[] = [];
    for (const c of capitalTrail) {
      const place = placeById(c.placeId);
      if (!place) continue;
      const last = pts[pts.length - 1];
      if (last && last.lon === place.lon && last.lat === place.lat) {
        last.from = c.from;
        last.id = c.id;
        continue;
      }
      pts.push({ lon: place.lon, lat: place.lat, from: c.from, id: c.id });
    }
    let cur = -1;
    for (let i = 0; i < pts.length; i++) {
      if (pts[i].from <= displayYear) cur = i;
    }
    const line = (coords: number[][]) =>
      coords.length >= 2
        ? {
            type: "Feature" as const,
            properties: {},
            geometry: { type: "LineString" as const, coordinates: coords },
          }
        : null;
    const pastCoords = pts.slice(0, Math.max(0, cur + 1)).map((p) => [p.lon, p.lat]);
    const futureCoords = pts.slice(Math.max(0, cur)).map((p) => [p.lon, p.lat]);
    const hiCoords =
      cur > 0
        ? [
            [pts[cur - 1].lon, pts[cur - 1].lat],
            [pts[cur].lon, pts[cur].lat],
          ]
        : [];
    return {
      past: {
        type: "FeatureCollection" as const,
        features: [line(pastCoords)].filter(Boolean) as Fc["features"],
      },
      future: {
        type: "FeatureCollection" as const,
        features: [line(futureCoords)].filter(Boolean) as Fc["features"],
      },
      highlight: {
        type: "FeatureCollection" as const,
        features: [line(hiCoords)].filter(Boolean) as Fc["features"],
      },
    };
  }, [displayYear]);

  const featureData = useMemo(
    () => featuresCollection(geoFeatures, displayYear, litFeatures),
    [displayYear, litFeatures],
  );

  const marchRouteData = useMemo(
    () =>
      routesCollection(marchRoutes, displayYear, {
        eventId: selected?.id,
        showIds: showRouteIds,
        litIds: litRoutes,
      }),
    [displayYear, selected?.id, showRouteIds, litRoutes],
  );

  /** T-024：可见路线上的印章棋子（每条一枚，停在已到达的最远途经点） */
  const routePieces = useMemo(() => {
    const visible = routesVisibleAt(marchRoutes, displayYear, {
      eventId: selected?.id,
      showIds: showRouteIds,
    });
    const byGroup = new Set<string>();
    const out: Array<{
      routeId: string;
      lon: number;
      lat: number;
      seal: string;
      label: string;
      eventId?: string;
      placeId?: string;
      atEventPlace: boolean;
    }> = [];
    for (const r of visible) {
      if (byGroup.has(r.group)) continue;
      const wp = routePieceAtYear(r, displayYear);
      if (!wp) continue;
      byGroup.add(r.group);
      let seal = r.name.slice(0, 1);
      if (r.eventId) {
        const ev = atlas.events.find((e) => e.id === r.eventId);
        const pid = ev?.personIds?.[0];
        const person = pid
          ? atlas.people.find((p) => p.id === pid)
          : atlas.people.find((p) => (ev?.people ?? []).includes(p.name));
        if (person?.name) seal = person.name.slice(0, 1);
        else if (ev?.people?.[0]) seal = ev.people[0].slice(0, 1);
      }
      const evPlace = r.eventId
        ? atlas.events.find((e) => e.id === r.eventId)?.placeId
        : undefined;
      out.push({
        routeId: r.id,
        lon: wp.lon,
        lat: wp.lat,
        seal,
        label: wp.label,
        eventId: r.eventId,
        placeId: wp.placeId,
        atEventPlace: Boolean(evPlace && wp.placeId === evPlace),
      });
    }
    return out;
  }, [displayYear, selected?.id, showRouteIds]);

  /** 旧 atlas.events[].route 折线，与 content/routes.json 并存。 */
  const legacyRouteData = useMemo(() => {
    const route = selected?.route;
    if (!route?.length) return null;
    return {
      type: "FeatureCollection" as const,
      features: [
        {
          type: "Feature" as const,
          properties: { id: selected?.id ?? "", lit: 1 },
          geometry: { type: "LineString" as const, coordinates: route },
        },
      ],
    };
  }, [selected]);

  /** T-008：选中事件的 leadsTo → 弧线 + 中点年份标签；T-029 附通行估算 */
  const leadsToArcs = useMemo(() => {
    if (!selected?.leadsTo?.length) {
      return {
        lines: null as Fc | null,
        labels: [] as Array<{
          lon: number;
          lat: number;
          eventId: string;
          year: number;
          title: string;
          travel?: TravelEstimate;
        }>,
      };
    }
    const from = placeById(selected.placeId);
    if (!from) {
      return { lines: null, labels: [] };
    }
    const features: Fc["features"] = [];
    const labels: Array<{
      lon: number;
      lat: number;
      eventId: string;
      year: number;
      title: string;
      travel?: TravelEstimate;
    }> = [];
    for (const id of selected.leadsTo) {
      const next = eventById(id);
      if (!next) continue;
      const to = placeById(next.placeId);
      if (!to) continue;
      const coords = arcLineCoords(
        [from.lon, from.lat],
        [to.lon, to.lat],
      );
      const travel = estimateTravel(
        haversineKm(from.lon, from.lat, to.lon, to.lat),
      );
      features.push({
        type: "Feature",
        properties: {
          eventId: next.id,
          year: next.year,
          title: next.title,
          km: travel.km,
        },
        geometry: { type: "LineString", coordinates: coords },
      });
      const mid = coords[Math.floor(coords.length * 0.55)]!;
      labels.push({
        lon: mid[0],
        lat: mid[1],
        eventId: next.id,
        year: next.year,
        title: next.title,
        travel,
      });
    }
    return {
      lines: features.length
        ? { type: "FeatureCollection" as const, features }
        : null,
      labels,
    };
  }, [selected]);

  /** T-029：当前事件绑定的行军线通行估算 */
  const selectedRouteCosts = useMemo(() => {
    if (!selected) return [] as Array<{ name: string; travel: TravelEstimate }>;
    const out: Array<{ name: string; travel: TravelEstimate }> = [];
    for (const r of marchRoutes) {
      if (r.eventId !== selected.id) continue;
      const coords = r.waypoints.map(
        (w) => [w.lon, w.lat] as [number, number],
      );
      const travel = estimatePath(coords);
      if (!travel) continue;
      out.push({ name: r.name, travel });
    }
    if (selected.route && selected.route.length >= 2) {
      const coords = selected.route.map(
        (p) => [p[0], p[1]] as [number, number],
      );
      const travel = estimatePath(coords);
      if (travel) out.push({ name: "事件附带路线", travel });
    }
    return out;
  }, [selected]);

  const storyCaption = activeStoryStep?.caption ?? null;
  const geoWhyText = selected?.geoWhy ?? null;
  const highlightWhy =
    eventHl?.why && eventHl.why !== geoWhyText ? eventHl.why : null;

  // 自动播放：按年匀速前进；跨过事件年时停 3 秒弹卡（T-006）
  useEffect(() => {
    if (!playing) {
      holdUntilRef.current = 0;
      setEventHoldLeft(0);
      return;
    }
    setAxis("year");
    let last = performance.now();
    const tick = window.setInterval(() => {
      const now = performance.now();
      if (now < holdUntilRef.current) {
        setEventHoldLeft(
          Math.max(0, Math.ceil((holdUntilRef.current - now) / 1000)),
        );
        return;
      }
      setEventHoldLeft(0);
      const dt = Math.min(0.2, (now - last) / 1000);
      last = now;
      const y0 = yearRef.current;
      const y1 = y0 + yearsPerSec * dt;
      const hit = timeline.find((e) => e.year > y0 && e.year <= y1);
      if (hit) {
        holdUntilRef.current = now + 3000;
        setEventHoldLeft(3);
        setYear(hit.year);
        const ni = timeline.findIndex((e) => e.id === hit.id);
        if (ni >= 0) setIndex(ni);
        setFocusPlaceId(hit.placeId);
        setDrawerRight(true);
        return;
      }
      if (y1 >= yearMax) {
        setYear(yearMax);
        setPlaying(false);
        setEventHoldLeft(0);
        return;
      }
      setYear(y1);
      const near = nearestEventAtOrBefore(timeline, Math.floor(y1));
      if (near) {
        const ni = timeline.findIndex((e) => e.id === near.id);
        if (ni >= 0) setIndex(ni);
      }
    }, 50);
    return () => window.clearInterval(tick);
  }, [playing, yearsPerSec, timeline, yearMax]);

  /** T-018：验收自检 window.__jzDebug */
  useEffect(() => {
    type JzDebug = {
      layers: () => string[];
      rendered: (layerId: string) => number | null;
      year: () => number;
      setYear: (y: number) => void;
      setZoom: (z: number) => void;
      flyTo: (lon: number, lat: number, z?: number) => void;
      snapshotsShown: () => { group: string; powers: string[] } | null;
      schematicShown: () => boolean;
      hostPower: () => string | null;
      powerBrowse: () => string | null;
      setPowerBrowse: (p: string | null) => void;
      powerEventTitles: () => string[];
      selectedId: () => string | null;
      selectEvent: (id: string) => boolean;
      queryBelonging: (
        lon: number,
        lat: number,
      ) => { hits: number; empty: number };
      /** T-029 */
      estimateTravel: (
        lon1: number,
        lat1: number,
        lon2: number,
        lat2: number,
      ) => TravelEstimate;
      routeCosts: () => Array<{ id: string; name: string; summary: string }>;
    };
    /** 验收用源 id / 角色名（land、china、countries、territory），图层 id 是 land-fill 等 */
    function resolveRenderedLayers(map: {
      getLayer: (id: string) => unknown;
      getStyle: () => { layers?: Array<{ id: string; type?: string; source?: string }> } | undefined;
    }, key: string): string[] {
      if (map.getLayer(key)) return [key];
      const layers = map.getStyle()?.layers ?? [];
      const fromSource = layers.filter((l) => l.source === key);
      const fills = fromSource.filter((l) => l.type === "fill");
      if (fills.length) return fills.map((l) => l.id);
      if (fromSource.length) return fromSource.map((l) => l.id);
      if (key === "china" && map.getLayer("china-fill")) return ["china-fill"];
      if (key === "territory") {
        return ["territory-fill", "territory-schematic-fill"].filter((id) =>
          map.getLayer(id),
        );
      }
      return [];
    }
    const api: JzDebug = {
      layers: () => {
        const map = mapRef.current?.getMap();
        const style = map?.getStyle();
        return (style?.layers ?? []).map((l) => l.id);
      },
      rendered: (layerId: string) => {
        /** T-030：隐藏态勿当「地图空白」 */
        if (typeof document !== "undefined" && document.hidden) return null;
        const map = mapRef.current?.getMap();
        if (!map) return 0;
        const ids = resolveRenderedLayers(map, layerId);
        if (!ids.length) return 0;
        try {
          return map.queryRenderedFeatures({ layers: ids }).length;
        } catch {
          return 0;
        }
      },
      year: () => Math.round(yearRef.current),
      setYear: (y: number) => {
        setPlaying(false);
        setAxis("year");
        yearRef.current = y;
        setYear(y);
        /** T-030：纯改年不改选中事件，避免抢镜头 */
      },
      setZoom: (z: number) => {
        mapRef.current?.getMap()?.easeTo({ zoom: z, duration: 0 });
        setMapZoom(z);
      },
      flyTo: (lon: number, lat: number, z?: number) => {
        mapRef.current?.flyTo({
          center: [lon, lat],
          zoom: z ?? 4,
          duration: 0,
        });
        if (typeof z === "number") setMapZoom(z);
      },
      snapshotsShown: () => {
        if (territoryModeRef.current !== "snapshot" || !territoryDataRef.current) {
          return null;
        }
        const powers: string[] = [];
        let group = "?";
        for (const f of territoryDataRef.current.features) {
          const p = (f.properties ?? {}) as {
            snapshot?: string;
            power?: string;
          };
          if (p.snapshot) group = String(p.snapshot);
          if (p.power) powers.push(p.power);
        }
        return { group, powers };
      },
      schematicShown: () => territoryModeRef.current === "schematic",
      hostPower: () => hostPowerRef.current,
      powerBrowse: () => powerBrowseRef.current,
      setPowerBrowse: (p: string | null) => setPowerBrowse(p),
      powerEventTitles: () => powerEventsRef.current.map((e) => e.title),
      selectedId: () => selectedRef.current?.id ?? null,
      selectEvent: (id: string) => {
        const ev = timelineAll.find((e) => e.id === id);
        if (!ev) return false;
        setPlaying(false);
        setStoryId(null);
        /** 走「按年」路径，避免 timeline 过滤导致 index 对不上 */
        setAxis("year");
        setYear(ev.year);
        yearRef.current = ev.year;
        setFocusPlaceId(ev.placeId);
        const i = timelineAll.findIndex((e) => e.id === id);
        if (i >= 0) setIndex(i);
        return true;
      },
      /** T-028 */
      queryBelonging: (lon: number, lat: number) => {
        const r = academicBelongingAt(lon, lat);
        setBelonging(r);
        setFocusPlaceId(null);
        setDrawerRight(true);
        return {
          hits: r.rows.filter((x) => x.kind === "hit").length,
          empty: r.rows.filter((x) => x.kind === "empty").length,
        };
      },
      /** T-029 */
      estimateTravel: (lon1, lat1, lon2, lat2) =>
        estimateTravel(haversineKm(lon1, lat1, lon2, lat2)),
      routeCosts: () =>
        marchRoutes
          .map((r) => {
            const travel = estimatePath(
              r.waypoints.map((w) => [w.lon, w.lat] as [number, number]),
            );
            if (!travel) return null;
            return { id: r.id, name: r.name, summary: travel.summary };
          })
          .filter((x): x is { id: string; name: string; summary: string } =>
            Boolean(x),
          ),
    };
    (window as unknown as { __jzDebug?: JzDebug }).__jzDebug = api;
    return () => {
      delete (window as unknown as { __jzDebug?: JzDebug }).__jzDebug;
    };
  }, [timelineAll, timeline]);

  /** `/` 聚焦搜索，`Esc` 清空并失焦（T-005） */
  useEffect(() => {
    function onKey(ev: KeyboardEvent) {
      const tag = (ev.target as HTMLElement | null)?.tagName;
      const typing =
        tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" ||
        (ev.target as HTMLElement | null)?.isContentEditable;
      if (ev.key === "/" && !typing && !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
        ev.preventDefault();
        setSearchOpen(true);
        searchRef.current?.focus();
        return;
      }
      if (ev.key === "Escape") {
        setQuery("");
        setSearchOpen(false);
        searchRef.current?.blur();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function applySearchHit(hit: SearchHit) {
    if (hit.kind === "place") {
      setFocusPersonId(null);
      setFocusPersonName(null);
      flyPlace(hit.place);
      setSearchOpen(false);
      return;
    }
    if (hit.kind === "event") {
      setFocusPersonId(null);
      setFocusPersonName(null);
      setPlaying(false);
      goToEvent(hit.event.id);
      setQuery("");
      setSearchOpen(false);
      return;
    }
    if (hit.kind === "person") {
      setFocusPlaceId(null);
      setFocusPersonId(hit.personId || null);
      setFocusPersonName(hit.name);
      setQuery("");
      setSearchOpen(false);
      setDrawerRight(true);
      return;
    }
    // route：跳到路线起点年与首个航点
    setFocusPersonId(null);
    setFocusPersonName(null);
    setPlaying(false);
    const wp = hit.route.waypoints[0];
    if (hit.route.eventId) {
      goToEvent(hit.route.eventId);
    } else {
      setYear(hit.route.from);
      const near = nearestEventAtOrBefore(timeline, hit.route.from);
      if (near) {
        const i = timeline.findIndex((e) => e.id === near.id);
        if (i >= 0) setIndex(i);
      }
    }
    if (wp) {
      mapRef.current?.flyTo({
        center: [wp.lon, wp.lat],
        zoom: 4.6,
        duration: 800,
      });
    }
    setQuery("");
    setSearchOpen(false);
  }

  /** T-024：棋子停在事件地点时弹出对应事件卡 */
  useEffect(() => {
    for (const p of routePieces) {
      if (p.atEventPlace && p.eventId && selected?.id !== p.eventId) {
        goToEvent(p.eventId);
        break;
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- goToEvent 稳定闭包；只跟棋子/选中走
  }, [routePieces, selected?.id]);

  /** T-027：容器尺寸变化时 map.resize（窗口缩放 / 侧栏开合） */
  useEffect(() => {
    const el = mapBoxRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => {
      mapRef.current?.getMap()?.resize();
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  /**
   * T-027 / T-030：有快照则 fitBounds；无快照跟事件地点。
   * 只在选事件 / 切轴 / 故事 / 疆域模式变化时取景；纯拖年份或派生 territoryData
   * 刷新不抢镜头。
   */
  useEffect(() => {
    if (activeStoryStep) return;
    const map = mapRef.current;
    if (!map) return;
    const key = `${selected?.id ?? ""}|${axis}|${territoryMode}`;
    if (frameKeyRef.current === key) return;
    if (territoryMode === "snapshot" && territoryData?.features?.length) {
      const box = bboxOfFeatures(territoryData.features);
      if (box) {
        map.fitBounds(
          [
            [box[0], box[1]],
            [box[2], box[3]],
          ],
          { padding: 56, duration: 700, maxZoom: 5.2 },
        );
        frameKeyRef.current = key;
        return;
      }
    }
    if (!selected) {
      frameKeyRef.current = key;
      return;
    }
    const place = placeById(selected.placeId);
    if (!place) return;
    map.flyTo({
      center: [place.lon, place.lat],
      zoom: Math.max(map.getZoom(), 4.0),
      duration: 700,
    });
    frameKeyRef.current = key;
  }, [
    selected?.id,
    axis,
    activeStoryStep,
    territoryMode,
    territoryData,
  ]);

  useEffect(() => {
    if (!activeStory || !activeStoryStep) return;
    setPlaying(false);
    setAxis("year");
    setYear(activeStoryStep.year);
    if (activeStoryStep.eventId) {
      const i = timeline.findIndex((e) => e.id === activeStoryStep.eventId);
      if (i >= 0) {
        setIndex(i);
        setFocusPlaceId(timeline[i]!.placeId);
      }
    }
    mapRef.current?.flyTo({
      center: [activeStoryStep.view.lon, activeStoryStep.view.lat],
      zoom: activeStoryStep.view.zoom,
      duration: 900,
    });
  }, [storyId, storyStep, activeStory, activeStoryStep, timeline]);

  function goToEvent(id: string) {
    const i = timeline.findIndex((e) => e.id === id);
    if (i < 0) return;
    setStoryId(null);
    setIndex(i);
    setYear(timeline[i]!.year);
    setFocusPlaceId(timeline[i]!.placeId);
  }

  function openStory(id: string) {
    setPlaying(false);
    setStoryId(id);
    setStoryStep(0);
  }

  function closeStory() {
    setStoryId(null);
    setStoryStep(0);
  }

  function selectEra(id: string) {
    const first = timeline.find((e) => e.eraId === id);
    if (first) goToEvent(first.id);
  }

  function flyPlace(place: Place) {
    setStoryId(null);
    setFocusPlaceId(place.id);
    setBelonging(academicBelongingAt(place.lon, place.lat));
    setDrawerRight(true);
    setQuery("");
    mapRef.current?.flyTo({
      center: [place.lon, place.lat],
      zoom: 5.2,
      duration: 800,
    });
  }

  const progress =
    axis === "event"
      ? timeline.length <= 1
        ? 1
        : index / (timeline.length - 1)
      : yearMax === yearMin
        ? 1
        : (year - yearMin) / (yearMax - yearMin);

  const focusPlace = focusPlaceId ? placeById(focusPlaceId) : null;
  const panelPlace = selected ? placeById(selected.placeId) : focusPlace;
  /** T-028：地点剖面的历代归属（同坐标） */
  const placeBelonging = useMemo(() => {
    if (!focusPlace) return null;
    return academicBelongingAt(focusPlace.lon, focusPlace.lat);
  }, [focusPlace]);

  return (
    <div className="flex h-screen flex-col text-ink">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-line px-6 py-3">
        <div>
          <p className="text-xs tracking-[0.35em] text-muted uppercase">
            Jiuzhou
          </p>
          <h1 className="text-3xl font-semibold tracking-wide text-accent">
            九州
          </h1>
          <p className="mt-1 max-w-xl text-sm text-muted">
            年份色块扫史 · 古今地名对照 · 行军与模块提亮。
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex overflow-hidden rounded-md border border-line text-sm">
            {(
              [
                ["year", "按年"],
                ["event", "按事件"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={cn(
                  "px-2.5 py-1.5",
                  axis === id ? "bg-accent-soft text-accent" : "bg-surface",
                )}
                onClick={() => setAxis(id)}
              >
                {label}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="rounded-md border border-line bg-surface px-3 py-1.5 text-sm"
            onClick={() => {
              if (axis === "event") {
                setIndex((i) => Math.max(0, i - 1));
                setYear(timeline[Math.max(0, index - 1)]?.year ?? year);
              } else {
                const prev = [...timeline].reverse().find((e) => e.year < year);
                if (prev) goToEvent(prev.id);
              }
            }}
          >
            上一条
          </button>
          <button
            type="button"
            className={cn(
              "rounded-md px-4 py-1.5 text-sm font-medium",
              playing ? "bg-era text-white" : "bg-accent text-white",
            )}
            onClick={() => {
              if (!playing && axis === "event" && index >= timeline.length - 1) {
                setIndex(0);
                setYear(timeline[0].year);
              }
              setPlaying((p) => !p);
            }}
          >
            {playing ? "暂停" : "自动播放"}
          </button>
          <button
            type="button"
            className="rounded-md border border-line bg-surface px-3 py-1.5 text-sm"
            onClick={() => {
              if (axis === "event") {
                const n = Math.min(timeline.length - 1, index + 1);
                setIndex(n);
                setYear(timeline[n].year);
              } else {
                const next = timeline.find((e) => e.year > year);
                if (next) goToEvent(next.id);
              }
            }}
          >
            下一条
          </button>
          <div className="flex overflow-hidden rounded-md border border-line text-sm">
            {YEAR_RATES.map((s) => (
              <button
                key={s.id}
                type="button"
                className={cn(
                  "px-2 py-1.5",
                  speedId === s.id ? "bg-accent-soft text-accent" : "bg-surface",
                )}
                onClick={() => setSpeedId(s.id)}
              >
                {s.label}
              </button>
            ))}
          </div>
          <span className="text-xs text-muted tabular-nums">
            {axis === "event"
              ? `${index + 1}/${timeline.length}`
              : formatYear(displayYear)}
          </span>
          <button
            type="button"
            className={cn(
              "rounded-md border px-3 py-1.5 text-sm",
              compareMode
                ? "border-accent bg-accent-soft text-accent"
                : "border-line bg-surface",
            )}
            onClick={() => {
              if (!compareMode) {
                setLeftYear(displayYear);
                const eraEnd = era?.to ?? displayYear + 200;
                setRightYear(Math.min(yearMax, eraEnd));
                setPlaying(false);
              }
              setCompareMode((v) => !v);
            }}
          >
            对比
          </button>
          <div className="flex overflow-hidden rounded-md border border-line text-sm">
            {(
              [
                ["historic", "古名"],
                ["modern", "今名"],
                ["both", "双显"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={cn(
                  "px-2 py-1.5",
                  nameMode === id ? "bg-accent-soft text-accent" : "bg-surface",
                )}
                onClick={() => setNameMode(id)}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="relative w-[min(18rem,100%)]">
            <input
              ref={searchRef}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setSearchOpen(true);
              }}
              onFocus={() => setSearchOpen(true)}
              onBlur={() => {
                window.setTimeout(() => setSearchOpen(false), 160);
              }}
              placeholder="搜索地名 / 事件 / 人物  /"
              className="w-full rounded-md border border-line bg-surface px-3 py-1.5 text-sm"
              aria-label="搜索"
            />
            {searchOpen && query.trim() && (
              <ul className="absolute right-0 z-30 mt-1 max-h-72 w-[min(22rem,90vw)] overflow-y-auto rounded-md border border-line bg-surface py-1 shadow-lg">
                {searchHits.length === 0 && (
                  <li className="px-3 py-2 text-xs text-muted">无匹配</li>
                )}
                {searchHits.map((hit, i) => (
                  <li key={`${hit.kind}-${i}-${hit.label}`}>
                    <button
                      type="button"
                      className="flex w-full items-start gap-2 px-3 py-1.5 text-left text-sm hover:bg-line/50"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => applySearchHit(hit)}
                    >
                      <span
                        className={cn(
                          "mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px]",
                          hit.kind === "place" && "bg-era/15 text-era",
                          hit.kind === "event" && "bg-accent-soft text-accent",
                          hit.kind === "person" && "bg-line text-muted",
                          hit.kind === "route" && "bg-era/10 text-era",
                        )}
                      >
                        {hit.kind === "place"
                          ? "地点"
                          : hit.kind === "event"
                            ? "事件"
                            : hit.kind === "person"
                              ? "人物"
                              : "路线"}
                      </span>
                      <span className="min-w-0 font-medium leading-snug">
                        {hit.label}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </header>

      <div className="border-b border-line bg-surface/70 px-6 py-2">
        <div className="mb-1 flex justify-between text-[11px] text-muted">
          <span>{formatYear(yearMin)}</span>
          <span className="text-era">
            {formatYear(displayYear)}
            {selected ? ` · ${selected.title}` : ""}
          </span>
          <span>{formatYear(yearMax)}</span>
        </div>
        {/* 阶段色带 */}
        <div className="relative mb-1 flex h-2.5 overflow-hidden rounded-sm">
          {atlas.eras.map((e, i) => {
            const span = Math.max(1, yearMax - yearMin);
            const left = ((e.from - yearMin) / span) * 100;
            const width = ((e.to - e.from) / span) * 100;
            return (
              <button
                key={e.id}
                type="button"
                title={`${e.title} ${formatYear(e.from)}–${formatYear(e.to)}`}
                className="absolute inset-y-0 border-r border-page/40 last:border-0"
                style={{
                  left: `${left}%`,
                  width: `${Math.max(width, 0.4)}%`,
                  backgroundColor: ERA_BAND_COLORS[i % ERA_BAND_COLORS.length],
                }}
                onClick={() => {
                  setPlaying(false);
                  selectEra(e.id);
                }}
              />
            );
          })}
        </div>
        {/* 事件密度柱（按 kind 堆叠） */}
        <div className="relative mb-1 flex h-8 items-end gap-px">
          {densityBins.bins.map((bin, i) => {
            const total = EVENT_KINDS.reduce((s, k) => s + bin[k], 0);
            const h =
              total === 0 ? 0 : Math.max(2, (total / densityBins.maxH) * 100);
            return (
              <div
                key={i}
                className="flex min-w-0 flex-1 flex-col-reverse"
                style={{ height: `${h}%` }}
                title={`${total} 事件`}
              >
                {EVENT_KINDS.map((k) =>
                  bin[k] > 0 ? (
                    <div
                      key={k}
                      style={{
                        height: `${(bin[k] / total) * 100}%`,
                        backgroundColor: KIND_COLORS[k],
                        opacity: kindOn.has(k) ? 0.85 : 0.15,
                      }}
                    />
                  ) : null,
                )}
              </div>
            );
          })}
        </div>
        <div className="relative h-2 rounded-full bg-line/80">
          <div
            className="absolute inset-y-0 left-0 rounded-full bg-accent transition-[width] duration-500"
            style={{ width: `${progress * 100}%` }}
          />
          <input
            type="range"
            min={axis === "event" ? 0 : yearMin}
            max={
              axis === "event"
                ? Math.max(0, timeline.length - 1)
                : yearMax
            }
            value={
              axis === "event"
                ? Math.min(index, Math.max(0, timeline.length - 1))
                : year
            }
            onChange={(e) => {
              setPlaying(false);
              const v = Number(e.target.value);
              if (axis === "event") {
                setIndex(v);
                setYear(timeline[v]?.year ?? year);
              } else {
                /** T-030：按年 scrub 只改年，不改选中事件、不抢镜头 */
                setYear(v);
              }
            }}
            className="absolute inset-0 w-full cursor-pointer opacity-0"
            aria-label="时间轴"
          />
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          {EVENT_KINDS.map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => toggleKind(k)}
              className={cn(
                "rounded border px-2 py-0.5 text-[11px] transition",
                kindOn.has(k)
                  ? "border-transparent text-white"
                  : "border-line bg-surface text-muted opacity-50",
              )}
              style={
                kindOn.has(k)
                  ? { backgroundColor: KIND_COLORS[k] }
                  : undefined
              }
            >
              {k}
              <span className="ml-1 opacity-80">
                {timelineAll.filter((e) => eventKindOf(e) === k).length}
              </span>
            </button>
          ))}
          <button
            type="button"
            className="rounded border border-line px-2 py-0.5 text-[11px] text-muted"
            onClick={() => setKindOn(new Set(EVENT_KINDS))}
          >
            全选
          </button>
        </div>
        {selected?.compare && (
          <div className="mt-2 flex items-center gap-2 text-xs">
            <span className="text-muted">{selected.compare.label}</span>
            <button
              type="button"
              className={cn(
                "rounded border px-2 py-0.5",
                !compareAfter
                  ? "border-accent bg-accent-soft text-accent"
                  : "border-line",
              )}
              onClick={() => setCompareAfter(false)}
            >
              前 {formatYear(selected.compare.beforeYear)}
            </button>
            <button
              type="button"
              className={cn(
                "rounded border px-2 py-0.5",
                compareAfter
                  ? "border-accent bg-accent-soft text-accent"
                  : "border-line",
              )}
              onClick={() => setCompareAfter(true)}
            >
              后 {formatYear(selected.compare.afterYear)}
            </button>
          </div>
        )}
      </div>

      <div className="relative flex min-h-0 flex-1">
        <div className="absolute left-2 top-2 z-10 hidden gap-1 max-[899px]:flex">
          <button
            type="button"
            className="rounded border border-line bg-surface/95 px-2 py-1 text-xs shadow"
            onClick={() => setDrawerLeft((v) => !v)}
          >
            阶段
          </button>
          <button
            type="button"
            className="rounded border border-line bg-surface/95 px-2 py-1 text-xs shadow"
            onClick={() => setDrawerRight((v) => !v)}
          >
            详情
          </button>
        </div>
        <aside
          className={cn(
            "flex w-56 shrink-0 flex-col gap-1 overflow-y-auto border-r border-line bg-surface/80 p-3",
            "max-[899px]:absolute max-[899px]:inset-y-0 max-[899px]:left-0 max-[899px]:z-20 max-[899px]:shadow-lg",
            "max-[899px]:transition-transform",
            drawerLeft
              ? "max-[899px]:translate-x-0"
              : "max-[899px]:-translate-x-full",
          )}
        >
          <p className="mb-2 px-2 text-xs tracking-widest text-muted">大阶段</p>
          {atlas.eras.map((e) => (
            <button
              key={e.id}
              type="button"
              onClick={() => {
                setPlaying(false);
                selectEra(e.id);
              }}
              className={cn(
                "rounded-md px-3 py-2 text-left text-sm transition",
                e.id === era.id
                  ? "bg-accent-soft text-accent"
                  : "text-ink hover:bg-line/50",
              )}
            >
              <span className="block font-medium">{e.title}</span>
              <span className="text-xs text-muted">
                {formatYear(e.from)} – {formatYear(e.to)}
              </span>
            </button>
          ))}
          <div className="mt-4 border-t border-line pt-3">
            <p className="mb-1 px-2 text-xs tracking-widest text-muted">
              图层
            </p>
            <label className="mb-1 flex cursor-pointer items-center gap-2 px-2 text-xs">
              <input
                type="checkbox"
                checked={showCapitals}
                onChange={(e) => setShowCapitals(e.target.checked)}
                className="accent-[var(--accent)]"
              />
              都城迁移
              {showCapitals && liveCapitals.mains.length > 0 && (
                <span className="text-muted">
                  · {liveCapitals.mains.length} 主都
                </span>
              )}
            </label>
            <label className="mb-1 flex cursor-pointer items-center gap-2 px-2 text-xs">
              <input
                type="checkbox"
                checked={paperAmbience}
                onChange={(e) => setPaperAmbience(e.target.checked)}
                className="accent-[var(--accent)]"
              />
              纸本质感
            </label>
            <label className="mb-2 flex cursor-pointer items-center gap-2 px-2 text-xs">
              <input
                type="checkbox"
                checked={showLandmarks}
                onChange={(e) => setShowLandmarks(e.target.checked)}
                className="accent-[var(--accent)]"
              />
              山川注记
              {showLandmarks && landmarkLabelIds.length > 0 && (
                <span className="text-muted">· {landmarkLabelIds.length}</span>
              )}
            </label>
            <p className="mb-1 px-2 text-[10px] tracking-widest text-muted">
              城邑符号
            </p>
            <ul className="mb-3 grid grid-cols-2 gap-x-2 gap-y-1 px-2 text-[11px] text-ink/85">
              {PLACE_GLYPH_LEGEND.map(({ kind, label }) => (
                <li key={kind} className="flex items-center gap-1.5">
                  <PlaceGlyph kind={kind} alive />
                  <span>{label}</span>
                </li>
              ))}
            </ul>
            <p className="mb-1 px-2 text-[10px] tracking-widest text-muted">
              精度（数据可靠度）
            </p>
            <ul className="mb-3 space-y-1 px-2 text-[11px] text-ink/85">
              {(
                [
                  ["academic", "bg-[#7c6a4a]/40", "border-[#5c4a32]"],
                  ["snapshot", "bg-[#e08a3c]/45", "border-[#b5483a]"],
                  ["schematic", "bg-[#9a3412]/15", "border-[#9a3412]"],
                ] as const
              ).map(([tier, fill, border]) => (
                <li key={tier} className="flex items-start gap-2">
                  <span
                    className={cn(
                      "mt-0.5 h-3 w-4 shrink-0 rounded-[2px]",
                      fill,
                      PRECISION_META[tier].border === "dashed"
                        ? "border border-dashed"
                        : "border",
                      border,
                    )}
                  />
                  <span>
                    <span className="font-medium">
                      {PRECISION_META[tier].label}
                    </span>
                    <span className="block text-[10px] leading-snug text-muted">
                      {tier === "academic"
                        ? "学术层；Hartwell 标近似"
                        : tier === "snapshot"
                          ? "手绘多势力快照"
                          : "虚线阶段框"}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
            <label className="mb-3 block px-2 text-[11px] text-ink/85">
              <span className="flex items-center justify-between gap-2">
                <span className="tracking-widest text-muted">学术层透明度</span>
                <span className="tabular-nums text-muted">
                  {Math.round(academicOpacity * 100)}%
                </span>
              </span>
              <input
                type="range"
                min={0}
                max={150}
                step={5}
                value={Math.round(academicOpacity * 100)}
                onChange={(e) =>
                  setAcademicOpacity(Number(e.target.value) / 100)
                }
                className="mt-1 w-full accent-[var(--color-accent,#b5483a)]"
                aria-label="学术层不透明度"
              />
            </label>
            <p className="mb-1 px-2 text-xs tracking-widest text-muted">
              主题叙事
            </p>
            <ul className="mb-3 space-y-0.5 px-1">
              {stories.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    className={cn(
                      "w-full rounded px-2 py-1.5 text-left text-xs transition",
                      storyId === s.id
                        ? "bg-accent-soft text-accent"
                        : "hover:bg-line/50",
                    )}
                    onClick={() =>
                      storyId === s.id ? closeStory() : openStory(s.id)
                    }
                    title={s.tagline}
                  >
                    <span className="font-medium">{s.title}</span>
                    <span className="mt-0.5 block text-[10px] leading-snug text-muted">
                      {s.tagline}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        <main className="relative min-h-0 min-w-0 flex-1">
          {compareMode && (
            <CompareMaps
              leftYear={leftYear}
              rightYear={rightYear}
              onLeftYear={setLeftYear}
              onRightYear={setRightYear}
              coastline={coastline}
              territories={territories}
              geoFeatures={geoFeatures}
              capitals={allCapitals}
              places={atlas.places}
              leftEraTerritoryId={
                atlas.eras.find(
                  (e) => leftYear >= e.from && leftYear <= e.to,
                )?.territoryId
              }
              rightEraTerritoryId={
                atlas.eras.find(
                  (e) => rightYear >= e.from && rightYear <= e.to,
                )?.territoryId
              }
              onClose={() => setCompareMode(false)}
            />
          )}
          <div ref={mapBoxRef} className="absolute inset-0">
          <MapGl
            ref={mapRef}
            initialViewState={CHINA_VIEW}
            mapStyle={PAPER_STYLE}
            style={{ width: "100%", height: "100%" }}
            attributionControl={false}
            interactiveLayerIds={[
              "leads-arc-line",
              "academic-fill",
              "territory-fill",
              "territory-schematic-fill",
            ]}
            cursor="pointer"
            onLoad={() => {
              const m = mapRef.current?.getMap();
              m?.resize();
              if (m) setMapZoom(m.getZoom());
            }}
            onMove={(e) => setMapZoom(e.viewState.zoom)}
            onMouseMove={(e) => {
              const acad = e.features?.find(
                (x) => x.layer?.id === "academic-fill",
              );
              if (acad?.properties) {
                const p = acad.properties as AcademicProps;
                const approx =
                  Boolean(p.approximate) || String(p.source) === "hartwell-v5";
                setPrecisionHover({
                  tier: "academic",
                  title: approx
                    ? `${p.name ?? "学术政区"} · 近似`
                    : String(p.name ?? "学术政区"),
                });
                return;
              }
              const terr = e.features?.find(
                (x) =>
                  x.layer?.id === "territory-fill" ||
                  x.layer?.id === "territory-schematic-fill",
              );
              if (terr?.properties) {
                const power = String(terr.properties.power ?? "疆域");
                const schem = terr.layer?.id === "territory-schematic-fill";
                setPrecisionHover({
                  tier: schem ? "schematic" : "snapshot",
                  title: power,
                });
                return;
              }
              setPrecisionHover(null);
            }}
            onMouseLeave={() => setPrecisionHover(null)}
            onClick={(e) => {
              const arc = e.features?.find(
                (x) => x.layer?.id === "leads-arc-line",
              );
              const nextId = arc?.properties?.eventId as string | undefined;
              if (nextId) {
                setPlaying(false);
                setAcademicPick(null);
                setPrecisionPick(null);
                setBelonging(null);
                goToEvent(nextId);
                return;
              }
              const acad = e.features?.find(
                (x) => x.layer?.id === "academic-fill",
              );
              if (acad?.properties) {
                const p = acad.properties as AcademicProps;
                const approximate =
                  Boolean(p.approximate) ||
                  String(p.source) === "hartwell-v5";
                setAcademicPick({
                  name: String(p.name ?? ""),
                  name_py: p.name_py ? String(p.name_py) : undefined,
                  type_ch: p.type_ch ? String(p.type_ch) : undefined,
                  fromYear: Number(p.fromYear),
                  toYear: Number(p.toYear),
                  source: String(p.source ?? ""),
                  sliceId: String(p.sliceId ?? ""),
                  sliceTitle: String(p.sliceTitle ?? ""),
                  approximate,
                });
                setPrecisionPick({
                  title: String(p.name ?? "学术政区"),
                  tier: "academic",
                  note: approximate
                    ? "Hartwell 县域拼接近似，西部/关中等可能有空白。"
                    : undefined,
                });
                setBelonging(null);
                return;
              }
              const terr = e.features?.find(
                (x) =>
                  x.layer?.id === "territory-fill" ||
                  x.layer?.id === "territory-schematic-fill",
              );
              if (terr?.properties) {
                const power = String(terr.properties.power ?? "疆域");
                const schem = terr.layer?.id === "territory-schematic-fill";
                setAcademicPick(null);
                setBelonging(null);
                setPrecisionPick({
                  title: power,
                  tier: schem ? "schematic" : "snapshot",
                });
                if (!schem && power) {
                  setPowerBrowse(power);
                  setDrawerRight(true);
                } else {
                  setPowerBrowse(null);
                }
                return;
              }
              /** T-028：空白处 → 历代归属 */
              setAcademicPick(null);
              setPrecisionPick(null);
              setPowerBrowse(null);
              setFocusPlaceId(null);
              const { lng, lat } = e.lngLat;
              setBelonging(academicBelongingAt(lng, lat));
              setDrawerRight(true);
            }}
          >
            <NavigationControl position="top-right" showCompass={false} />
            <Source id="land" type="geojson" data={land}>
              <Layer
                id="land-fill"
                type="fill"
                paint={{
                  "fill-color": MAP_TOKENS.landFill,
                  "fill-opacity": 1,
                }}
              />
            </Source>
            <Source id="countries" type="geojson" data={countries}>
              <Layer
                id="neighbor-fill"
                type="fill"
                filter={["==", ["get", "role"], "neighbor"]}
                paint={{
                  "fill-color": MAP_TOKENS.neighborLand,
                  "fill-opacity": 0.95,
                }}
              />
              <Layer
                id="china-fill"
                type="fill"
                filter={["==", ["get", "role"], "china"]}
                paint={{
                  "fill-color": MAP_TOKENS.landFill,
                  "fill-opacity": 1,
                }}
              />
              <Layer
                id="country-line"
                type="line"
                paint={{
                  "line-color": MAP_TOKENS.countryLine,
                  "line-width": 0.8,
                  "line-opacity": 0.45,
                  "line-dasharray": [2, 1.5],
                }}
              />
            </Source>
            {/* NE 灰度晕渲：压在陆面色块上，低透明近似乘算（T-007） */}
            <Source
              id="relief"
              type="image"
              url={reliefUrl}
              coordinates={[
                [reliefMeta.west, reliefMeta.north],
                [reliefMeta.east, reliefMeta.north],
                [reliefMeta.east, reliefMeta.south],
                [reliefMeta.west, reliefMeta.south],
              ]}
            >
              <Layer
                id="relief-shade"
                type="raster"
                paint={{
                  "raster-opacity": reliefMeta.opacity ?? 0.35,
                  "raster-contrast": 0.12,
                  "raster-saturation": -1,
                  "raster-fade-duration": 0,
                }}
              />
            </Source>
            <Source id="coast" type="geojson" data={coastline}>
              <Layer
                id="coast-glow-wide"
                type="line"
                paint={{
                  "line-color": "#e8f2f4",
                  "line-width": 14,
                  "line-blur": 10,
                  "line-opacity": 0.28,
                }}
              />
              <Layer
                id="coast-glow-mid"
                type="line"
                paint={{
                  "line-color": "#d0e4e8",
                  "line-width": 8,
                  "line-blur": 7,
                  "line-opacity": 0.38,
                }}
              />
              <Layer
                id="coast-glow-near"
                type="line"
                paint={{
                  "line-color": "#b8d4da",
                  "line-width": 3,
                  "line-blur": 4,
                  "line-opacity": 0.5,
                }}
              />
              <Layer
                id="coast-line"
                type="line"
                paint={{
                  "line-color": MAP_TOKENS.coast,
                  "line-width": 1.0,
                  "line-opacity": 0.7,
                }}
              />
            </Source>
            <Source id="lakes" type="geojson" data={lakes}>
              <Layer
                id="lakes-fill"
                type="fill"
                paint={{
                  "fill-color": MAP_TOKENS.lake,
                  "fill-opacity": 0.75,
                }}
              />
              <Layer
                id="lakes-line"
                type="line"
                paint={{
                  "line-color": MAP_TOKENS.lakeLine,
                  "line-width": 0.7,
                  "line-opacity": 0.6,
                }}
              />
            </Source>
            <Source id="hydro" type="geojson" data={hydro}>
              <Layer
                id="hydro-rivers-casing"
                type="line"
                filter={["!=", ["get", "kind"], "canal"]}
                paint={{
                  "line-color": "#ffffff",
                  "line-width": [
                    "case",
                    [
                      "in",
                      ["get", "id"],
                      [
                        "literal",
                        ["huanghe", "changjiang", "huaihe", "zhujiang"],
                      ],
                    ],
                    3.6,
                    2.2,
                  ],
                  "line-opacity": 0.55,
                }}
              />
              <Layer
                id="hydro-rivers"
                type="line"
                filter={["!=", ["get", "kind"], "canal"]}
                paint={{
                  "line-color": [
                    "case",
                    ["in", ["get", "id"], ["literal", [...litHydro]]],
                    MAP_TOKENS.highlight,
                    MAP_TOKENS.river,
                  ],
                  "line-width": [
                    "case",
                    ["in", ["get", "id"], ["literal", [...litHydro]]],
                    3.2,
                    [
                      "case",
                      [
                        "in",
                        ["get", "id"],
                        [
                          "literal",
                          ["huanghe", "changjiang", "huaihe", "zhujiang"],
                        ],
                      ],
                      2.4,
                      1.2,
                    ],
                  ],
                  "line-opacity": 0.85,
                }}
              />
              <Layer
                id="hydro-canal"
                type="line"
                filter={["==", ["get", "kind"], "canal"]}
                paint={{
                  "line-color": [
                    "case",
                    ["in", ["get", "id"], ["literal", [...litHydro]]],
                    MAP_TOKENS.highlight,
                    MAP_TOKENS.canal,
                  ],
                  "line-width": [
                    "case",
                    ["in", ["get", "id"], ["literal", [...litHydro]]],
                    3.2,
                    2.1,
                  ],
                  "line-opacity": 0.82,
                  "line-dasharray": [2, 1.4],
                }}
              />
            </Source>
            <Source id="corridors" type="geojson" data={corridors}>
              <Layer
                id="corridors-line"
                type="line"
                paint={{
                  "line-color": [
                    "case",
                    ["in", ["get", "id"], ["literal", [...litCorridors]]],
                    MAP_TOKENS.highlight,
                    MAP_TOKENS.corridor,
                  ],
                  "line-width": [
                    "case",
                    ["in", ["get", "id"], ["literal", [...litCorridors]]],
                    2.8,
                    1.25,
                  ],
                  "line-opacity": [
                    "case",
                    ["in", ["get", "id"], ["literal", [...litCorridors]]],
                    0.9,
                    0.55,
                  ],
                  "line-dasharray": [1.5, 2],
                }}
              />
            </Source>
            <Source id="growing-features" type="geojson" data={featureData}>
              <Layer
                id="features-line"
                type="line"
                paint={{
                  "line-color": [
                    "match",
                    ["get", "group"],
                    "yellow-river",
                    "#b45309",
                    "canal",
                    MAP_TOKENS.canal,
                    "wall",
                    "#57534e",
                    "works",
                    "#0f766e",
                    MAP_TOKENS.era,
                  ],
                  "line-width": [
                    "case",
                    ["==", ["get", "lit"], 1],
                    3.6,
                    ["match", ["get", "group"], "yellow-river", 2.6, 2.0],
                  ],
                  "line-opacity": [
                    "case",
                    ["==", ["get", "lit"], 1],
                    0.95,
                    0.75,
                  ],
                }}
              />
            </Source>
            {territoryPaintData && territoryMode === "snapshot" && (
              <Source id="territory" type="geojson" data={territoryPaintData}>
                <Layer
                  id="territory-fill"
                  type="fill"
                  paint={{
                    "fill-color": [
                      "coalesce",
                      ["get", "color"],
                      MAP_TOKENS.territory,
                    ],
                    /** T-021：宿主/浏览政权提亮，其余略淡 */
                    "fill-opacity": [
                      "case",
                      ["==", ["get", "lit"], 1],
                      0.62,
                      ["==", ["get", "dim"], 1],
                      0.22,
                      0.5,
                    ],
                  }}
                />
                <Layer
                  id="territory-gap"
                  type="line"
                  paint={{
                    "line-color": MAP_TOKENS.page,
                    "line-width": 2.2,
                    "line-opacity": 0.9,
                  }}
                />
                <Layer
                  id="territory-line"
                  type="line"
                  paint={{
                    "line-color": [
                      "coalesce",
                      ["get", "edge"],
                      ["get", "color"],
                      MAP_TOKENS.territory,
                    ],
                    "line-width": [
                      "case",
                      ["==", ["get", "lit"], 1],
                      2.8,
                      1.7,
                    ],
                    "line-opacity": [
                      "case",
                      ["==", ["get", "dim"], 1],
                      0.45,
                      0.9,
                    ],
                  }}
                />
              </Source>
            )}
            {territoryPaintData && territoryMode === "schematic" && (
              <Source id="territory-schematic" type="geojson" data={territoryPaintData}>
                <Layer
                  id="territory-schematic-fill"
                  type="fill"
                  paint={{
                    "fill-color": [
                      "coalesce",
                      ["get", "color"],
                      MAP_TOKENS.territory,
                    ],
                    "fill-opacity": 0.14,
                  }}
                />
                <Layer
                  id="territory-schematic-line"
                  type="line"
                  paint={{
                    "line-color": [
                      "coalesce",
                      ["get", "edge"],
                      MAP_TOKENS.territory,
                    ],
                    "line-width": 1.2,
                    "line-opacity": 0.45,
                    "line-dasharray": [2.5, 2],
                  }}
                />
              </Source>
            )}
            {academicData.features.length > 0 && (
              <Source id="academic" type="geojson" data={academicData}>
                <Layer
                  id="academic-fill"
                  type="fill"
                  paint={{
                    "fill-color": [
                      "case",
                      ["==", ["get", "approximate"], true],
                      "#b08968",
                      "#7c6a4a",
                    ],
                    "fill-opacity": [
                      "case",
                      ["==", ["get", "approximate"], true],
                      Math.min(0.55, 0.14 * academicOpacity),
                      Math.min(0.7, 0.2 * academicOpacity),
                    ],
                  }}
                />
                <Layer
                  id="academic-line"
                  type="line"
                  filter={["!=", ["get", "approximate"], true]}
                  paint={{
                    "line-color": "#5c4a32",
                    "line-width": 0.9,
                    "line-opacity": Math.min(1, 0.72 * academicOpacity),
                  }}
                />
                <Layer
                  id="academic-line-approx"
                  type="line"
                  filter={["==", ["get", "approximate"], true]}
                  paint={{
                    "line-color": "#9a7b5a",
                    "line-width": 0.9,
                    "line-opacity": 0.65,
                    "line-dasharray": [1.6, 1.2],
                  }}
                />
              </Source>
            )}
            {mapZoom < 5.8 &&
              powerCentroids.map((c) => (
                <Marker
                  key={`power-${c.power}-${c.lon}`}
                  longitude={c.lon}
                  latitude={c.lat}
                  anchor="center"
                >
                  <span
                    className="pointer-events-none select-none text-[13px] font-semibold tracking-[0.28em]"
                    style={{
                      color: c.color,
                      opacity: mapZoom < 4.2 ? 0.92 : Math.max(0.25, 0.92 - (mapZoom - 4.2) * 0.35),
                      textShadow:
                        "0 0 2px #f3efe6, 1px 0 0 #f3efe6, -1px 0 0 #f3efe6, 0 1px 0 #f3efe6, 0 -1px 0 #f3efe6, 1px 1px 0 #f3efe6, -1px -1px 0 #f3efe6",
                    }}
                  >
                    {c.power}
                  </span>
                </Marker>
              ))}
            {marchRouteData.features.length > 0 && (
              <Source id="march-routes" type="geojson" data={marchRouteData}>
                <Layer
                  id="march-route-line"
                  type="line"
                  paint={{
                    "line-color": [
                      "case",
                      ["==", ["get", "lit"], 1],
                      MAP_TOKENS.highlight,
                      "#c2410c",
                    ],
                    "line-width": [
                      "case",
                      ["==", ["get", "lit"], 1],
                      3.4,
                      2.4,
                    ],
                    "line-opacity": 0.88,
                  }}
                />
              </Source>
            )}
            {belonging && !focusPlace && (
              <Marker
                longitude={belonging.lon}
                latitude={belonging.lat}
                anchor="bottom"
              >
                <div
                  className="h-0 w-0 border-x-[6px] border-b-[10px] border-x-transparent border-b-[#c23a2b] drop-shadow"
                  title="沿革查询点"
                />
              </Marker>
            )}
            {routePieces.map((piece) => (
              <Marker
                key={`piece-${piece.routeId}`}
                longitude={piece.lon}
                latitude={piece.lat}
                anchor="center"
                onClick={(ev) => {
                  ev.originalEvent.stopPropagation();
                  if (piece.eventId) {
                    setPlaying(false);
                    goToEvent(piece.eventId);
                  }
                }}
              >
                <button
                  type="button"
                  className="group flex flex-col items-center gap-0.5 border-0 bg-transparent p-0"
                  title={piece.label}
                >
                  <span
                    className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-[#f3efe6] text-[15px] font-bold text-[#f3efe6] shadow-md ring-2 ring-[#8b1a12]/55"
                    style={{
                      background:
                        "radial-gradient(circle at 35% 30%, #e8573a 0%, #c23a2b 55%, #8b1a12 100%)",
                      fontFamily: "serif",
                    }}
                  >
                    {piece.seal}
                  </span>
                  <span className="max-w-[6.5rem] truncate rounded bg-[#c23a2b]/90 px-1 py-0.5 text-[9px] font-medium text-[#f3efe6] shadow-sm">
                    {piece.label}
                  </span>
                </button>
              </Marker>
            ))}
            {leadsToArcs.lines && (
              <Source id="leads-arc" type="geojson" data={leadsToArcs.lines}>
                <Layer
                  id="leads-arc-line"
                  type="line"
                  paint={{
                    "line-color": MAP_TOKENS.era,
                    "line-width": 2.4,
                    "line-opacity": 0.85,
                    "line-dasharray": [1.2, 1.4],
                  }}
                />
              </Source>
            )}
            {leadsToArcs.labels.map((lb) => (
              <Marker
                key={`lead-${lb.eventId}-${lb.year}`}
                longitude={lb.lon}
                latitude={lb.lat}
                anchor="center"
                onClick={(ev) => {
                  ev.originalEvent.stopPropagation();
                  setPlaying(false);
                  goToEvent(lb.eventId);
                }}
              >
                <button
                  type="button"
                  className="rounded border border-era/40 bg-page/95 px-1.5 py-0.5 text-[10px] text-era shadow-sm hover:bg-accent-soft"
                  title={
                    lb.travel
                      ? `${lb.title} · ${lb.travel.summary}`
                      : lb.title
                  }
                >
                  → {formatYear(lb.year)}
                  {lb.travel ? ` · ${lb.travel.km}km` : ""}
                </button>
              </Marker>
            ))}
            {legacyRouteData && (
              <Source id="legacy-route" type="geojson" data={legacyRouteData}>
                <Layer
                  id="legacy-route-line"
                  type="line"
                  paint={{
                    "line-color": MAP_TOKENS.highlight,
                    "line-opacity": 0.7,
                    "line-width": 3,
                    "line-dasharray": [1.2, 1.2],
                  }}
                />
              </Source>
            )}
            {showCapitals && (
              <>
                <Source
                  id="capital-trail-future"
                  type="geojson"
                  data={capitalTrailGeo.future}
                >
                  <Layer
                    id="capital-trail-future-line"
                    type="line"
                    paint={{
                      "line-color": "#78716c",
                      "line-width": 1.4,
                      "line-opacity": 0.35,
                      "line-dasharray": [2.2, 2.2],
                    }}
                  />
                </Source>
                <Source
                  id="capital-trail-past"
                  type="geojson"
                  data={capitalTrailGeo.past}
                >
                  <Layer
                    id="capital-trail-past-line"
                    type="line"
                    paint={{
                      "line-color": "#1e3a5f",
                      "line-width": 2.2,
                      "line-opacity": 0.72,
                    }}
                  />
                </Source>
                <Source
                  id="capital-trail-hi"
                  type="geojson"
                  data={capitalTrailGeo.highlight}
                >
                  <Layer
                    id="capital-trail-hi-line"
                    type="line"
                    paint={{
                      "line-color": "#9a3412",
                      "line-width": 3.4,
                      "line-opacity": 0.92,
                    }}
                  />
                </Source>
                {liveCapitals.alts.map(({ cap, place }) => (
                  <Marker
                    key={`alt-${cap.id}`}
                    longitude={place.lon}
                    latitude={place.lat}
                    anchor="center"
                    onClick={(ev) => {
                      ev.originalEvent.stopPropagation();
                      flyPlace(place);
                    }}
                  >
                    <div
                      className="capital-alt"
                      title={cap.note ?? `${cap.state} · ${cap.name}`}
                    />
                  </Marker>
                ))}
                {liveCapitals.mains.map(({ cap, place }) => (
                  <Marker
                    key={`main-${cap.id}`}
                    longitude={place.lon}
                    latitude={place.lat}
                    anchor="bottom"
                    onClick={(ev) => {
                      ev.originalEvent.stopPropagation();
                      flyPlace(place);
                    }}
                  >
                    <div
                      className="flex flex-col items-center gap-0.5"
                      title={cap.note ?? `${cap.state} · ${cap.name}`}
                    >
                      <span className="rounded bg-era px-1.5 py-0.5 text-[9px] font-semibold text-white shadow-sm">
                        {cap.state}·{cap.name}
                      </span>
                      <div className="capital-star" />
                    </div>
                  </Marker>
                ))}
              </>
            )}
            {placesGeo.features.map((f) => {
              const id = String(f.properties?.id ?? "");
              const place = placeById(id);
              if (!place) return null;
              const coords = f.geometry.coordinates as [number, number];
              const active = Number(f.properties?.active ?? 0) === 1;
              const alive = Number(f.properties?.alive ?? 1) === 1;
              const kind = placeGlyphKind(place);
              return (
                <Marker
                  key={`glyph-${id}`}
                  longitude={coords[0]}
                  latitude={coords[1]}
                  anchor="center"
                  onClick={(ev) => {
                    ev.originalEvent.stopPropagation();
                    setAcademicPick(null);
                    setPrecisionPick(null);
                    flyPlace(place);
                  }}
                >
                  <button
                    type="button"
                    className="cursor-pointer border-0 bg-transparent p-0"
                    title={`${placeNameAt(place, displayYear)} · ${place.modern}`}
                    aria-label={place.modern}
                  >
                    <PlaceGlyph kind={kind} active={active} alive={alive} />
                  </button>
                </Marker>
              );
            })}
            {showLandmarks &&
              landmarks
                .filter((lm) => landmarkLabelIds.includes(lm.id))
                .map((lm) => {
                  const isBg =
                    lm.kind === "sea" ||
                    lm.kind === "plateau" ||
                    lm.kind === "plain" ||
                    lm.kind === "basin" ||
                    lm.kind === "desert";
                  const fontPx = lm.size >= 3 ? 13 : lm.size >= 2 ? 11 : 10;
                  const tracking =
                    lm.kind === "mountain"
                      ? "0.22em"
                      : isBg
                        ? "0.32em"
                        : "0.12em";
                  const opacity =
                    lm.kind === "sea"
                      ? 0.55
                      : lm.kind === "plateau" || lm.kind === "plain"
                        ? 0.48
                        : lm.kind === "basin" || lm.kind === "desert"
                          ? 0.52
                          : lm.kind === "lake"
                            ? 0.7
                            : 0.78;
                  const color =
                    lm.kind === "sea" || lm.kind === "lake"
                      ? "#3d6a7a"
                      : lm.kind === "desert"
                        ? "#8a6a3a"
                        : "#5c4a32";
                  return (
                    <Marker
                      key={`lm-${lm.id}`}
                      longitude={lm.lon}
                      latitude={lm.lat}
                      anchor="center"
                    >
                      <span
                        className="pointer-events-none select-none whitespace-nowrap font-medium"
                        style={{
                          fontSize: fontPx,
                          letterSpacing: tracking,
                          color,
                          opacity,
                          transform: `rotate(${lm.rotate ?? 0}deg)`,
                          textShadow:
                            "0 0 2px #f3efe6, 1px 0 0 #f3efe6, -1px 0 0 #f3efe6, 0 1px 0 #f3efe6, 0 -1px 0 #f3efe6",
                        }}
                      >
                        {lm.name}
                      </span>
                    </Marker>
                  );
                })}
            {placesGeo.features
              .filter((f) =>
                placeLabelIds.includes(String(f.properties?.id ?? "")),
              )
              .map((f) => {
                const id = String(f.properties?.id ?? "");
                const name = String(f.properties?.name ?? "");
                const secondary = String(f.properties?.secondary ?? "");
                const active = Number(f.properties?.active ?? 0) === 1;
                const coords = f.geometry.coordinates as [number, number];
                const place = placeById(id);
                if (!place) return null;
                return (
                  <Marker
                    key={`lbl-${id}`}
                    longitude={coords[0]}
                    latitude={coords[1]}
                    anchor="top"
                    onClick={(ev) => {
                      ev.originalEvent.stopPropagation();
                      flyPlace(place);
                    }}
                  >
                    <span
                      className={cn(
                        "mt-1 flex max-w-[9rem] flex-col items-center rounded px-1 py-0.5 text-center leading-tight",
                        active
                          ? "bg-accent text-white shadow-sm"
                          : "bg-transparent text-ink",
                      )}
                      style={
                        active
                          ? undefined
                          : {
                              textShadow:
                                "0 0 2px #f3efe6, 1px 0 0 #f3efe6, -1px 0 0 #f3efe6, 0 1px 0 #f3efe6, 0 -1px 0 #f3efe6",
                            }
                      }
                    >
                      <span className="truncate text-[11px] font-medium">
                        {name}
                      </span>
                      {secondary ? (
                        <span
                          className={cn(
                            "truncate text-[9px]",
                            active ? "text-white/80" : "text-muted",
                          )}
                        >
                          {secondary}
                        </span>
                      ) : null}
                    </span>
                  </Marker>
                );
              })}
            {snapshotCapitals.map((c) => (
              <Marker
                key={`snap-cap-${c.place.id}-${c.power}`}
                longitude={c.place.lon}
                latitude={c.place.lat}
                anchor="bottom"
                onClick={(ev) => {
                  ev.originalEvent.stopPropagation();
                  flyPlace(c.place);
                }}
              >
                <span
                  className="mb-3 rounded px-1.5 py-0.5 text-[9px] font-semibold text-white shadow-sm"
                  style={{ backgroundColor: c.color }}
                >
                  {c.power}都·{c.capitalName}
                </span>
              </Marker>
            ))}
            {selected?.people?.[0] && selected.placeId && (
              <Marker
                longitude={
                  placeById(selected.placeId)?.lon ?? CHINA_VIEW.longitude
                }
                latitude={
                  placeById(selected.placeId)?.lat ?? CHINA_VIEW.latitude
                }
                anchor="bottom"
              >
                <span className="mb-5 rounded-full bg-era px-1.5 py-0.5 text-[9px] text-white">
                  {selected.people[0]}
                </span>
              </Marker>
            )}
          </MapGl>
          </div>

          {territoryMode === "schematic" && (
            <div className="pointer-events-none absolute inset-0 z-[5] flex items-center justify-center">
              <span className="rotate-[-18deg] select-none text-6xl font-semibold tracking-[0.4em] text-ink/10">
                示意
              </span>
            </div>
          )}
          {paperAmbience && (
            <>
              <div
                className="pointer-events-none absolute inset-0 z-[4]"
                style={{
                  background:
                    "radial-gradient(ellipse at center, transparent 42%, rgba(42,33,24,0.12) 100%)",
                }}
              />
              <div
                className="pointer-events-none absolute inset-0 z-[4] opacity-[0.05] mix-blend-multiply"
                style={{
                  backgroundImage:
                    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23n)' opacity='0.55'/%3E%3C/svg%3E\")",
                }}
              />
            </>
          )}
          {precisionHover && !precisionPick && (
            <div className="pointer-events-none absolute right-3 top-3 z-10 rounded border border-line/70 bg-page/90 px-2 py-1 text-[11px] shadow-sm">
              <span className="font-medium text-ink">
                {PRECISION_META[precisionHover.tier].label}
              </span>
              <span className="text-muted"> · {precisionHover.title}</span>
            </div>
          )}
          {(precisionPick || academicPick) && (
            <div className="absolute bottom-28 left-4 z-10 max-w-xs rounded-md border border-line bg-surface/95 px-3 py-2 shadow-md">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-ink">
                    {precisionPick?.title ?? academicPick?.name}
                    {academicPick?.type_ch ? (
                      <span className="ml-1 text-xs font-normal text-muted">
                        {academicPick.type_ch}
                      </span>
                    ) : null}
                  </p>
                  {precisionPick && (
                    <p className="mt-0.5 text-xs">
                      <span
                        className={cn(
                          "inline-block rounded px-1 py-0.5 font-medium",
                          precisionPick.tier === "academic" &&
                            "bg-[#7c6a4a]/25 text-[#5c4a32]",
                          precisionPick.tier === "snapshot" &&
                            "bg-accent-soft text-accent",
                          precisionPick.tier === "schematic" &&
                            "bg-line/80 text-muted",
                        )}
                      >
                        {PRECISION_META[precisionPick.tier].label}
                      </span>
                    </p>
                  )}
                  <p className="mt-1 text-[11px] leading-snug text-muted">
                    {precisionPick
                      ? precisionPick.note ??
                        PRECISION_META[precisionPick.tier].tip
                      : null}
                  </p>
                  {academicPick ? (
                    <>
                      {academicPick.name_py ? (
                        <p className="text-xs text-muted">
                          {academicPick.name_py}
                        </p>
                      ) : null}
                      <p className="mt-1 text-xs text-ink/80">
                        {formatYear(academicPick.fromYear)} –{" "}
                        {formatYear(academicPick.toYear)}
                        <span className="text-muted">
                          {" "}
                          · {academicPick.sliceTitle}
                        </span>
                      </p>
                      <p className="text-[11px] text-muted">
                        来源 {academicPick.source}
                        {academicPick.approximate ? " · 近似（Hartwell）" : ""}
                      </p>
                    </>
                  ) : null}
                </div>
                <button
                  type="button"
                  className="text-xs text-muted hover:text-ink"
                  onClick={() => {
                    setAcademicPick(null);
                    setPrecisionPick(null);
                  }}
                >
                  关闭
                </button>
              </div>
            </div>
          )}
          <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-page/95 via-page/70 to-transparent px-4 pb-3 pt-8">
            <div className="pointer-events-auto mx-auto max-w-5xl space-y-1.5">
              <div className="flex items-start gap-2 rounded-md border border-line/60 bg-surface/90 px-3 py-1.5 shadow-sm">
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-era">{era.title}</p>
                  <p
                    className={cn(
                      "max-w-3xl text-xs leading-relaxed text-muted",
                      !eraBlurbOpen && "truncate",
                    )}
                  >
                    {era.blurb}
                    {eraBlurbOpen && (
                      <>
                        {" · 岸线/水系/走廊 · 生长河渠与行军线随年展开"}
                        {territoryMode === "snapshot"
                          ? " · 多势力快照按国分色"
                          : territoryMode === "schematic"
                            ? " · 虚线为示意疆域（非考据）"
                            : ""}
                        {` · 地点 ${visiblePlaces.length}`}
                        {featureData.features.length
                          ? ` · 地理要素 ${featureData.features.length}`
                          : ""}
                        {marchRouteData.features.length
                          ? ` · 行军线 ${marchRouteData.features.length}`
                          : ""}
                      </>
                    )}
                  </p>
                </div>
                <button
                  type="button"
                  className="shrink-0 rounded border border-line px-2 py-0.5 text-[11px] text-muted hover:text-ink"
                  onClick={() => setEraBlurbOpen((v) => !v)}
                >
                  {eraBlurbOpen ? "收起" : "展开"}
                </button>
              </div>
              {activeStory && activeStoryStep && (
                <div className="rounded-md border border-accent/30 bg-surface/95 px-3 py-2 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-xs tracking-widest text-muted">
                      主题 · {activeStory.title}
                      <span className="ml-2 font-normal">
                        {storyStep + 1}/{activeStory.steps.length}
                      </span>
                    </p>
                    <div className="flex gap-1">
                      <button
                        type="button"
                        className="rounded border border-line px-2 py-0.5 text-xs"
                        disabled={storyStep <= 0}
                        onClick={() => setStoryStep((s) => Math.max(0, s - 1))}
                      >
                        上一镜
                      </button>
                      <button
                        type="button"
                        className="rounded border border-line px-2 py-0.5 text-xs"
                        disabled={storyStep >= activeStory.steps.length - 1}
                        onClick={() =>
                          setStoryStep((s) =>
                            Math.min(activeStory.steps.length - 1, s + 1),
                          )
                        }
                      >
                        下一镜
                      </button>
                      <button
                        type="button"
                        className="rounded border border-line px-2 py-0.5 text-xs"
                        onClick={closeStory}
                      >
                        退出
                      </button>
                    </div>
                  </div>
                  <p className="mt-1 text-sm leading-6 text-ink">
                    {activeStoryStep.caption}
                  </p>
                </div>
              )}
              <div className="rounded-md border border-line/60 bg-surface/90 shadow-sm">
                <button
                  type="button"
                  className="flex w-full items-center justify-between gap-2 px-3 py-1.5 text-left text-xs text-muted hover:text-ink"
                  onClick={() => setEventDrawerOpen((v) => !v)}
                >
                  <span>
                    本阶段事件 · {eraEvents.length}
                    {selected ? ` · 当前「${selected.title}」` : ""}
                  </span>
                  <span className="shrink-0">
                    {eventDrawerOpen ? "收起" : "展开"}
                  </span>
                </button>
                {eventDrawerOpen && (
                  <div className="flex gap-2 overflow-x-auto border-t border-line/50 px-2 pb-2 pt-1.5">
                    {eraEvents.map((ev) => (
                      <button
                        key={ev.id}
                        type="button"
                        onClick={() => {
                          setPlaying(false);
                          goToEvent(ev.id);
                        }}
                        className={cn(
                          "shrink-0 rounded-md border px-3 py-2 text-left text-sm transition",
                          ev.id === selected?.id
                            ? "border-accent bg-accent-soft"
                            : "border-line bg-surface/90 hover:border-accent/40",
                        )}
                      >
                        <span className="block text-xs text-muted">
                          {formatYear(ev.year)}
                        </span>
                        <span className="font-medium">{ev.title}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>

        <aside
          className={cn(
            "w-[22rem] shrink-0 overflow-y-auto border-l border-line bg-surface/90 p-5 xl:w-[26rem]",
            "max-[899px]:absolute max-[899px]:inset-y-0 max-[899px]:right-0 max-[899px]:z-20 max-[899px]:w-[min(26rem,100%)] max-[899px]:shadow-lg",
            "max-[899px]:transition-transform",
            drawerRight
              ? "max-[899px]:translate-x-0"
              : "max-[899px]:translate-x-full",
          )}
        >
          {belonging && !focusPlace && (
            <div className="mb-5 rounded-md border border-line bg-page/70 p-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-xs tracking-widest text-muted">历代归属</p>
                  <h2 className="text-lg font-semibold text-era">学术层点查</h2>
                </div>
                <button
                  type="button"
                  className="text-xs text-muted hover:text-accent"
                  onClick={() => setBelonging(null)}
                >
                  关闭
                </button>
              </div>
              <BelongingList result={belonging} year={displayYear} />
              <p className="mt-2 text-[10px] leading-snug text-muted">
                切片局限见 academic/SOURCES.md；无覆盖不等于历史上无建制。
              </p>
            </div>
          )}
          {powerBrowse && territoryMode === "snapshot" && (
            <div className="mb-5 rounded-md border border-line bg-page/70 p-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-xs tracking-widest text-muted">政权事件</p>
                  <h2 className="text-xl font-semibold text-era">
                    {powerBrowse}
                  </h2>
                  <p className="mt-1 text-[11px] text-muted">
                    当前快照窗口内、地点落在该色块内的事件
                  </p>
                </div>
                <button
                  type="button"
                  className="text-xs text-muted hover:text-accent"
                  onClick={() => setPowerBrowse(null)}
                >
                  关闭
                </button>
              </div>
              <p className="mt-3 text-xs tracking-widest text-muted">
                共 {powerEvents.length} 条
              </p>
              <ul className="mt-1 max-h-56 space-y-1 overflow-y-auto">
                {powerEvents.length === 0 && (
                  <li className="px-2 text-xs text-muted">
                    窗口内没有落点在此的事件（或地点在空白/海上）。
                  </li>
                )}
                {powerEvents.map((ev) => (
                  <li key={ev.id}>
                    <button
                      type="button"
                      className={cn(
                        "w-full rounded px-2 py-1.5 text-left text-sm hover:bg-line/40",
                        ev.id === selected?.id && "bg-accent-soft",
                      )}
                      onClick={() => {
                        setPlaying(false);
                        goToEvent(ev.id);
                      }}
                    >
                      <span className="text-xs text-muted">
                        {formatYear(ev.year)}
                        {ev.kind ? ` · ${ev.kind}` : ""}
                      </span>
                      <span className="block font-medium">{ev.title}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {(focusPerson || focusPersonName) && (
            <div className="mb-5 rounded-md border border-line bg-page/70 p-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-xs tracking-widest text-muted">人物</p>
                  <h2 className="text-xl font-semibold text-era">
                    {focusPerson?.name ?? focusPersonName}
                  </h2>
                  {focusPerson?.years && (
                    <p className="text-xs text-muted">{focusPerson.years}</p>
                  )}
                </div>
                <button
                  type="button"
                  className="text-xs text-muted hover:text-accent"
                  onClick={() => {
                    setFocusPersonId(null);
                    setFocusPersonName(null);
                  }}
                >
                  关闭
                </button>
              </div>
              {focusPerson?.blurb && (
                <p className="mt-2 text-sm leading-6">{focusPerson.blurb}</p>
              )}
              {!focusPerson && (
                <p className="mt-2 text-xs text-muted">
                  尚未建档，仅列出事件卡中的同名条目。
                </p>
              )}
              <p className="mt-3 text-xs tracking-widest text-muted">
                参与事件 · {personEvents.length}
              </p>
              <ul className="mt-1 space-y-1">
                {personEvents.map((ev) => (
                  <li key={ev.id}>
                    <button
                      type="button"
                      className="w-full rounded px-2 py-1 text-left text-sm hover:bg-line/40"
                      onClick={() => {
                        setPlaying(false);
                        goToEvent(ev.id);
                      }}
                    >
                      <span className="text-xs text-muted">
                        {formatYear(ev.year)}
                      </span>{" "}
                      {ev.title}
                    </button>
                  </li>
                ))}
              </ul>
              {personRoutes.length > 0 && (
                <>
                  <p className="mt-3 text-xs tracking-widest text-muted">
                    相关路线 · {personRoutes.length}
                  </p>
                  <ul className="mt-1 space-y-2 text-sm">
                    {personRoutes.map((r) => {
                      const travel = estimatePath(
                        r.waypoints.map(
                          (w) => [w.lon, w.lat] as [number, number],
                        ),
                      );
                      return (
                        <li key={r.id} className="px-2 text-muted">
                          <span className="text-ink">{r.name}</span>
                          {travel && (
                            <span className="mt-0.5 block text-[11px]">
                              {travel.summary}
                            </span>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                </>
              )}
            </div>
          )}
          {focusPlace && (
            <div className="mb-5 rounded-md border border-line bg-page/70 p-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-xs tracking-widest text-muted">地点剖面</p>
                  <h2 className="mt-1 text-lg font-semibold text-accent">
                    {
                      formatPlaceLabel(focusPlace, displayYear, nameMode)
                        .primary
                    }
                  </h2>
                  {nameMode === "historic" && (
                    <p className="mt-1 text-sm text-muted">
                      今 {focusPlace.modern}
                    </p>
                  )}
                  {nameMode === "both" &&
                    formatPlaceLabel(focusPlace, displayYear, nameMode)
                      .secondary && (
                      <p className="mt-1 text-sm text-muted">
                        {
                          formatPlaceLabel(focusPlace, displayYear, nameMode)
                            .secondary
                        }
                      </p>
                    )}
                  {nameMode === "modern" && (
                    <p className="mt-1 text-sm text-muted">
                      古 {placeNameAt(focusPlace, displayYear)}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  className="shrink-0 text-xs text-muted hover:text-ink"
                  onClick={() => {
                    setFocusPlaceId(null);
                    setBelonging(null);
                  }}
                >
                  关闭
                </button>
              </div>
              {focusPlace.role && (
                <p className="mt-2 text-sm leading-6">{focusPlace.role}</p>
              )}
              {placeBelonging && (
                <>
                  <p className="mt-3 text-xs tracking-widest text-muted">
                    沿革（学术层）
                  </p>
                  <BelongingList result={placeBelonging} year={displayYear} />
                </>
              )}
              <p className="mt-3 text-xs tracking-widest text-muted">
                相关事件 · {placeRelatedEvents.length}
              </p>
              <ul className="mt-2 max-h-48 space-y-1 overflow-y-auto">
                {placeRelatedEvents.length === 0 && (
                  <li className="text-xs text-muted">尚无挂到此地的事件。</li>
                )}
                {placeRelatedEvents.map((ev) => (
                  <li key={ev.id}>
                    <button
                      type="button"
                      className={cn(
                        "w-full rounded px-2 py-1.5 text-left text-sm hover:bg-line/40",
                        ev.id === selected?.id && "bg-accent-soft",
                      )}
                      onClick={() => {
                        setPlaying(false);
                        goToEvent(ev.id);
                      }}
                    >
                      <span className="text-xs text-muted">
                        {formatYear(ev.year)}
                        {ev.kind ? ` · ${ev.kind}` : ""}
                      </span>
                      <span className="block font-medium">{ev.title}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <AnimatePresence mode="wait">
            {selected ? (
              <motion.div
                key={selected.id + String(displayYear)}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.22 }}
              >
                <p className="text-xs tracking-widest text-muted">事件</p>
                <h2 className="mt-1 text-xl font-semibold text-accent">
                  {selected.title}
                </h2>
                <p className="mt-2 text-sm text-muted">
                  {formatYear(selected.year)}
                  {selected.dynastyTag ? ` · ${selected.dynastyTag}` : ""}
                  {selected.kind ? ` · ${selected.kind}` : ""}
                </p>
                {hostPower && (
                  <p className="mt-1 text-sm text-era">
                    发生在{" "}
                    <button
                      type="button"
                      className="font-medium underline decoration-era/40 underline-offset-2 hover:text-accent"
                      onClick={() => {
                        setPowerBrowse(hostPower);
                        setDrawerRight(true);
                      }}
                    >
                      {hostPower}
                    </button>{" "}
                    境内
                  </p>
                )}
                {selected.lede && (
                  <p className="mt-2 text-[15px] leading-7 text-ink/90">
                    {selected.lede}
                  </p>
                )}
                {geoWhyText && (
                  <div className="mt-3 rounded-md border border-era/25 bg-era/5 p-3">
                    <p className="text-xs tracking-widest text-era">地理因果</p>
                    <p className="mt-2 text-[15px] leading-7">{geoWhyText}</p>
                  </div>
                )}
                {(selectedRouteCosts.length > 0 ||
                  leadsToArcs.labels.some((l) => l.travel)) && (
                  <div className="mt-3 rounded-md border border-line bg-page/70 p-3">
                    <p className="text-xs tracking-widest text-muted">
                      通行估算
                    </p>
                    <ul className="mt-2 space-y-2 text-[13px] leading-6">
                      {selectedRouteCosts.map((row) => (
                        <li key={row.name}>
                          <span className="font-medium">{row.name}</span>
                          <span className="mt-0.5 block text-muted">
                            {row.travel.summary}
                          </span>
                        </li>
                      ))}
                      {leadsToArcs.labels.map((lb) =>
                        lb.travel ? (
                          <li key={`lead-cost-${lb.eventId}`}>
                            <span className="font-medium">
                              影响链 → {lb.title}
                            </span>
                            <span className="mt-0.5 block text-muted">
                              {lb.travel.summary}
                            </span>
                          </li>
                        ) : null,
                      )}
                    </ul>
                    <p className="mt-2 text-[10px] leading-snug text-muted">
                      大圆折线距离；日行程为约数（
                      {TRAVEL_RATE_SOURCES.map((s) => s.title).join("；")}
                      ）。不是精确军制。
                    </p>
                  </div>
                )}
                {panelPlace && (
                  <div className="mt-3 rounded-md border border-line bg-page/70 p-3">
                    <p className="text-xs tracking-widest text-muted">地点</p>
                    <p className="mt-1 text-base font-medium">
                      {
                        formatPlaceLabel(panelPlace, displayYear, nameMode)
                          .primary
                      }
                      {nameMode === "historic" && (
                        <span className="ml-2 text-sm font-normal text-muted">
                          今 {panelPlace.modern}
                        </span>
                      )}
                      {nameMode === "both" &&
                        formatPlaceLabel(panelPlace, displayYear, nameMode)
                          .secondary && (
                          <span className="ml-2 text-sm font-normal text-muted">
                            {
                              formatPlaceLabel(
                                panelPlace,
                                displayYear,
                                nameMode,
                              ).secondary
                            }
                          </span>
                        )}
                    </p>
                    <p className="mt-1 text-xs text-muted">
                      {({
                        capital: "都城",
                        metropolis: "都会",
                        pass: "关隘",
                        prefecture: "府州",
                        other: "地点",
                      } as const)[panelPlace.tier] ?? panelPlace.tier}
                    </p>
                    {panelPlace.role && (
                      <p className="mt-2 text-sm leading-6">{panelPlace.role}</p>
                    )}
                  </div>
                )}
                {selected.people.length > 0 && (
                  <p className="mt-3 flex flex-wrap items-center gap-1 text-sm">
                    <span className="text-muted">人物 </span>
                    {selected.people.map((name, i) => {
                      const pid = selected.personIds?.[i];
                      const archived = pid
                        ? atlas.people.some((p) => p.id === pid)
                        : atlas.people.some((p) => p.name === name);
                      return (
                        <span key={`${name}-${i}`}>
                          {i > 0 && <span className="text-muted">、</span>}
                          {archived ? (
                            <button
                              type="button"
                              className="text-era underline-offset-2 hover:underline"
                              onClick={() => {
                                const person =
                                  (pid &&
                                    atlas.people.find((p) => p.id === pid)) ||
                                  atlas.people.find((p) => p.name === name);
                                setFocusPlaceId(null);
                                setFocusPersonId(person?.id ?? pid ?? null);
                                setFocusPersonName(name);
                              }}
                            >
                              {name}
                            </button>
                          ) : (
                            <span className="text-ink">{name}</span>
                          )}
                        </span>
                      );
                    })}
                  </p>
                )}
                {storyCaption && (
                  <div className="mt-4 rounded-md border border-accent/25 bg-accent-soft/40 p-3">
                    <p className="text-xs tracking-widest text-muted">镜头旁白</p>
                    <p className="mt-2 text-[15px] leading-7">{storyCaption}</p>
                  </div>
                )}
                {highlightWhy && (
                  <div className="mt-3 rounded-md border border-line bg-page/40 p-3">
                    <p className="text-xs tracking-widest text-muted">提亮说明</p>
                    <p className="mt-2 text-sm leading-6 text-muted">
                      {highlightWhy}
                    </p>
                  </div>
                )}
                <details className="mt-4 rounded-md border border-line bg-page/60 p-3">
                  <summary className="cursor-pointer text-xs tracking-widest text-muted">
                    正文与影响（展开）
                  </summary>
                  <p className="mt-3 text-[15px] leading-7">{selected.summary}</p>
                  <p className="mt-3 text-[15px] leading-7">{selected.impact}</p>
                </details>
                {selected.leadsTo.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs tracking-widest text-muted">通往</p>
                    <ul className="mt-2 space-y-1">
                      {selected.leadsTo.map((id) => {
                        const next = eventById(id);
                        if (!next) return null;
                        const lb = leadsToArcs.labels.find(
                          (x) => x.eventId === id,
                        );
                        return (
                          <li key={id}>
                            <button
                              type="button"
                              className="text-left text-sm text-era underline-offset-2 hover:underline"
                              onClick={() => {
                                setPlaying(false);
                                goToEvent(next.id);
                              }}
                            >
                              {formatYear(next.year)} · {next.title}
                              {lb?.travel && (
                                <span className="mt-0.5 block text-[11px] font-normal text-muted no-underline">
                                  {lb.travel.summary}
                                </span>
                              )}
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
                {playing && (
                  <p className="mt-6 text-xs text-muted">
                    自动播放中 ·{" "}
                    {YEAR_RATES.find((s) => s.id === speedId)?.label}
                    {eventHoldLeft > 0
                      ? ` · 事件停留 ${eventHoldLeft}s`
                      : " · 年轴匀速前进"}
                  </p>
                )}
              </motion.div>
            ) : (
              <p className="text-sm text-muted">尚无事件。</p>
            )}
          </AnimatePresence>
        </aside>
      </div>
    </div>
  );
}
