/** 射线法点在多边形内（含 MultiPolygon）；洞环未处理，示意疆域够用。 */

function pointInRing(lon: number, lat: number, ring: number[][]): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i]![0]!;
    const yi = ring[i]![1]!;
    const xj = ring[j]![0]!;
    const yj = ring[j]![1]!;
    const denom = yj - yi;
    const intersect =
      yi > lat !== yj > lat &&
      lon < ((xj - xi) * (lat - yi)) / (denom === 0 ? 1e-12 : denom) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

export function pointInGeometry(
  lon: number,
  lat: number,
  geometry: { type?: string; coordinates?: unknown } | null | undefined,
): boolean {
  if (!geometry?.type || !geometry.coordinates) return false;
  if (geometry.type === "Polygon") {
    const rings = geometry.coordinates as number[][][];
    const outer = rings[0];
    if (!outer?.length) return false;
    if (!pointInRing(lon, lat, outer)) return false;
    for (let h = 1; h < rings.length; h++) {
      const hole = rings[h];
      if (hole?.length && pointInRing(lon, lat, hole)) return false;
    }
    return true;
  }
  if (geometry.type === "MultiPolygon") {
    const polys = geometry.coordinates as number[][][][];
    for (const poly of polys) {
      const outer = poly?.[0];
      if (!outer?.length) continue;
      if (!pointInRing(lon, lat, outer)) continue;
      let inHole = false;
      for (let h = 1; h < (poly?.length ?? 0); h++) {
        const hole = poly![h];
        if (hole?.length && pointInRing(lon, lat, hole)) {
          inHole = true;
          break;
        }
      }
      if (!inHole) return true;
    }
  }
  return false;
}

export function powerAtPoint(
  lon: number,
  lat: number,
  features: Array<{
    geometry?: { type?: string; coordinates?: unknown } | null;
    properties?: { power?: string; kind?: string } | null;
  }>,
): string | null {
  for (const f of features) {
    const p = f.properties;
    if (!p?.power) continue;
    if (pointInGeometry(lon, lat, f.geometry)) return p.power;
  }
  return null;
}
