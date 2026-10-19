/**
 * T-010 / T-031：学术政区按需加载（勿 eager 全量），按年份筛面。
 * 字段容错：name / fromYear|beg_yr|beg|from / toYear|end_yr|end|to
 * T-028：点任意一点跨切片 PIP，列历代归属。
 */
import indexJson from "../../../packages/maps/geo/academic/index.json";
import { pointInGeometry } from "@/geo-pip";

export type AcademicSliceMeta = {
  id: string;
  file: string;
  title: string;
  fromYear: number;
  toYear: number;
  lineage: string;
  featureCount: number;
  bytes: number;
};

export type AcademicProps = {
  name: string;
  name_py?: string;
  type_ch?: string;
  fromYear: number;
  toYear: number;
  source: string;
  sliceId: string;
  sliceTitle: string;
  approximate: boolean;
};

type Fc = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties?: Record<string, unknown>;
    geometry: object;
  }>;
};

/** T-031：懒加载；启动时不解析全部学术 JSON */
const loaders = import.meta.glob(
  "../../../packages/maps/geo/academic/*.json",
  { import: "default" },
) as Record<string, () => Promise<Fc>>;

const byFile = new Map<string, Fc>();
const inflight = new Map<string, Promise<Fc | null>>();

function loaderKeyForFile(file: string): string | null {
  for (const path of Object.keys(loaders)) {
    const base = path.replace(/\\/g, "/").split("/").pop();
    if (base === file) return path;
  }
  return null;
}

async function loadSliceFile(file: string): Promise<Fc | null> {
  if (file === "index.json") return null;
  const hit = byFile.get(file);
  if (hit) return hit;
  const pending = inflight.get(file);
  if (pending) return pending;
  const key = loaderKeyForFile(file);
  const loader = key ? loaders[key] : undefined;
  if (!loader) return null;
  const p = loader()
    .then((fc) => {
      if (fc?.type === "FeatureCollection") {
        byFile.set(file, fc);
        return fc;
      }
      return null;
    })
    .finally(() => {
      inflight.delete(file);
    });
  inflight.set(file, p);
  return p;
}

export const academicIndex = indexJson as {
  fetchedAt: string;
  slices: AcademicSliceMeta[];
};

function num(...vals: unknown[]): number | null {
  for (const v of vals) {
    if (typeof v === "number" && Number.isFinite(v)) return v;
    if (typeof v === "string" && v.trim() !== "" && Number.isFinite(Number(v))) {
      return Number(v);
    }
  }
  return null;
}

function featureYears(
  props: Record<string, unknown>,
  slice: AcademicSliceMeta,
): { from: number; to: number } {
  const from =
    num(
      props.fromYear,
      props.beg_yr,
      props.BEG_YR,
      props.beg,
      props.from,
    ) ?? slice.fromYear;
  const to =
    num(props.toYear, props.end_yr, props.END_YR, props.end, props.to) ??
    slice.toYear;
  return { from, to };
}

function collectAtYear(year: number): Fc {
  const y = Math.round(year);
  const features: Fc["features"] = [];
  for (const slice of academicIndex.slices) {
    if (y < slice.fromYear || y > slice.toYear) continue;
    const fc = byFile.get(slice.file);
    if (!fc) continue;
    for (const f of fc.features) {
      const raw = (f.properties ?? {}) as Record<string, unknown>;
      const { from, to } = featureYears(raw, slice);
      if (y < from || y > to) continue;
      const name = String(raw.name ?? raw.NAME_CH ?? raw.NAME ?? "");
      if (!name) continue;
      const approximate = slice.lineage === "hartwell-v5";
      const props: AcademicProps = {
        name,
        name_py: raw.name_py != null ? String(raw.name_py) : undefined,
        type_ch: raw.type_ch != null ? String(raw.type_ch) : undefined,
        fromYear: from,
        toYear: to,
        source: String(raw.source ?? slice.lineage),
        sliceId: slice.id,
        sliceTitle: slice.title,
        approximate,
      };
      features.push({
        type: "Feature",
        properties: props as unknown as Record<string, unknown>,
        geometry: f.geometry,
      });
    }
  }
  return { type: "FeatureCollection", features };
}

