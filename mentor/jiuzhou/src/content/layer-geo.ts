/** 把 features / routes 转成 MapLibre FeatureCollection。 */

import {
  type GeoFeature,
  type MarchRoute,
  featuresAtYear,
  routeLineAtYear,
  routesVisibleAt,
} from "./types";

type LineFc = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: Record<string, string | number>;
    geometry: { type: "LineString"; coordinates: [number, number][] };
  }>;
};

export function featuresCollection(
  features: GeoFeature[],
  year: number,
  litIds?: Set<string>,
): LineFc {
  const alive = featuresAtYear(features, year, litIds);
  return {
    type: "FeatureCollection",
    features: alive.map((f) => ({
      type: "Feature",
      properties: {
        id: f.id,
        group: f.group,
        name: f.name,
        lit: litIds?.has(f.id) ? 1 : 0,
      },
      geometry: f.geometry,
    })),
  };
}

export function routesCollection(
  routes: MarchRoute[],
  year: number,
  opts?: {
    eventId?: string | null;
    showIds?: Set<string>;
    litIds?: Set<string>;
  },
): LineFc {
  const visible = routesVisibleAt(routes, year, {
    eventId: opts?.eventId,
    showIds: opts?.showIds,
  });
  const features: LineFc["features"] = [];
  for (const r of visible) {
    const coords = routeLineAtYear(r, year);
    if (!coords) continue;
    features.push({
      type: "Feature",
      properties: {
        id: r.id,
        kind: r.kind,
        name: r.name,
        lit: opts?.litIds?.has(r.id) ? 1 : 0,
      },
      geometry: { type: "LineString", coordinates: coords },
    });
  }
  return { type: "FeatureCollection", features };
}
