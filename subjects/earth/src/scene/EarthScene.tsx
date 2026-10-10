import { Html, OrbitControls, useTexture } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import surfaceTextureUrl from "../assets/earth-blue-marble.png";
import {
  atmosphereLayers,
  data,
  densityAt,
  densityColor,
  EARTH_RADIUS_KM,
  EXOSPHERE_FADE_KM,
  interiorLayerRadii,
  interiorLayers,
  kmToScene,
} from "../content/load";
import { useEarth } from "../state/store";

// 剖切平面：切掉 x>0 与 z>0 的四分之一（THREE 约定 normal·p + c < 0 的部分被裁）。
const CLIP_PLANES = [
  new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0),
  new THREE.Plane(new THREE.Vector3(0, 0, -1), 0),
];

/** WGS 84 椭球：整组沿极轴压扁，比例是真实的（赤道比极半径长约 21.4 km）。 */
const POLAR_SCALE = data.shape.polarRadiusKm / data.shape.equatorialRadiusKm;

// 剖面上的径向标尺方向（单位向量，组内坐标）：盘 A（x=0，z<0 半圆）放内部锚点与探针，
// 盘 B（z=0，x<0 半圆）放大气锚点——各占一片截面，互不打架。
const PROBE_DIR = new THREE.Vector3(0, -0.55, -0.835).normalize();
const INTERIOR_RULER_DIR = new THREE.Vector3(0, 0.5, -0.866).normalize();
const ATMOS_RULER_DIR = new THREE.Vector3(-0.45, 0.893, 0).normalize();

function Stars() {
  const geometry = useMemo(() => {
    const count = 900;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const radius = 12 + Math.random() * 12;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.cos(phi);
      positions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return geometry;
  }, []);
  return (
    <points geometry={geometry}>
      <pointsMaterial size={0.045} color="#8ea6cf" sizeAttenuation />
    </points>
  );
}

function Globe({ clippingPlanes }: { clippingPlanes: THREE.Plane[] }) {
  const texture = useTexture(surfaceTextureUrl);
  return (
    <mesh renderOrder={2}>
      <sphereGeometry args={[1, 128, 96]} />
      {/* 剖开后可见的球面是切缘旁的窄条，单一方向光总有照不到的角度——
          贴图同时作 emissiveMap 保底，灯光只负责立体感 */}
      <meshStandardMaterial
        map={texture}
        emissive="#ffffff"
        emissiveMap={texture}
        emissiveIntensity={0.42}
        roughness={0.9}
        metalness={0}
        clippingPlanes={clippingPlanes}
        clipShadows
      />
    </mesh>
  );
}

/** 内部各层：只画外缘球壳（半透明），剖开时从开口看到内壁层次。 */
function InteriorShells({ clippingPlanes }: { clippingPlanes: THREE.Plane[] }) {
  return (
    <>
      {interiorLayers.map((layer, index) => {
        const { outerSceneR } = interiorLayerRadii(layer);
        return (
          <mesh key={layer.id} renderOrder={4 + index}>
            <sphereGeometry args={[outerSceneR, 96, 64]} />
            <meshBasicMaterial
              color={layer.colorHint}
              transparent
              opacity={0.14}
              side={THREE.DoubleSide}
              depthWrite={false}
              clippingPlanes={clippingPlanes}
            />
          </mesh>
        );
      })}
    </>
  );
}

/**
 * 剖面截面：两个半圆盘（x=0 与 z=0），每层一环，颜色由 PREM 密度映射——
 * 界面处的密度跳跃直接可见，颜色是算出来的（ADR 0056），不是手涂的。
 */
function SectionFaces() {
  const rings = interiorLayers.map((layer) => {
    const { innerSceneR, outerSceneR } = interiorLayerRadii(layer);
    const midDepth = (layer.topDepthKm + layer.bottomDepthKm) / 2;
    return {
      id: layer.id,
      name: layer.name,
      innerSceneR,
      outerSceneR,
      color: densityColor(densityAt(midDepth)),
      layer,
    };
  });

  return (
    <>
      {/* 盘 B：z=0 平面（XY 几何天然落在该平面），保留 x<0 半圆 */}
      {rings.map((ring) => (
        <mesh key={`faceB-${ring.id}`} renderOrder={20}>
          <ringGeometry
            args={[Math.max(ring.innerSceneR, 0.001), ring.outerSceneR, 128, 1, Math.PI / 2, Math.PI]}
          />
          <meshBasicMaterial color={ring.color} side={THREE.DoubleSide} />
        </mesh>
      ))}
      {/* 盘 A：x=0 平面（绕 Y 转 -90° 后 x<0 半圆落到 z<0），保留 z<0 半圆 */}
      {rings.map((ring) => (
        <mesh key={`faceA-${ring.id}`} rotation={[0, -Math.PI / 2, 0]} renderOrder={20}>
          <ringGeometry
            args={[Math.max(ring.innerSceneR, 0.001), ring.outerSceneR, 128, 1, Math.PI / 2, Math.PI]}
          />
          <meshBasicMaterial color={ring.color} side={THREE.DoubleSide} />
        </mesh>
      ))}
    </>
  );
}

