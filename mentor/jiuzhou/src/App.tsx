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
import { featuresCollection, routesCollection } from "@/content/layer-geo";
import { CompareMaps } from "@/CompareMaps";
import {
  academicAtYear,
  type AcademicProps,
} from "@/academic-layers";
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

const CHINA_VIEW = { longitude: 105.5, latitude: 35.5, zoom: 3.45 };

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
  /** T-019：暗角与纸纹，默认开 */
  const [paperAmbience, setPaperAmbience] = useState(true);
  /** 势力名标签随缩放淡出 */
  const [mapZoom, setMapZoom] = useState(CHINA_VIEW.zoom);
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
      return {
        type: "Feature" as const,
        properties: {
          id: place.id,
          name: label.primary,
          modern: place.modern,
          secondary: label.secondary ?? "",
          tier: place.tier,
          sortKey,
          mustShow,
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

  /** T-003：DOM 标签 + 屏幕包围盒碰撞（离线，不依赖 glyphs） */
  const [placeLabelIds, setPlaceLabelIds] = useState<string[]>([]);
  useEffect(() => {
    const map = mapRef.current?.getMap();
    if (!map) return;
    function recompute() {
      const m = mapRef.current?.getMap();
      if (!m) return;
      const feats = [...placesGeo.features].sort(
        (a, b) =>
          Number(a.properties?.sortKey ?? 9) -
          Number(b.properties?.sortKey ?? 9),
      );
      const zoom = m.getZoom();
      const taken: Array<{ x0: number; y0: number; x1: number; y1: number }> =
        [];
      const ids: string[] = [];
      for (const f of feats) {
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
          continue;
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
        const hit = taken.some(
          (t) =>
            !(
              box.x1 < t.x0 ||
              box.x0 > t.x1 ||
              box.y1 < t.y0 ||
              box.y0 > t.y1
            ),
        );
        if (hit) continue;
        taken.push(box);
        ids.push(props.id);
        if (ids.length >= 48) break;
      }
      setPlaceLabelIds(ids);
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
  }, [placesGeo]);

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

  /** T-019：注入 POWER_COLORS，供 fill 表达式读取 */
  const territoryPaintData = useMemo(() => {
    if (!territoryData) return null;
    return {
      type: "FeatureCollection" as const,
      features: territoryData.features.map((f) => {
        const p = (f.properties ?? {}) as TerrProps;
        const color = powerColor(p.power, p.color ?? MAP_TOKENS.territory);
        return {
          ...f,
          properties: {
            ...p,
            color,
            edge: powerEdgeColor(color),
          },
        };
      }),
    };
  }, [territoryData]);

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

  /** T-008：选中事件的 leadsTo → 弧线 + 中点年份标签 */
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
      features.push({
        type: "Feature",
        properties: {
          eventId: next.id,
          year: next.year,
          title: next.title,
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
      });
    }
    return {
      lines: features.length
        ? { type: "FeatureCollection" as const, features }
        : null,
      labels,
    };
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
      rendered: (layerId: string) => number;
      year: () => number;
      setYear: (y: number) => void;
      snapshotsShown: () => { group: string; powers: string[] } | null;
      schematicShown: () => boolean;
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
        const near = nearestEventAtOrBefore(timelineAll, y);
        if (near) {
          const i = timelineAll.findIndex((e) => e.id === near.id);
          if (i >= 0) setIndex(i);
        }
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
    };
    (window as unknown as { __jzDebug?: JzDebug }).__jzDebug = api;
    return () => {
      delete (window as unknown as { __jzDebug?: JzDebug }).__jzDebug;
    };
  }, [timelineAll]);

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

  /** T-027：有快照则 fitBounds 整片疆域；无快照才跟事件地点 */
  useEffect(() => {
    if (activeStoryStep) return;
    const map = mapRef.current;
    if (!map) return;
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
        return;
      }
    }
    if (!selected) return;
    const place = placeById(selected.placeId);
    if (!place) return;
    map.flyTo({
      center: [place.lon, place.lat],
      zoom: Math.max(map.getZoom(), 4.0),
      duration: 700,
    });
  }, [
    selected?.id,
    axis,
    activeStoryStep,
    territoryMode,
    territoryData,
    displayYear,
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
                setYear(v);
                const near = nearestEventAtOrBefore(
                  timelineAll.filter((ev) => kindOn.has(eventKindOf(ev))),
                  v,
                );
                if (near) {
                  const i = timeline.findIndex((x) => x.id === near.id);
                  if (i >= 0) setIndex(i);
                }
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
            <label className="mb-3 flex cursor-pointer items-center gap-2 px-2 text-xs">
              <input
                type="checkbox"
                checked={paperAmbience}
                onChange={(e) => setPaperAmbience(e.target.checked)}
                className="accent-[var(--accent)]"
              />
              纸本质感
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
              "places-circle",
              "leads-arc-line",
              "academic-fill",
            ]}
            cursor="pointer"
            onLoad={() => {
              const m = mapRef.current?.getMap();
              m?.resize();
              if (m) setMapZoom(m.getZoom());
            }}
            onMove={(e) => setMapZoom(e.viewState.zoom)}
            onClick={(e) => {
              const arc = e.features?.find(
                (x) => x.layer?.id === "leads-arc-line",
              );
              const nextId = arc?.properties?.eventId as string | undefined;
              if (nextId) {
                setPlaying(false);
                setAcademicPick(null);
                goToEvent(nextId);
                return;
              }
              const placeHit = e.features?.find(
                (x) => x.layer?.id === "places-circle",
              );
              if (placeHit) {
                const id = placeHit.properties?.id as string | undefined;
                if (!id) return;
                setAcademicPick(null);
                const place = placeById(id);
                if (place) flyPlace(place);
                return;
              }
              const acad = e.features?.find(
                (x) => x.layer?.id === "academic-fill",
              );
              if (acad?.properties) {
                const p = acad.properties as AcademicProps;
                setAcademicPick({
                  name: String(p.name ?? ""),
                  name_py: p.name_py ? String(p.name_py) : undefined,
                  type_ch: p.type_ch ? String(p.type_ch) : undefined,
                  fromYear: Number(p.fromYear),
                  toYear: Number(p.toYear),
                  source: String(p.source ?? ""),
                  sliceId: String(p.sliceId ?? ""),
                  sliceTitle: String(p.sliceTitle ?? ""),
                  approximate:
                    Boolean(p.approximate) ||
                    String(p.source) === "hartwell-v5",
                });
                return;
              }
              setAcademicPick(null);
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
                    /** 半透明叠在地形上，近似 multiply 透底 */
                    "fill-opacity": 0.5,
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
                    "line-width": 1.7,
                    "line-opacity": 0.9,
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
                      0.14,
                      0.2,
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
                    "line-opacity": 0.72,
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
                  title={lb.title}
                >
                  → {formatYear(lb.year)}
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
            <Source id="places" type="geojson" data={placesGeo}>
              <Layer
                id="places-circle"
                type="circle"
                paint={{
                  "circle-radius": [
                    "match",
                    ["get", "tier"],
                    "capital",
                    6,
                    "metropolis",
                    5,
                    "pass",
                    4,
                    3,
                  ],
                  "circle-color": [
                    "case",
                    ["==", ["get", "active"], 1],
                    MAP_TOKENS.highlight,
                    [
                      "match",
                      ["get", "tier"],
                      "capital",
                      MAP_TOKENS.era,
                      "metropolis",
                      MAP_TOKENS.highlight,
                      "#8a7355",
                    ],
                  ],
                  "circle-stroke-width": 1.2,
                  "circle-stroke-color": "#fff8ef",
                }}
              />
            </Source>
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
          {academicPick && (
            <div className="absolute bottom-28 left-4 z-10 max-w-xs rounded-md border border-line bg-surface/95 px-3 py-2 shadow-md">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-ink">
                    {academicPick.name}
                    {academicPick.type_ch ? (
                      <span className="ml-1 text-xs font-normal text-muted">
                        {academicPick.type_ch}
                      </span>
                    ) : null}
                  </p>
                  {academicPick.name_py ? (
                    <p className="text-xs text-muted">{academicPick.name_py}</p>
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
                </div>
                <button
                  type="button"
                  className="text-xs text-muted hover:text-ink"
                  onClick={() => setAcademicPick(null)}
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
                  <ul className="mt-1 space-y-1 text-sm">
                    {personRoutes.map((r) => (
                      <li key={r.id} className="px-2 text-muted">
                        {r.name}
                      </li>
                    ))}
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
                  onClick={() => setFocusPlaceId(null)}
                >
                  关闭
                </button>
              </div>
              {focusPlace.role && (
                <p className="mt-2 text-sm leading-6">{focusPlace.role}</p>
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
                        return (
                          <li key={id}>
                            <button
                              type="button"
                              className="text-sm text-era underline-offset-2 hover:underline"
                              onClick={() => {
                                setPlaying(false);
                                goToEvent(next.id);
                              }}
                            >
                              {formatYear(next.year)} · {next.title}
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
