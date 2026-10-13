import { useMemo, useRef, useState } from "react";
import MapGl, { Layer, Marker, NavigationControl, Source } from "react-map-gl/maplibre";
import { PAPER_STYLE, MAP_TOKENS } from "@athena/maps/index.ts";
import landJson from "../../../packages/maps/geo/land.json";
import countriesJson from "../../../packages/maps/geo/countries.json";
import { featuresCollection } from "@/content/layer-geo";
import {
  type Capital,
  type GeoFeature,
  type Place,
  capitalAliveAt,
  formatYear,
} from "@/content/types";

type Fc = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties?: Record<string, unknown>;
    geometry: object;
  }>;
};

const landFc = landJson as Fc;
const countriesFc = countriesJson as Fc;

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

function pickTerritory(
  territories: Fc,
  year: number,
  eraTerritoryId?: string,
): Fc | null {
  const inYear = territories.features.filter((f) => {
    const p = (f.properties ?? {}) as TerrProps;
    const from = typeof p.fromYear === "number" ? p.fromYear : -9999;
    const to = typeof p.toYear === "number" ? p.toYear : 9999;
    return year >= from && year <= to;
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
    return { type: "FeatureCollection", features: best };
  }
  const schematics = inYear.filter(
    (f) => (f.properties as TerrProps).kind !== "snapshot",
  );
  if (schematics.length) {
    return { type: "FeatureCollection", features: schematics };
  }
  if (!eraTerritoryId) return null;
  const fallback = territories.features.filter(
    (f) => (f.properties as TerrProps).id === eraTerritoryId,
  );
  return fallback.length
    ? { type: "FeatureCollection", features: fallback }
    : null;
}

function YearPane({
  year,
  coastline,
  territories,
  geoFeatures,
  capitals,
  places,
  eraTerritoryId,
}: {
  year: number;
  coastline: Fc;
  territories: Fc;
  geoFeatures: GeoFeature[];
  capitals: Capital[];
  places: Place[];
  eraTerritoryId?: string;
}) {
  const terr = useMemo(
    () => pickTerritory(territories, year, eraTerritoryId),
    [territories, year, eraTerritoryId],
  );
  const feats = useMemo(
    () => featuresCollection(geoFeatures, year, new Set()),
    [geoFeatures, year],
  );
  const mains = useMemo(() => {
    const out: Array<{ cap: Capital; place: Place }> = [];
    for (const cap of capitals) {
      if (cap.role !== "main" || !capitalAliveAt(cap, year)) continue;
      const place = places.find((p) => p.id === cap.placeId);
      if (place) out.push({ cap, place });
    }
    return out;
  }, [capitals, places, year]);

  return (
    <MapGl
      initialViewState={{ longitude: 105.5, latitude: 35.5, zoom: 3.45 }}
      mapStyle={PAPER_STYLE}
      style={{ width: "100%", height: "100%" }}
      attributionControl={false}
      interactive={false}
    >
      <NavigationControl position="top-right" showCompass={false} />
      <Source id="land" type="geojson" data={landFc}>
        <Layer
          id="land-fill"
          type="fill"
          paint={{ "fill-color": MAP_TOKENS.landFill, "fill-opacity": 1 }}
        />
      </Source>
      <Source id="countries" type="geojson" data={countriesFc}>
        <Layer
          id="neighbor-fill"
          type="fill"
          filter={["==", ["get", "role"], "neighbor"]}
          paint={{
            "fill-color": MAP_TOKENS.neighborLand,
            "fill-opacity": 0.95,
          }}
        />
      </Source>
      <Source id="coast" type="geojson" data={coastline}>
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
      <Source id="feats" type="geojson" data={feats}>
        <Layer
          id="feats-line"
          type="line"
          paint={{
            "line-color": "#57534e",
            "line-width": 1.8,
            "line-opacity": 0.7,
          }}
        />
      </Source>
      {terr && (
        <Source id="terr" type="geojson" data={terr}>
          <Layer
            id="terr-fill"
            type="fill"
            paint={{
              "fill-color": [
                "coalesce",
                ["get", "color"],
                MAP_TOKENS.territory,
              ],
              "fill-opacity": 0.3,
            }}
          />
          <Layer
            id="terr-line"
            type="line"
            paint={{
              "line-color": [
                "coalesce",
                ["get", "color"],
                MAP_TOKENS.territory,
              ],
              "line-width": 1.6,
              "line-opacity": 0.75,
            }}
          />
        </Source>
      )}
      {mains.map(({ cap, place }) => (
        <Marker
          key={cap.id}
          longitude={place.lon}
          latitude={place.lat}
          anchor="bottom"
        >
          <div className="flex flex-col items-center gap-0.5">
            <span className="rounded bg-era px-1.5 py-0.5 text-[9px] font-semibold text-white shadow-sm">
              {cap.state}·{cap.name}
            </span>
            <div className="capital-star" />
          </div>
        </Marker>
      ))}
    </MapGl>
  );
}

export function CompareMaps({
  leftYear,
  rightYear,
  onLeftYear,
  onRightYear,
  coastline,
  territories,
  geoFeatures,
  capitals,
  places,
  leftEraTerritoryId,
  rightEraTerritoryId,
  onClose,
}: {
  leftYear: number;
  rightYear: number;
  onLeftYear: (y: number) => void;
  onRightYear: (y: number) => void;
  coastline: Fc;
  territories: Fc;
  geoFeatures: GeoFeature[];
  capitals: Capital[];
  places: Place[];
  leftEraTerritoryId?: string;
  rightEraTerritoryId?: string;
  onClose: () => void;
}) {
  const boxRef = useRef<HTMLDivElement>(null);
  const [split, setSplit] = useState(50);

  function onDrag(clientX: number) {
    const box = boxRef.current;
    if (!box) return;
    const rect = box.getBoundingClientRect();
    const pct = ((clientX - rect.left) / rect.width) * 100;
    setSplit(Math.min(85, Math.max(15, pct)));
  }

  return (
    <div className="absolute inset-0 z-20 flex flex-col bg-page">
      <div className="flex flex-wrap items-center gap-2 border-b border-line bg-surface/95 px-4 py-2 text-sm">
        <span className="font-medium text-era">卷帘对比</span>
        <label className="flex items-center gap-1 text-xs text-muted">
          左
          <input
            type="number"
            value={leftYear}
            onChange={(e) => onLeftYear(Number(e.target.value))}
            className="w-20 rounded border border-line bg-page px-1 py-0.5 text-ink"
          />
          <span>{formatYear(leftYear)}</span>
        </label>
        <label className="flex items-center gap-1 text-xs text-muted">
          右
          <input
            type="number"
            value={rightYear}
            onChange={(e) => onRightYear(Number(e.target.value))}
            className="w-20 rounded border border-line bg-page px-1 py-0.5 text-ink"
          />
          <span>{formatYear(rightYear)}</span>
        </label>
        <button
          type="button"
          className="ml-auto rounded border border-line px-2 py-0.5 text-xs"
          onClick={onClose}
        >
          退出对比
        </button>
      </div>
      <div
        ref={boxRef}
        className="relative min-h-0 flex-1"
        onMouseMove={(e) => {
          if (e.buttons === 1 && (e.target as HTMLElement).dataset?.split)
            onDrag(e.clientX);
        }}
      >
        <div
          className="absolute inset-0"
          style={{ clipPath: `inset(0 ${100 - split}% 0 0)` }}
        >
          <YearPane
            year={leftYear}
            coastline={coastline}
            territories={territories}
            geoFeatures={geoFeatures}
            capitals={capitals}
            places={places}
            eraTerritoryId={leftEraTerritoryId}
          />
          <span className="pointer-events-none absolute left-3 top-3 rounded bg-surface/90 px-2 py-1 text-xs font-medium shadow">
            {formatYear(leftYear)}
          </span>
        </div>
        <div
          className="absolute inset-0"
          style={{ clipPath: `inset(0 0 0 ${split}%)` }}
        >
          <YearPane
            year={rightYear}
            coastline={coastline}
            territories={territories}
            geoFeatures={geoFeatures}
            capitals={capitals}
            places={places}
            eraTerritoryId={rightEraTerritoryId}
          />
          <span className="pointer-events-none absolute right-3 top-3 rounded bg-surface/90 px-2 py-1 text-xs font-medium shadow">
            {formatYear(rightYear)}
          </span>
        </div>
        <div
          data-split
          className="absolute top-0 z-10 h-full w-3 -translate-x-1/2 cursor-ew-resize"
          style={{ left: `${split}%` }}
          onMouseDown={(e) => {
            e.preventDefault();
            const move = (ev: MouseEvent) => onDrag(ev.clientX);
            const up = () => {
              window.removeEventListener("mousemove", move);
              window.removeEventListener("mouseup", up);
            };
            window.addEventListener("mousemove", move);
            window.addEventListener("mouseup", up);
          }}
        >
          <div className="mx-auto h-full w-0.5 bg-accent" />
        </div>
      </div>
    </div>
  );
}