/** 仅用已缓存切片（可能为空）；优先走 academicAtYearAsync */
export function academicAtYear(year: number): Fc {
  return collectAtYear(year);
}

/** T-031：只拉当前年命中的切片 */
export async function academicAtYearAsync(year: number): Promise<Fc> {
  const y = Math.round(year);
  const needed = academicIndex.slices.filter(
    (s) => y >= s.fromYear && y <= s.toYear,
  );
  await Promise.all(needed.map((s) => loadSliceFile(s.file)));
  return collectAtYear(y);
}

/** T-028：历代归属一行（命中或该切片无覆盖） */
export type BelongingHit = {
  sliceId: string;
  sliceTitle: string;
  fromYear: number;
  toYear: number;
  name: string;
  type_ch?: string;
  source: string;
  approximate: boolean;
};

export type BelongingRow =
  | { kind: "hit"; hit: BelongingHit }
  | {
      kind: "empty";
      sliceId: string;
      sliceTitle: string;
      fromYear: number;
      toYear: number;
      approximate: boolean;
    };

export type BelongingResult = {
  lon: number;
  lat: number;
  rows: BelongingRow[];
};

function belongingFromCache(lon: number, lat: number): BelongingResult {
  const rows: BelongingRow[] = [];
  for (const slice of academicIndex.slices) {
    const approximate = slice.lineage === "hartwell-v5";
    const fc = byFile.get(slice.file);
    let hit: BelongingHit | null = null;
    if (fc) {
      for (const f of fc.features) {
        const geom = f.geometry as {
          type?: string;
          coordinates?: unknown;
        };
        if (!pointInGeometry(lon, lat, geom)) continue;
        const raw = (f.properties ?? {}) as Record<string, unknown>;
        const { from, to } = featureYears(raw, slice);
        const name = String(raw.name ?? raw.NAME_CH ?? raw.NAME ?? "");
        if (!name) continue;
        hit = {
          sliceId: slice.id,
          sliceTitle: slice.title,
          fromYear: from,
          toYear: to,
          name,
          type_ch: raw.type_ch != null ? String(raw.type_ch) : undefined,
          source: String(raw.source ?? slice.lineage),
          approximate,
        };
        break;
      }
    }
    if (hit) {
      rows.push({ kind: "hit", hit });
    } else {
      rows.push({
        kind: "empty",
        sliceId: slice.id,
        sliceTitle: slice.title,
        fromYear: slice.fromYear,
        toYear: slice.toYear,
        approximate,
      });
    }
  }
  rows.sort((a, b) => {
    const ay = a.kind === "hit" ? a.hit.fromYear : a.fromYear;
    const by = b.kind === "hit" ? b.hit.fromYear : b.fromYear;
    return ay - by;
  });
  return { lon, lat, rows };
}

/** 同步：仅已加载切片；未加载的切片会显示 empty */
export function academicBelongingAt(lon: number, lat: number): BelongingResult {
  return belongingFromCache(lon, lat);
}

/** T-028 / T-031：先拉齐全部切片再 PIP */
export async function academicBelongingAtAsync(
  lon: number,
  lat: number,
): Promise<BelongingResult> {
  await Promise.all(
    academicIndex.slices.map((s) => loadSliceFile(s.file)),
  );
  return belongingFromCache(lon, lat);
}

/** 当前年对应的切片行是否应加粗 */
export function belongingRowActiveAt(
  row: BelongingRow,
  year: number,
): boolean {
  const y = Math.round(year);
  if (row.kind === "hit") {
    return y >= row.hit.fromYear && y <= row.hit.toYear;
  }
  return y >= row.fromYear && y <= row.toYear;
}
