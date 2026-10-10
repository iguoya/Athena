import { useMemo, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import * as THREE from "three";
import { openApp, type AppDto, type CatalogDto } from "../api";

const STATE_COLOR: Record<AppDto["state"], string> = {
  stopped: "#5a5f7a",
  starting: "#ff9800",
  ready: "#4caf50",
};

function IconNode({ app, active, onHover }: { app: AppDto; active: boolean; onHover: (id: string | null) => void }) {
  const [x, y, z] = app.pos;
  return (
    // 图标与中文文字走 DOM 叠加（drei Html）：清晰、可点、可 CSS 动画。
    <Html position={[x, y, z]} center distanceFactor={900} zIndexRange={[10, 0]}>
      <div
        className="tile"
        data-state={app.state}
        style={{
          opacity: active ? 1 : 0.88,
          transform: active ? "scale(1.12)" : "scale(1)",
          transition: "transform 140ms ease-out, opacity 140ms",
        }}
        onClick={() => openApp(app.id).catch(console.error)}
        onMouseEnter={() => onHover(app.id)}
        onMouseLeave={() => onHover(null)}
      >
        {app.icon ? (
          <img src={app.icon} alt="" />
        ) : (
          <div className="fallback" style={{ background: app.accent }}>
            {app.letter}
          </div>
        )}
        <span className="name">{app.title}</span>
        <span className="dot" style={{ background: STATE_COLOR[app.state] }} />
      </div>
    </Html>
  );
}

function OrbitRing({ radius, tilt, yaw }: { radius: number; tilt: number; yaw: number }) {
  // 用 primitive 挂 THREE.Line 而不是 <line> JSX：后者的类型会被 DOM 的 SVG <line> 撞掉。
  const line = useMemo(() => {
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i <= 128; i++) {
      const theta = (i / 128) * Math.PI * 2;
      const px = radius * Math.sin(theta);
      const pz = radius * Math.cos(theta);
      const py = -pz * Math.sin(tilt);
      const pz2 = pz * Math.cos(tilt);
      const v = new THREE.Vector3(px, py, pz2);
      v.applyAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
      pts.push(v);
    }
    const geometry = new THREE.BufferGeometry().setFromPoints(pts);
    const material = new THREE.LineBasicMaterial({ color: "#5468a4", transparent: true, opacity: 0.35 });
    return new THREE.Line(geometry, material);
  }, [radius, tilt, yaw]);
  return <primitive object={line} />;
}

function TigerCore() {
  // 虎头贴图等图标管线接入后替换成 sprite；骨架阶段用发光核心占位。
  return (
    <mesh>
      <sphereGeometry args={[46, 32, 32]} />
      <meshStandardMaterial color="#e8862e" emissive="#a44f10" emissiveIntensity={0.6} />
    </mesh>
  );
}

// 领域轨道环（ADR 0125）：虎头居中，每个领域一条倾斜轨道，图标是环上的行星；
// 布局坐标全部来自 launcher-core 的 layout3d，前端只渲染。
export default function OrbitScene({ catalog }: { catalog: CatalogDto }) {
  const [hovered, setHovered] = useState<string | null>(null);
  return (
    <Canvas
      camera={{ position: [0, 900, 2100], fov: 55, near: 1, far: 8000 }}
      onCreated={({ camera }) => camera.lookAt(0, 0, 0)}
      style={{ background: "radial-gradient(ellipse at center, #141833 0%, #0d1020 70%)" }}
    >
      <ambientLight intensity={0.9} />
      <TigerCore />
      {catalog.orbits.map((o, i) => (
        <OrbitRing key={i} radius={o.radius} tilt={o.tilt} yaw={o.yaw} />
      ))}
      {catalog.apps.map((a) => (
        <IconNode
          key={a.id + a.pos.join()}
          app={a}
          active={hovered === null || hovered === a.id}
          onHover={setHovered}
        />
      ))}
      <OrbitControls enablePan={false} minDistance={300} maxDistance={4800} />
    </Canvas>
  );
}
