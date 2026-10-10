// earth.json 的类型镜像：字段含义以数据文件内的 note 为准，这里只描述形状。
// 数据是唯一真源（ADR 0128 决策 6）：渲染、剖面着色、探针读数与图表全部由它生成。

export interface EarthData {
  meta: {
    title: string;
    scale: "real";
    note: string;
    lengthUnit: "km";
    sceneUnitEarthRadii: 1;
    sceneUnitLengthKm: number;
    disclaimers: string[];
  };
  shape: {
    model: string;
    equatorialRadiusKm: number;
    polarRadiusKm: number;
    inverseFlattening: number;
    meanRadiusKm: number;
    sourceIds: string[];
    note: string;
  };
  surface: {
    textureFile: string;
    sourceIds: string[];
    features: SurfaceFeature[];
  };
  interior: {
    layers: InteriorLayer[];
    boundaries: Boundary[];
    keyPoints: InteriorKeyPoint[];
    premSegments: PremSegment[];
    premNote: string;
    tempProfile: TempPoint[];
    tempNote: string;
    sourceIds: string[];
  };
  atmosphere: {
    layers: AtmosphereLayer[];
    karmanLineKm: number;
    karmanNote: string;
    scaleHeightKm: number;
    scaleHeightNote: string;
    composition: GasEntry[];
    compositionNote: string;
    ussa1976: Ussa1976;
    keyPoints: AtmosphereKeyPoint[];
    sourceIds: string[];
  };
  sources: Record<string, { title: string; url: string }>;
}

export interface SurfaceFeature {
  name: string;
  heightKm: number;
  note: string;
}

export interface InteriorLayer {
  id: string;
  name: string;
  english: string;
  topDepthKm: number;
  bottomDepthKm: number;
  /** 只有地壳需要：大陆 / 大洋两套典型厚度 */
  bottomDepthKmContinental?: number;
  bottomDepthKmOceanic?: number;
  bottomDepthRangeKm?: [number, number];
  colorHint: string;
  description: string;
  sourceIds: string[];
}

export interface Boundary {
  id: string;
  name: string;
  depthKm: number;
  note: string;
}

export interface InteriorKeyPoint {
  name: string;
  depthKm: number;
  note: string;
}

export interface PremSegment {
  topDepthKm: number;
  bottomDepthKm: number;
  topDensity: number;
  bottomDensity: number;
  note: string;
}

export interface TempPoint {
  depthKm: number;
  tempC: number;
  rangeC: [number, number] | null;
  note: string;
}

export interface AtmosphereLayer {
  id: string;
  name: string;
  english: string;
  bottomHeightKm: number;
  /** null = 没有明确上界（外逸层），渲染为渐隐 */
  topHeightKm: number | null;
  topHeightNote?: string;
  colorHint: string;
  description: string;
  sourceIds: string[];
}

export interface GasEntry {
  gas: string;
  volumePercent: number;
  note?: string;
}

export interface Ussa1976 {
  tempPointsC: { heightKm: number; tempC: number }[];
  pressurePointsHPa: { heightKm: number; pressureHPa: number }[];
  note: string;
  sourceIds: string[];
}

export interface AtmosphereKeyPoint {
  name: string;
  heightKm: number;
  note: string;
}
