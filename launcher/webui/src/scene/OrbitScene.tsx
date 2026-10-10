import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import * as THREE from "three";
import { openApp, type AppDto, type CatalogDto } from "../api";

const STATE_COLOR: Record<AppDto["state"], string> = {
  stopped: "#b0b4c8",
  starting: "#ff9800",
  ready: "#2e9e44",
};

const SPHERE_R = 34;

// 图标徽章贴图：SVG 光栅化到透明底画布，作为球面正前方贴片的纹理。
// material 随贴图到位用 key 重建（动态挂 map 不触发 shader 重编译，会渲染成白球）。
function useIconTexture(app: AppDto): THREE.Texture | null {
  const [texture, setTexture] = useState<THREE.Texture | null>(null);
  useEffect(() => {
    let alive = true;
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext("2d")!;
    const finish = () => {
      if (!alive) return;
      const tex = new THREE.CanvasTexture(canvas);
      tex.colorSpace = THREE.SRGBColorSpace;
      setTexture(tex);
    };
    if (app.icon) {
      const img = new Image();
      img.onload = () => {
        ctx.clearRect(0, 0, 256, 256);
        ctx.drawImage(img, 28, 28, 200, 200);
        finish();
      };
      img.onerror = finish;
      img.src = app.icon;
    } else {
      // 兜底：accent 圆底 + letter。
      ctx.clearRect(0, 0, 256, 256);
      ctx.fillStyle = app.accent;
      ctx.beginPath();
      ctx.arc(128, 128, 110, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "white";
      ctx.font = "600 96px 'Segoe UI', sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(app.letter.slice(0, 2), 128, 130);
      finish();
    }
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [app.id]);
  return texture;
}

function IconSphere({
  app, index, active, hovered, onHover,
}: {
  app: AppDto;
  index: number;
  active: boolean;
  hovered: boolean;
  onHover: (id: string | null) => void;
}) {
  const [x, y, z] = app.pos;
  const texture = useIconTexture(app);
  const spinner = useRef<THREE.Group>(null);
  // 自转速度与相位按序号差异化，行星各转各的；相位让悬浮错落。
  const spinSpeed = useMemo(() => 0.35 + ((index * 37) % 40) / 100, [index]);
  const floatPhase = useMemo(() => (index * 137.5 * Math.PI) / 180, [index]);
  const elapsed = useRef(0);
  // 自转 + 上下悬浮 + 悬停缩放，全部帧插值。
  useFrame((_, delta) => {
    if (!spinner.current) return;
    elapsed.current += delta;
    spinner.current.rotation.y += spinSpeed * delta;
    spinner.current.position.y = Math.sin(elapsed.current * 0.9 + floatPhase) * 5;
    const target = hovered ? 1.3 : 1;
    const s = spinner.current.scale.x + (target - spinner.current.scale.x) * Math.min(1, delta * 10);
    spinner.current.scale.setScalar(s);
  });

  // 贴片纹理到位前不挂徽章（避免白方块一闪）。
  const badgeReady = texture !== null;

  return (
    <group position={[x, y, z]}>
      {/* 自转组：球体 + 图标徽章 + 状态环一起转，徽章转到背面被球体自然遮挡。 */}
      <group ref={spinner}>
        <mesh
          onClick={() => openApp(app.id).catch(console.error)}
          onPointerOver={(e) => {
            e.stopPropagation();
            onHover(app.id);
          }}
          onPointerOut={() => onHover(null)}
        >
          <sphereGeometry args={[SPHERE_R, 48, 48]} />
          <meshStandardMaterial
            color={app.accent}
            roughness={0.4}
            metalness={0.08}
            transparent
            opacity={active ? 1 : 0.75}
          />
        </mesh>
        {/* 图标徽章：贴在球面正前方的透明贴片，随自转绕球巡行。 */}
        {badgeReady && (
          <mesh position={[0, 0, SPHERE_R + 1.5]}>
            <planeGeometry args={[SPHERE_R * 1.15, SPHERE_R * 1.15]} />
            <meshBasicMaterial map={texture} transparent depthWrite={false} />
          </mesh>
        )}
        {/* 运行状态环：贴着球面的细环。 */}
        <mesh rotation={[Math.PI / 2.6, 0.4, 0]}>
          <torusGeometry args={[SPHERE_R + 7, 2.4, 12, 48]} />
          <meshBasicMaterial color={STATE_COLOR[app.state]} transparent opacity={hovered ? 1 : 0.85} />
        </mesh>
      </group>
      <Html position={[0, -(SPHERE_R + 26), 0]} center distanceFactor={900} zIndexRange={[10, 0]}>
        <div
          style={{
            color: "#3a3a44",
            fontSize: 13,
            textShadow: "0 1px 2px rgba(255,255,255,0.9)",
            whiteSpace: "nowrap",
            textAlign: "center",
            pointerEvents: "none",
            opacity: active ? 1 : 0.6,
            transition: "opacity 140ms",
          }}
        >
          {app.title}
        </div>
      </Html>
    </group>
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
    const material = new THREE.LineBasicMaterial({ color: "#8a97c8", transparent: true, opacity: 0.55 });
    return new THREE.Line(geometry, material);
  }, [radius, tilt, yaw]);
  return <primitive object={line} />;
}

function TigerCore({ hovered }: { hovered: string | null }) {
  // 虎头贴图等图标管线接入后替换成 sprite；骨架阶段用发光核心占位。
  return (
    <group>
      {/* 恒星光：虎头是场景唯一的光源，行星朝向它的一侧亮、背面暗。 */}
      <pointLight color="#ffb45e" intensity={220000} decay={2} distance={8000} />
      <mesh>
        <sphereGeometry args={[92, 48, 48]} />
        <meshStandardMaterial
          color="#e8862e"
          emissive="#a44f10"
          emissiveIntensity={hovered === null ? 0.6 : 0.35}
        />
      </mesh>
    </group>
  );
}

// 领域轨道环（ADR 0125）：虎头居中为恒星，每颗应用是一颗带图标徽章的行星球体；
// 布局坐标全部来自 launcher-core 的 layout3d，前端只渲染。
export default function OrbitScene({ catalog }: { catalog: CatalogDto }) {
  const [hovered, setHovered] = useState<string | null>(null);
  return (
    <Canvas
      camera={{ position: [0, 900, 2100], fov: 55, near: 1, far: 8000 }}
      onCreated={({ camera }) => camera.lookAt(0, 0, 0)}
      style={{ background: "radial-gradient(ellipse at center, #ffffff 0%, #eef0fa 60%, #e3e7f6 100%)" }}
    >
      <ambientLight intensity={1.2} />
      <directionalLight position={[600, 1200, 800]} intensity={1.1} />
      <TigerCore hovered={hovered} />
      {catalog.orbits.map((o, i) => (
        <OrbitRing key={i} radius={o.radius} tilt={o.tilt} yaw={o.yaw} />
      ))}
      {catalog.apps.map((a, i) => (
        <IconSphere
          key={a.id + a.pos.join()}
          app={a}
          index={i}
          active={hovered === null || hovered === a.id}
          hovered={hovered === a.id}
          onHover={setHovered}
        />
      ))}
      <OrbitControls enablePan={false} minDistance={300} maxDistance={4800} />
    </Canvas>
  );
}
