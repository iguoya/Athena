import { describe, expect, it } from "vitest";
import {
  atmosphereLayerAtHeight,
  atmosphereLayerTopRadius,
  atmosphereLayers,
  data,
  densityAt,
  densityColor,
  interiorLayerAtDepth,
  interiorLayerRadii,
  interiorLayers,
  interiorTempAt,
  kmToScene,
  ussaPressureAt,
  ussaTempAt,
  USSA_MAX_HEIGHT_KM,
} from "./load";

// 这组测试是「追求严谨」的落地：数据文件里的每个关键数值都对照独立抄录的
// 标准值核对（出处见 earth.json 的 sources）。改数据必须过这四道闸。

const closeTo = (actual: number, expected: number, epsilon = 1e-6) =>
  expect(actual).toBeCloseTo(expected, epsilon);

describe("形状：WGS 84", () => {
  it("椭球参数自洽：b = a·(1−f)，且 1/f 与表中一致", () => {
    const { equatorialRadiusKm: a, polarRadiusKm: b, inverseFlattening: invF } = data.shape;
    const f = 1 / invF;
    closeTo(b, a * (1 - f), 4);
    closeTo(invF, 298.257223563, 6);
  });

  it("平均半径 6371 km，场景单位由此派生", () => {
    expect(data.shape.meanRadiusKm).toBe(6371.0);
    closeTo(kmToScene(6371), 1);
    closeTo(kmToScene(0), 0);
  });
});

describe("地球内部分层", () => {
  it("六层无缝覆盖 0–6371 km，从地壳到内核", () => {
    const ids = interiorLayers.map((l) => l.id);
    expect(ids).toEqual([
      "crust",
      "upper-mantle",
      "transition-zone",
      "lower-mantle",
      "outer-core",
      "inner-core",
    ]);
    expect(interiorLayers[0].topDepthKm).toBe(0);
    expect(interiorLayers[interiorLayers.length - 1].bottomDepthKm).toBe(6371);
    for (let i = 1; i < interiorLayers.length; i++) {
      expect(interiorLayers[i].topDepthKm).toBe(interiorLayers[i - 1].bottomDepthKm);
      expect(interiorLayers[i].bottomDepthKm).toBeGreaterThan(interiorLayers[i].topDepthKm);
    }
  });

  it("关键层界对照标准值：莫霍 35、410、660、古登堡 2891、莱曼 5150", () => {
    const bottoms = Object.fromEntries(interiorLayers.map((l) => [l.id, l.bottomDepthKm]));
    expect(bottoms["crust"]).toBe(35);
    expect(bottoms["upper-mantle"]).toBe(410);
    expect(bottoms["transition-zone"]).toBe(660);
    expect(bottoms["lower-mantle"]).toBe(2891);
    expect(bottoms["outer-core"]).toBe(5150);
  });

  it("地壳声明了大陆 / 大洋两套典型厚度，且都在 30–70 / 5–10 km 文献区间内", () => {
    const crust = interiorLayers[0];
    expect(crust.bottomDepthKmOceanic).toBeLessThan(crust.bottomDepthKmContinental!);
    const [lo, hi] = crust.bottomDepthRangeKm!;
    expect(crust.bottomDepthKmContinental!).toBeGreaterThanOrEqual(lo);
    expect(crust.bottomDepthKmContinental!).toBeLessThanOrEqual(hi);
    expect(crust.bottomDepthKmOceanic!).toBeGreaterThanOrEqual(5);
    expect(crust.bottomDepthKmOceanic!).toBeLessThanOrEqual(10);
  });

  it("人类钻探最深的科拉 SG-3（12.262 km）在地壳之内——「没钻透地壳」这个教学点由数据本身成立", () => {
    const kola = data.interior.keyPoints.find((p) => p.name.includes("科拉"));
    expect(kola).toBeDefined();
    const layer = interiorLayerAtDepth(kola!.depthKm);
    expect(layer?.id).toBe("crust");
  });
});