/** 大气辉光：卡门线高度的壳 + fresnel 边缘增亮。真实比例下它是贴着地表的一圈薄光。 */
function AtmosphereGlow() {
  const material = useRef<THREE.ShaderMaterial>(null);
  const radius = kmToScene(EARTH_RADIUS_KM + data.atmosphere.karmanLineKm);
  const uniforms = useMemo(
    () => ({ uColor: { value: new THREE.Color("#7fb3e8") } }),
    [],
  );
  return (
    <mesh renderOrder={6}>
      <sphereGeometry args={[radius, 96, 64]} />
      <shaderMaterial
        ref={material}
        uniforms={uniforms}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        vertexShader={`
          varying vec3 vNormal;
          varying vec3 vView;
          void main() {
            vNormal = normalize(normalMatrix * normal);
            vec4 mv = modelViewMatrix * vec4(position, 1.0);
            vView = normalize(-mv.xyz);
            gl_Position = projectionMatrix * mv;
          }
        `}
        fragmentShader={`
          uniform vec3 uColor;
          varying vec3 vNormal;
          varying vec3 vView;
          void main() {
            float rim = pow(1.0 - abs(dot(normalize(vNormal), normalize(vView))), 3.0);
            gl_FragColor = vec4(uColor, rim * 0.55);
          }
        `}
      />
    </mesh>
  );
}

/** 外逸层渐隐包络：上界不封闭，画到 10000 km 处以极低透明度消失（数据 note 的呈现落地）。 */
function ExosphereEnvelope() {
  const radius = kmToScene(EARTH_RADIUS_KM + EXOSPHERE_FADE_KM);
  return (
    <mesh renderOrder={1}>
      <sphereGeometry args={[radius, 64, 48]} />
      <meshBasicMaterial
        color="#24344f"
        transparent
        opacity={0.06}
        side={THREE.BackSide}
        depthWrite={false}
      />
    </mesh>
  );
}

/** 盘 A（x=0，z<0）上的一圈界线弧：大气各层顶与内部锚点刻度共用。 */
function ArcOnFaceA({
  radiusKm,
  color,
  thicknessKm = 9,
  opacity = 0.9,
}: {
  radiusKm: number;
  color: string;
  thicknessKm?: number;
  opacity?: number;
}) {
  const r = kmToScene(radiusKm);
  const half = kmToScene(thicknessKm) / 2;
  return (
    <mesh rotation={[0, -Math.PI / 2, 0]} renderOrder={22}>
      <ringGeometry args={[Math.max(r - half, 0.0005), r + half, 128, 1, Math.PI / 2, Math.PI]} />
      <meshBasicMaterial color={color} transparent opacity={opacity} side={THREE.DoubleSide} />
    </mesh>
  );
}

function Label({
  position,
  text,
  strong = false,
  offsetY = 0,
}: {
  position: [number, number, number];
  text: string;
  strong?: boolean;
  offsetY?: number;
}) {
  return (
    <Html position={position} center style={{ pointerEvents: "none" }} zIndexRange={[50, 40]}>
      <div
        className={`earth-label ${strong ? "earth-label-strong" : ""}`}
        style={{ whiteSpace: "nowrap", transform: `translateY(${offsetY}px)` }}
      >
        {text}
      </div>
    </Html>
  );
}

/** 内部锚点标尺：一条从地表向内的刻度线，锚点画在其半径处。 */
function InteriorRuler({ showLabels }: { showLabels: boolean }) {
  const start = INTERIOR_RULER_DIR.clone().multiplyScalar(1);
  const end = INTERIOR_RULER_DIR.clone().multiplyScalar(kmToScene(EARTH_RADIUS_KM - 700) * 0.985);
  const line = useMemo(() => {
    const geometry = new THREE.BufferGeometry().setFromPoints([start, end]);
    return new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: "#d8b45a" }));
  }, [start, end]);
  return (
    <>
      <primitive object={line} />
      {data.interior.keyPoints.map((point) => {
        const r = kmToScene(EARTH_RADIUS_KM - point.depthKm);
        const position = INTERIOR_RULER_DIR.clone().multiplyScalar(r);
        return (
          <group key={point.name}>
            <ArcOnFaceA radiusKm={EARTH_RADIUS_KM - point.depthKm} color="#d8b45a" thicknessKm={6} />
            {showLabels && (
              <Label
                position={position.toArray()}
                text={`${point.name} · ${point.depthKm} km`}
              />
            )}
          </group>
        );
      })}
    </>
  );
}

