import { Html } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import {
  ballisticPath,
  demoSeconds,
  greatCirclePoint,
  routeDistanceKm,
  stageHeights,
} from "../content/demo";
import { data } from "../content/load";
import { useEarth } from "../state/store";

const STAGE_COLORS: Record<string, string> = {
  boost: "#ef4444",
  midcourse: "#f59e0b",
  reentry: "#c084fc",
};

function polyline(points: THREE.Vector3[]): THREE.BufferGeometry {
  return new THREE.BufferGeometry().setFromPoints(points);
}

/** 演示层：选中的航线/弹道常驻画线，播放时标记沿轨迹移动（进度跟随模拟时钟）。 */
export function DemoLayer() {
  const demo = useEarth((s) => s.demo);
  const playing = useEarth((s) => s.playing);
  const replayKey = useEarth((s) => s.replayKey);
  const markerRef = useRef<THREE.Mesh>(null);
  const progress = useRef(0);

  const model = useMemo(() => {
    if (!demo) return null;
    if (demo.kind === "air") {
      const route = data.demos.routes.find((r) => r.id === demo.id);
      const craft = data.demos.aircraft[0];
      if (!route) return null;
      const steps = 128;
      const points = Array.from({ length: steps + 1 }, (_, i) =>
        greatCirclePoint(route.from, route.to, i / steps, craft.cruiseHeightKm),
      );
      const seconds = demoSeconds("air", {
        routeKm: routeDistanceKm(route),
        speedKmh: craft.cruiseSpeedKmh,
      });
      return { kind: "air" as const, route, craft, points, seconds };
    }
    const spec = data.demos.ballistics.find((b) => b.id === demo.id);
    if (!spec) return null;
    const profile = spec.id === "df-17" ? "glide" : "arc";
    const samples = ballisticPath(data.demos.launch, spec, profile);
    const segments = (["boost", "midcourse", "reentry"] as const).map((stage) => ({
      stage,
      points: samples.filter((s) => s.stage === stage).map((s) => s.point),
    }));
    const apex = samples.reduce((best, s) => (s.heightKm > best.heightKm ? s : best), samples[0]);
    const heights = stageHeights(samples);
    // 三段分界点：助推结束 / 再入起点各标一次射高
    const boostEnd = samples.filter((s) => s.stage === "boost").at(-1)!;
    const reentryStart = samples.find((s) => s.stage === "reentry")!;
    const endpoints = { launch: samples[0].point, landing: samples[samples.length - 1].point };
    return {
      kind: "ballistic" as const,
      spec,
      samples,
      segments,
      apex,
      heights,
      boostEnd,
      reentryStart,
      endpoints,
      seconds: demoSeconds("ballistic", { stageMinutes: spec.stageMinutes }),
    };
  }, [demo]);

  // 每次重播把进度清零
  useEffect(() => {
    progress.current = 0;
  }, [replayKey, demo]);

  const total = model?.seconds ?? 1;
  // 弹道用自己的播放倍率（几分钟的飞行不能被自转倍率压成一秒）；航线仍跟自转时钟
  const rate = () =>
    model?.kind === "ballistic"
      ? useEarth.getState().demoScale
      : useEarth.getState().spinScale;
  useFrame((_, dt) => {
    if (!model || !playing || progress.current >= 1) return;
    progress.current = Math.min(1, progress.current + (dt * rate()) / total);
    const path =
      model.kind === "air" ? model.points : model.samples.map((s) => s.point);
    const marker = markerRef.current;
    if (marker) {
      const scaled = progress.current * (path.length - 1);
      const i = Math.min(Math.floor(scaled), path.length - 2);
      const frac = scaled - i;
      const position = path[i].clone().lerp(path[i + 1], frac);
      marker.position.copy(position);
      if (scaled + 1 < path.length) {
        marker.lookAt(path[i + 1]);
      }
    }
  });

  if (!model) return null;
  const progressRatio = progress.current;

  return (
    <group>
      {model.kind === "air" ? (
        <line>
          <primitive object={polyline(model.points)} attach="geometry" />
          <lineBasicMaterial color={model.craft.colorHint} />
        </line>
      ) : (
        model.segments.map(
          (segment) =>
            segment.points.length > 1 && (
              <line key={segment.stage}>
                <primitive object={polyline(segment.points)} attach="geometry" />
                <lineBasicMaterial color={STAGE_COLORS[segment.stage]} />
              </line>
            ),
        )
      )}
      {/* 顶点标注（弹道）：中段在外太空是这类演示的核心教学点 */}
      {model.kind === "ballistic" && (
        <group position={model.apex.point}>
          <mesh>
            <sphereGeometry args={[0.008, 12, 12]} />
            <meshBasicMaterial color="#fde047" />
          </mesh>
          <Html center style={{ pointerEvents: "none" }} zIndexRange={[45, 40]}>
            <div className="earth-label">
              中段顶点 ≈ {model.heights.apexKm} km{model.heights.apexKm > 100 ? " · 太空" : ""}
            </div>
          </Html>
        </group>
      )}
      {model.kind === "ballistic" &&
        (
          [
            ["助推结束", model.boostEnd, model.heights.boostEndKm],
            ["再入起点", model.reentryStart, model.heights.reentryStartKm],
          ] as const
        ).map(([label, sample, km]) => (
          <group key={label} position={sample.point}>
            <mesh>
              <sphereGeometry args={[0.005, 10, 10]} />
              <meshBasicMaterial color={STAGE_COLORS[sample.stage]} />
            </mesh>
            <Html center style={{ pointerEvents: "none" }} zIndexRange={[45, 40]}>
              <div className="earth-label">
                {label} ≈ {km} km
              </div>
            </Html>
          </group>
        ))}
      {model.kind === "ballistic" && (
        <>
          <group position={model.endpoints.launch}>
            <Html center style={{ pointerEvents: "none" }} zIndexRange={[45, 40]}>
              <div className="earth-label">示意发射点</div>
            </Html>
          </group>
          <group position={model.endpoints.landing}>
            <mesh>
              <sphereGeometry args={[0.006, 10, 10]} />
              <meshBasicMaterial color="#c084fc" />
            </mesh>
            <Html center style={{ pointerEvents: "none" }} zIndexRange={[45, 40]}>
              <div className="earth-label">示意落点</div>
            </Html>
          </group>
        </>
      )}
      {/* 移动标记：三角锥朝向轨迹切线 */}
      <mesh ref={markerRef}>
        <coneGeometry args={[0.008, 0.024, 6]} />
        <meshBasicMaterial color={model.kind === "air" ? model.craft.colorHint : "#fbbf24"} />
      </mesh>
      {/* 进度条（3D 内不放，读数在演示面板；这里只做起飞点的静止标记） */}
      {progressRatio === 0 && (
        <mesh
          position={
            model.kind === "air"
              ? model.points[0]
              : model.samples[0].point
          }
        >
          <sphereGeometry args={[0.006, 10, 10]} />
          <meshBasicMaterial color="#94a3b8" />
        </mesh>
      )}
    </group>
  );
}