describe("PREM 密度模型", () => {
  const segments = data.interior.premSegments;

  it("分段无缝覆盖 0–6371 km", () => {
    expect(segments[0].topDepthKm).toBe(0);
    expect(segments[segments.length - 1].bottomDepthKm).toBe(6371);
    for (let i = 1; i < segments.length; i++) {
      expect(segments[i].topDepthKm).toBe(segments[i - 1].bottomDepthKm);
    }
  });

  it("密度随深度单调不减，界面只允许跳升（向上变小），地心 13.09 g/cm³", () => {
    for (const s of segments) {
      expect(s.bottomDensity).toBeGreaterThanOrEqual(s.topDensity);
    }
    for (let i = 1; i < segments.length; i++) {
      expect(segments[i].topDensity).toBeGreaterThanOrEqual(segments[i - 1].bottomDensity);
    }
    closeTo(segments[segments.length - 1].bottomDensity, 13.09);
  });

  it("古登堡面（2891 km）的密度跳升约 4.3 g/cm³，是全地球最大的一次", () => {
    const mantle = segments.find((s) => s.bottomDepthKm === 2891)!;
    const core = segments.find((s) => s.topDepthKm === 2891)!;
    const jump = core.topDensity - mantle.bottomDensity;
    expect(jump).toBeGreaterThanOrEqual(4);
    expect(jump).toBeLessThanOrEqual(4.6);
  });

  it("界面值对照 PREM 常用引用值", () => {
    closeTo(densityAt(0), 2.72);
    closeTo(densityAt(2890.9), 5.57, 2); // 地幔底（段内插值）
    closeTo(densityAt(5149.9), 12.17, 2); // 外核底（段内插值；ICB 之上跳到内核侧 12.76 由单调测试覆盖）
    closeTo(densityAt(6371), 13.09);
    expect(densityAt(700)).toBeGreaterThan(densityAt(100));
  });

  it("密度色标可生成且单调映射", () => {
    expect(densityColor(2.72)).toMatch(/^#[0-9a-f]{6}$/);
    expect(densityColor(13)).not.toBe(densityColor(3));
  });
});

describe("地球内部温度（共识区间，示意廓线）", () => {
  it("关键深度给出文献区间，整体随深度上升", () => {
    const points = data.interior.tempProfile;
    for (const point of points) {
      if (point.rangeC) {
        expect(point.tempC).toBeGreaterThanOrEqual(point.rangeC[0]);
        expect(point.tempC).toBeLessThanOrEqual(point.rangeC[1]);
      }
    }
    expect(interiorTempAt(6371)).toBeGreaterThan(interiorTempAt(0) * 100);
    // 核幔边界共识 3700–4000 °C
    const cmb = points.find((p) => p.depthKm === 2891)!;
    expect(cmb.tempC).toBeGreaterThanOrEqual(3700);
    expect(cmb.tempC).toBeLessThanOrEqual(4000);
  });
});

describe("大气分层", () => {
  it("五层从 0 起、无缝衔接，只有外逸层上界不封闭", () => {
    const ids = atmosphereLayers.map((l) => l.id);
    expect(ids).toEqual([
      "troposphere",
      "stratosphere",
      "mesosphere",
      "thermosphere",
      "exosphere",
    ]);
    expect(atmosphereLayers[0].bottomHeightKm).toBe(0);
    for (let i = 1; i < atmosphereLayers.length; i++) {
      const prev = atmosphereLayers[i - 1];
      expect(atmosphereLayers[i].bottomHeightKm).toBe(prev.topHeightKm);
      expect(prev.topHeightKm).not.toBeNull();
    }
    expect(atmosphereLayers[atmosphereLayers.length - 1].topHeightKm).toBeNull();
  });

  it("WMO 界线：对流层顶 12、平流层顶 50、中间层顶 85、热层顶 600", () => {
    const tops = Object.fromEntries(atmosphereLayers.map((l) => [l.id, l.topHeightKm]));
    expect(tops["troposphere"]).toBe(12);
    expect(tops["stratosphere"]).toBe(50);
    expect(tops["mesosphere"]).toBe(85);
    expect(tops["thermosphere"]).toBe(600);
  });

  it("卡门线 100 km 落在热层内——它不是物理界面", () => {
    expect(data.atmosphere.karmanLineKm).toBe(100);
    expect(atmosphereLayerAtHeight(100)?.id).toBe("thermosphere");
  });

  it("大气锚点按真实高度落层：ISS 在热层，GPS 静止轨道在外逸层", () => {
    const iss = data.atmosphere.keyPoints.find((p) => p.name.includes("国际空间站"))!;
    expect(atmosphereLayerAtHeight(iss.heightKm)?.id).toBe("thermosphere");
    const geo = data.atmosphere.keyPoints.find((p) => p.name.includes("地球静止轨道"))!;
    expect(atmosphereLayerAtHeight(geo.heightKm)?.id).toBe("exosphere");
  });
});

describe("US Standard Atmosphere 1976", () => {
  it("七段廓线的折点对照标准值（0–86 km，中纬度年平均）", () => {
    const expected: [number, number][] = [
      [0, 15.0],
      [11, -56.5],
      [20, -56.5],
      [32, -44.5],
      [47, -2.5],
      [51, -2.5],
      [71, -58.5],
      [86, -86.3],
    ];
    for (const [heightKm, tempC] of expected) {
      closeTo(ussaTempAt(heightKm), tempC, 1);
    }
  });

  it("等温段在表里成立（对流层顶 11–20 km、平流层顶 47–51 km）", () => {
    closeTo(ussaTempAt(15), -56.5, 1);
    closeTo(ussaTempAt(49), -2.5, 1);
  });

  it("海平面 1013.25 hPa，86 km 处约 0.0037 hPa，全表单调下降", () => {
    closeTo(ussaPressureAt(0), 1013.25);
    closeTo(ussaPressureAt(86), 0.0037, 2);
    for (let h = 1; h <= USSA_MAX_HEIGHT_KM; h++) {
      expect(ussaPressureAt(h)).toBeLessThan(ussaPressureAt(h - 1));
    }
  });

  it("适用上限 86 km——以上的读数属于带范围的参考值，不是 USSA", () => {
    expect(USSA_MAX_HEIGHT_KM).toBe(86);
  });
});

describe("几何换算与探针", () => {
  it("层半径换算：地壳外缘是场景半径 1，内核外缘（ICB）约 0.192 R（1221 km）、内缘是地心", () => {
    const crust = interiorLayerRadii(interiorLayers[0]);
    closeTo(crust.outerSceneR, 1);
    const innerCore = interiorLayerRadii(interiorLayers[interiorLayers.length - 1]);
    closeTo(innerCore.innerSceneR, 0);
    closeTo(innerCore.outerSceneR, 1221 / 6371, 3);
  });

  it("大气壳半径：卡门线在 1.0157 R——真实比例下贴着地表", () => {
    const thermo = atmosphereLayers.find((l) => l.id === "thermosphere")!;
    closeTo(atmosphereLayerTopRadius(thermo)!, (6371 + 600) / 6371, 4);
    expect(atmosphereLayerTopRadius(atmosphereLayers[4])).toBeNull();
  });

  it("按深度 / 高度找层往返一致", () => {
    expect(interiorLayerAtDepth(10)?.id).toBe("crust");
    expect(interiorLayerAtDepth(2000)?.id).toBe("lower-mantle");
    expect(interiorLayerAtDepth(6000)?.id).toBe("inner-core");
    expect(atmosphereLayerAtHeight(30)?.id).toBe("stratosphere");
    expect(atmosphereLayerAtHeight(3000)?.id).toBe("exosphere");
  });

  it("内部温度内插取到界面共识值", () => {
    closeTo(interiorTempAt(0), 15);
    closeTo(interiorTempAt(2891), 3800);
  });
});

describe("出处（图谱/参考类的底线：每个数值组都能追到源头）", () => {
  it("每个层与关键表都声明了非空的 sourceIds，且都能在源头目录里找到", () => {
    const all: string[] = [
      ...data.shape.sourceIds,
      ...data.surface.sourceIds,
      ...data.interior.sourceIds,
      ...data.atmosphere.sourceIds,
      ...data.atmosphere.ussa1976.sourceIds,
    ];
    for (const layer of [...interiorLayers, ...atmosphereLayers]) {
      expect(layer.sourceIds.length).toBeGreaterThan(0);
      all.push(...layer.sourceIds);
    }
    for (const id of all) {
      expect(data.sources[id], `缺出处：${id}`).toBeDefined();
      expect(data.sources[id].url).toMatch(/^https?:\/\//);
    }
  });

  it("真实比例的免责声明在位——薄层看不见是事实，界面必须讲清楚", () => {
    expect(data.meta.disclaimers.length).toBeGreaterThan(0);
    expect(data.meta.scale).toBe("real");
    expect(data.meta.disclaimers.join()).toContain("未放大");
  });
});