/** 大气锚点标尺：一条伸向 35786 km（地球静止轨道）的刻度线——真实比例下大气外的世界。 */
function AtmosphereRuler({ showLabels }: { showLabels: boolean }) {
  const geoKm = data.atmosphere.keyPoints;
  const maxKm = Math.max(...geoKm.map((p) => p.heightKm));
  const start = ATMOS_RULER_DIR.clone().multiplyScalar(1.002);
  const end = ATMOS_RULER_DIR.clone().multiplyScalar(kmToScene(EARTH_RADIUS_KM + maxKm) * 1.01);
  const line = useMemo(() => {
    const geometry = new THREE.BufferGeometry().setFromPoints([start, end]);
    return new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: "#9db8dd" }));
  }, [start, end]);
  return (
    <>
      <primitive object={line} />
      {/* 真实比例下 11–535 km 的锚点都挤在地表附近，标签沿标尺方向梯次错开才读得了 */}
      {geoKm.map((point, index) => {
        const r = kmToScene(EARTH_RADIUS_KM + point.heightKm);
        const position = ATMOS_RULER_DIR.clone().multiplyScalar(r);
        return (
          <group key={point.name}>
            <mesh position={position} renderOrder={22}>
              <sphereGeometry args={[0.006, 8, 8]} />
              <meshBasicMaterial color="#9db8dd" />
            </mesh>
            {showLabels && (
              <Label
                position={position.toArray()}
                text={`${point.name} · ${point.heightKm} km`}
                offsetY={index * 15 - 20}
              />
            )}
          </group>
        );
      })}
    </>
  );
}

/** 探针：盘 A 上沿径向移动的读数点（interior=深度，atmosphere=高度）。 */
function Probe() {
  const probeMode = useEarth((s) => s.probeMode);
  const probeKm = useEarth((s) => s.probeKm);
  const radius =
    probeMode === "interior"
      ? EARTH_RADIUS_KM - probeKm
      : EARTH_RADIUS_KM + probeKm;
  // 几何只建一次（0 → 单位方向），移动探针靠缩放，不重建缓冲。
  const line = useMemo(() => {
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      PROBE_DIR,
    ]);
    return new THREE.Line(
      geometry,
      new THREE.LineBasicMaterial({ color: "#ffd54a" }),
    );
  }, []);
  const point = PROBE_DIR.clone().multiplyScalar(kmToScene(radius));
  return (
    <>
      <primitive object={line} scale={kmToScene(radius)} />
      <mesh position={point} renderOrder={30}>
        <sphereGeometry args={[0.014, 16, 16]} />
        <meshBasicMaterial color="#ffd54a" />
      </mesh>
    </>
  );
}

/** 相机距离的阻尼飞行 + 节流上报（比例尺换算用）。 */
function CameraRig() {
  const focusDistance = useEarth((s) => s.focusDistance);
  const arrive = useEarth((s) => s.arrive);
  const frames = useRef(0);
  useFrame((state, dt) => {
    const distance = state.camera.position.length();
    if (focusDistance != null) {
      const direction = state.camera.position.clone().normalize();
      const next = THREE.MathUtils.damp(distance, focusDistance, 3.5, dt);
      state.camera.position.copy(direction.multiplyScalar(next));
      if (Math.abs(next - focusDistance) < 0.005) arrive();
    }
    frames.current += 1;
    if (frames.current % 12 === 0) {
      useEarth.getState().reportDistance(state.camera.position.length());
    }
  });
  return null;
}

export function EarthScene() {
  const cutaway = useEarth((s) => s.cutaway);
  const showLabels = useEarth((s) => s.showLabels);
  const clippingPlanes = cutaway ? CLIP_PLANES : [];

  return (
    <>
      <color attach="background" args={["#0b1020"]} />
      <Stars />
      {/* 可见的保留球面是 +x 或 +z 两侧的「牙」，只有接近顶部的光能同时照到它们；
          剖面盘是 BasicMaterial 不受光，不怕被照花 */}
      <ambientLight intensity={0.6} />
      <directionalLight position={[1.2, 5, 1.2]} intensity={2.0} />
      <group scale={[1, POLAR_SCALE, 1]}>
        {cutaway && <SectionFaces />}
        <Globe clippingPlanes={clippingPlanes} />
        <InteriorShells clippingPlanes={clippingPlanes} />
        <AtmosphereGlow />
        <ExosphereEnvelope />
        {cutaway && (
          <>
            {atmosphereLayers.map((layer) =>
              layer.topHeightKm === null ? null : (
                <ArcOnFaceA
                  key={layer.id}
                  radiusKm={EARTH_RADIUS_KM + layer.topHeightKm}
                  color={layer.colorHint}
                  thicknessKm={7}
                  opacity={0.85}
                />
              ),
            )}
            <InteriorRuler showLabels={showLabels} />
            <AtmosphereRuler showLabels={showLabels} />
            <Probe />
          </>
        )}
      </group>
      <OrbitControls
        makeDefault
        enablePan={false}
        minDistance={1.02}
        maxDistance={12}
        dampingFactor={0.08}
      />
      <CameraRig />
    </>
  );
}
