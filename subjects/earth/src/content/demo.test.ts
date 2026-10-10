import { describe, expect, it } from "vitest";
import {
  ballisticPath,
  centralAngle,
  demoSeconds,
  destinationPoint,
  greatCirclePoint,
  lonLatToScene,
  routeDistanceKm,
} from "./demo";
import { data } from "./load";

const closeTo = (actual: number, expected: number, digits = 4) =>
  expect(actual).toBeCloseTo(expected, digits);

describe("经纬度 → 场景坐标", () => {
  it("赤道上的经度映射与 three SphereGeometry 贴图一致：lon 0 在 +x，lon -180 在 -x", () => {
    const gulfOfGuinea = lonLatToScene(0, 0);
    closeTo(gulfOfGuinea.x, 1);
    closeTo(gulfOfGuinea.z, 0);
    const pacific = lonLatToScene(-180, 0);
    closeTo(pacific.x, -1);
  });

  it("北极在 +y，地表半径为场景单位 1，高度按 km 加", () => {
    const north = lonLatToScene(0, 90);
    closeTo(north.y, 1);
    closeTo(north.x, 0);
    const karman = lonLatToScene(0, 0, 100);
    expect(karman.length()).toBeGreaterThan(1);
    closeTo(karman.length(), (6371 + 100) / 6371, 3);
  });
});

describe("大圆航线", () => {
  it("京沪大圆距离约 1080 km（公开航线常识量级）", () => {
    const route = data.demos.routes.find((r) => r.id === "pek-sha")!;
    const km = routeDistanceKm(route);
    expect(km).toBeGreaterThan(1000);
    expect(km).toBeLessThan(1200);
  });

  it("京纽大圆约 11000 km，比平面地图的直线观感远得多", () => {
    const route = data.demos.routes.find((r) => r.id === "pek-jfk")!;
    const km = routeDistanceKm(route);
    expect(km).toBeGreaterThan(10400);
    expect(km).toBeLessThan(11600);
  });

  it("slerp 起终点准确、中点在大圆上且距两端等角", () => {
    const from: [number, number] = [116.4, 39.9];
    const to: [number, number] = [-74.0, 40.7];
    const start = greatCirclePoint(from, to, 0);
    const startExpected = lonLatToScene(from[0], from[1]);
    expect(start.distanceTo(startExpected)).toBeLessThan(1e-6);
    const mid = greatCirclePoint(from, to, 0.5);
    const half = centralAngle(from, to) / 2;
    closeTo(
      mid.angleTo(lonLatToScene(from[0], from[1]).normalize()),
      half,
      3,
    );
  });
});

describe("球面落点（发射方位 + 角距）", () => {
  it("零距离原地不动，等距离沿方位走", () => {
    const same = destinationPoint([108, 36], 75, 0);
    closeTo(same[0], 108, 6);
    closeTo(same[1], 36, 6);
    const landed = destinationPoint([108, 36], 75, 0.5);
    closeTo(centralAngle([108, 36], landed as [number, number]), 0.5, 5);
  });

  it("东风演示的落点与射程一致（角距 = 射程 / 地球半径）", () => {
    const df41 = data.demos.ballistics.find((b) => b.id === "df-41")!;
    const launch = data.demos.launch;
    const landing = destinationPoint(
      launch.lonLat,
      launch.bearingDeg,
      df41.rangeKm / 6371,
    );
    closeTo(
      centralAngle(launch.lonLat, landing as [number, number]) * 6371,
      df41.rangeKm,
      2,
    );
  });
});

describe("示意弹道剖面", () => {
  it("两端在地面、中段在顶点附近、整体先升后降", () => {
    const launch = data.demos.launch;
    const df26 = data.demos.ballistics.find((b) => b.id === "df-26")!;
    const path = ballisticPath(launch, df26);
    closeTo(path[0].heightKm, 0, 6);
    closeTo(path[path.length - 1].heightKm, 0, 6);
    closeTo(path[Math.floor(path.length / 2)].heightKm, df26.apogeeKm, 2);
    const maxH = Math.max(...path.map((s) => s.heightKm));
    closeTo(maxH, df26.apogeeKm, 2);
  });

  it("滑翔体剖面：爬升后压平（中段不回到正弦拱顶），末端俯冲到地面", () => {
    const launch = data.demos.launch;
    const df17 = data.demos.ballistics.find((b) => b.id === "df-17")!;
    const path = ballisticPath(launch, df17, "glide");
    closeTo(path[0].heightKm, 0, 6);
    closeTo(path[path.length - 1].heightKm, 0, 6);
    const mid = path[Math.floor(path.length / 2)].heightKm;
    // 滑翔段高度保持在顶点的七成以上，与抛物线（正弦）的中点 = 顶点区分开
    expect(mid).toBeGreaterThan(df17.apogeeKm * 0.7);
    expect(mid).toBeLessThan(df17.apogeeKm * 0.97);
  });

  it("弹道教学点：洲际顶点远超卡门线与空间站轨道，且三段划分在场", () => {
    const df41 = data.demos.ballistics.find((b) => b.id === "df-41")!;
    expect(df41.apogeeKm).toBeGreaterThan(1000);
    expect(df41.apogeeKm).toBeGreaterThan(408 * 3);
    const path = ballisticPath(data.demos.launch, df41);
    const stages = new Set(path.map((s) => s.stage));
    expect(stages).toEqual(new Set(["boost", "midcourse", "reentry"]));
  });
});

describe("演示时钟", () => {
  it("民航用时 = 距离 ÷ 速度的真实小时数，弹道用全程分钟", () => {
    closeTo(demoSeconds("air", { routeKm: 1080, speedKmh: 850 }) / 3600, 1.27, 1);
    closeTo(demoSeconds("ballistic", { stageMinutes: 26 }) / 60, 26);
  });
});
