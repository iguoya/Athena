import * as THREE from "three";
import type { BallisticSpec, FlightRoute, LaunchSite } from "./types";
import { EARTH_RADIUS_KM, kmToScene } from "./load";

// 演示轨迹的纯函数：经纬度 → 场景坐标、大圆航线插值、示意弹道剖面。
// 弹道是教学示意（正弦高度剖面），不是真实飞行程序——数据文件里的
// ballisticNote 与出处条目是口径的锚。

const DEG = Math.PI / 180;

/**
 * 经纬度 → 场景坐标。与 three SphereGeometry 的等距圆柱贴图对齐：
 * 推导自其顶点公式（u = (lon+180)/360），保证「北京」落在贴图的北京上。
 */
export function lonLatToScene(
  lonDeg: number,
  latDeg: number,
  heightKm = 0,
): THREE.Vector3 {
  const lat = latDeg * DEG;
  const lon = lonDeg * DEG;
  const r = kmToScene(EARTH_RADIUS_KM + heightKm);
  return new THREE.Vector3(
    Math.cos(lon) * Math.cos(lat) * r,
    Math.sin(lat) * r,
    -Math.sin(lon) * Math.cos(lat) * r,
  );
}

/** 球面两点角距（弧度） */
export function centralAngle(fromLonLat: [number, number], toLonLat: [number, number]): number {
  const [lon1, lat1] = fromLonLat.map((d) => d * DEG) as [number, number];
  const [lon2, lat2] = toLonLat.map((d) => d * DEG) as [number, number];
  return Math.acos(
    Math.min(
      1,
      Math.sin(lat1) * Math.sin(lat2) +
        Math.cos(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1),
    ),
  );
}

/** 大圆航线距离（km） */
export function routeDistanceKm(route: Pick<FlightRoute, "from" | "to">): number {
  return centralAngle(route.from, route.to) * EARTH_RADIUS_KM;
}

/**
 * 沿大圆的插值点：t ∈ [0,1]，0 = 起点、1 = 终点。用向量 slerp，
 * 与贴图坐标同源（lonLatToScene），不经过经纬度中转。
 */
export function greatCirclePoint(
  fromLonLat: [number, number],
  toLonLat: [number, number],
  t: number,
  heightKm = 0,
): THREE.Vector3 {
  const v0 = lonLatToScene(fromLonLat[0], fromLonLat[1], 0).normalize();
  const v1 = lonLatToScene(toLonLat[0], toLonLat[1], 0).normalize();
  const omega = Math.acos(Math.min(1, v0.dot(v1)));
  const point =
    omega < 1e-6
      ? v0.clone()
      : v0
          .clone()
          .multiplyScalar(Math.sin((1 - t) * omega) / Math.sin(omega))
          .add(v1.clone().multiplyScalar(Math.sin(t * omega) / Math.sin(omega)));
  return point.multiplyScalar(kmToScene(EARTH_RADIUS_KM + heightKm));
}

/** 已知起点、方位角与角距的球面落点（大圆航行的 destination point 公式） */
export function destinationPoint(
  fromLonLat: [number, number],
  bearingDeg: number,
  angularDistance: number,
): [number, number] {
  const [lon1, lat1] = [fromLonLat[0] * DEG, fromLonLat[1] * DEG];
  const delta = angularDistance;
  const bearing = bearingDeg * DEG;
  const lat2 = Math.asin(
    Math.sin(lat1) * Math.cos(delta) + Math.cos(lat1) * Math.sin(delta) * Math.cos(bearing),
  );
  const lon2 =
    lon1 +
    Math.atan2(
      Math.sin(bearing) * Math.sin(delta) * Math.cos(lat1),
      Math.cos(delta) - Math.sin(lat1) * Math.sin(lat2),
    );
  return [(lon2 / DEG + 540) % 360 - 180, lat2 / DEG];
}

export interface BallisticSample {
  point: THREE.Vector3;
  heightKm: number;
  t: number;
  stage: "boost" | "midcourse" | "reentry";
}

/**
 * 示意弹道采样：沿发射方位的大圆走 rangeKm，高度剖面分两种——
 * 「arc」抛物线形（正弦近似）与「glide」高超滑翔形（爬升—压平—俯冲）。
 * 三段的划分按比例固定：助推 / 中段 / 再入，教学示意，非真实程序。
 */
export function ballisticPath(
  launch: LaunchSite,
  spec: Pick<BallisticSpec, "rangeKm" | "apogeeKm">,
  profile: "arc" | "glide" = "arc",
  steps = 160,
): BallisticSample[] {
  const delta = spec.rangeKm / EARTH_RADIUS_KM;
  const landing = destinationPoint(launch.lonLat, launch.bearingDeg, delta);
  const samples: BallisticSample[] = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    let heightKm: number;
    if (profile === "glide") {
      const climb = 0.16;
      const dive = 0.88;
      if (t < climb) {
        heightKm = spec.apogeeKm * (t / climb);
      } else if (t < dive) {
        // 压平的滑翔段：在顶点附近缓缓掉高度
        heightKm = spec.apogeeKm * (0.96 - 0.2 * ((t - climb) / (dive - climb)));
      } else {
        heightKm = spec.apogeeKm * 0.76 * (1 - (t - dive) / (1 - dive));
      }
    } else {
      heightKm = spec.apogeeKm * Math.sin(Math.PI * t);
    }
    const point = greatCirclePoint(launch.lonLat, landing, t, Math.max(heightKm, 0));
    const stage: BallisticSample["stage"] =
      t < 0.12 ? "boost" : t < 0.88 ? "midcourse" : "reentry";
    samples.push({ point, heightKm, t, stage });
  }
  return samples;
}

/** 三段分界处的示意射高（km，近似到 5 km），读自 ballisticPath 的剖面采样 */
export interface StageHeights {
  boostEndKm: number;
  apexKm: number;
  reentryStartKm: number;
}

export function stageHeights(samples: BallisticSample[]): StageHeights {
  const round5 = (km: number) => Math.round(km / 5) * 5;
  const lastOf = (stage: BallisticSample["stage"]) =>
    samples.filter((s) => s.stage === stage).at(-1)!;
  const firstOf = (stage: BallisticSample["stage"]) =>
    samples.find((s) => s.stage === stage)!;
  return {
    boostEndKm: round5(lastOf("boost").heightKm),
    apexKm: round5(Math.max(...samples.map((s) => s.heightKm))),
    reentryStartKm: round5(firstOf("reentry").heightKm),
  };
}

/** 演示的模拟时长（秒，真实时间） */
export function demoSeconds(
  kind: "air" | "ballistic",
  args: { routeKm?: number; speedKmh?: number; stageMinutes?: number },
): number {
  if (kind === "air") {
    return ((args.routeKm ?? 0) / (args.speedKmh ?? 1)) * 3600;
  }
  return (args.stageMinutes ?? 10) * 60;
}
