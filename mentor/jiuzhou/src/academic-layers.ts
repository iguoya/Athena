/**
 * T-010：构建期打包 packages/maps/geo/academic/，按年份筛政区面。
 * 字段容错：name / fromYear|beg_yr|beg|from / toYear|end_yr|end|to
 */
import indexJson from "../../../packages/maps/geo/academic/index.json";

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

const modules = import.meta.glob(
  "../../../packages/maps/geo/academic/*.json",
  { eager: true, import: "default" },
) as Record<string, Fc>;

const byFile = new Map<string, Fc>();
for (const [path, fc] of Object.entries(modules)) {
  const file = path.replace(/\\/g, "/").split("/").pop();
  if (!file || file === "index.json") continue;
  if (fc?.type !== "FeatureCollection") continue;
  byFile.set(file, fc);
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

/** 当前年命中的学术政区（切片级 + 要素级起止年） */
export function academicAtYear(year: number): Fc {
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
