import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import * as THREE from "three";
import { openApp, type AppDto, type CatalogDto, type OrbitDto } from "../api";

const STATE_COLOR: Record<AppDto["state"], string> = {
  stopped: "#b0b4c8",
  starting: "#ff9800",
  ready: "#2e9e44",
};

const SPHERE_R = 34;

// 图标的两张贴图：球面雕纹（accent 底 + 低透明图标，随自转缓缓移动，让自转可见）
// 与正面徽章（透明底全彩图标，始终朝向相机保证可读）。material 随贴图到位用 key
// 重建——动态挂 map 不触发 shader 重编译，会渲染成无贴图的白球。
function useIconTextures(app: AppDto): { sphere: THREE.Texture | null; badge: THREE.Texture | null } {
  const [sphere, setSphere] = useState<THREE.Texture | null>(null);
  const [badge, setBadge] = useState<THREE.Texture | null>(null);
  useEffect(() => {
    let alive = true;
    const make = (draw: (ctx: CanvasRenderingContext2D) => void) => {
      const canvas = document.createElement("canvas");
      canvas.width = 256;
      canvas.height = 256;
      const ctx = canvas.getContext("2d")!;
      draw(ctx);
      const tex = new THREE.CanvasTexture(canvas);
      tex.colorSpace = THREE.SRGBColorSpace;
      return tex;
    };
    const done = (sphereTex: THREE.Texture, badgeTex: THREE.Texture | null) => {
      if (!alive) return;
      setSphere(sphereTex);
      setBadge(badgeTex);
    };
    if (app.icon) {
      const img = new Image();
      img.onload = () => {
        const sphereTex = make((ctx) => {
          ctx.fillStyle = app.accent;
          ctx.fillRect(0, 0, 256, 256);
          ctx.globalAlpha = 0.3;
          ctx.drawImage(img, 48, 48, 160, 160);
          ctx.globalAlpha = 1;
        });
        const badgeTex = make((ctx) => {
          ctx.clearRect(0, 0, 256, 256);
          ctx.drawImage(img, 28, 28, 200, 200);
        });
        done(sphereTex, badgeTex);
      };
      img.onerror = () => { const fb = makeFallback(app.accent, app.letter, false); done(fb.sphere, fb.badge); };
    } else {
      const fb = makeFallback(app.accent, app.letter, true); done(fb.sphere, fb.badge);
    }
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [app.id]);
  return { sphere, badge };
}

function makeFallback(accent: string, letter: string, withBadge: boolean): { sphere: THREE.Texture; badge: THREE.Texture | null } {
  const mk = (draw: (ctx: CanvasRenderingContext2D) => void) => {
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext("2d")!;
    draw(ctx);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    return tex;
  };
  const sphereTex = mk((ctx) => {
    ctx.fillStyle = accent;
    ctx.fillRect(0, 0, 256, 256);
    ctx.fillStyle = "rgba(255,255,255,0.35)";
    ctx.font = "600 120px 'Segoe UI', sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(letter.slice(0, 2), 128, 132);
  });
  const badgeTex = mk((ctx) => {
    ctx.clearRect(0, 0, 256, 256);
    ctx.fillStyle = accent;
    ctx.beginPath();
    ctx.arc(128, 128, 110, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "white";
    ctx.font = "600 96px 'Segoe UI', sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(letter.slice(0, 2), 128, 130);
  });
  return withBadge ? { sphere: sphereTex, badge: badgeTex } : { sphere: sphereTex, badge: null };
}

function IconSphere({
  app, index, orbit, active, hovered, onHover,
}: {
  app: AppDto;
  index: number;
  orbit: OrbitDto;
  active: boolean;
  hovered: boolean;
  onHover: (id: string | null) => void;
}) {
  const { sphere: sphereTex, badge: badgeTex } = useIconTextures(app);
  const spinner = useRef<THREE.Group>(null);
  const planet = useRef<THREE.Group>(null);
  const badge = useRef<THREE.Mesh>(null);
  const camDir = useMemo(() => new THREE.Vector3(), []);
  // 自转速度与相位按序号差异化，行星各转各的；相位让悬浮错落。
  const spinSpeed = useMemo(() => 0.35 + ((index * 37) % 40) / 100, [index]);
  const floatPhase = useMemo(() => (index * 137.5 * Math.PI) / 180, [index]);
  // 公转角速度开普勒式递减：内环快、外环慢（半长轴 300 转一圈约 28 秒）。
  // 取负：theta 递减，从黄道北方俯视为逆时针——与自转同向（真实太阳系的
  // prograde 特性：公转与自转继承同一片星云的角动量方向）。
  const orbitOmega = useMemo(() => -0.22 * (300 / orbit.a), [orbit.a]);
  const elapsed = useRef(0);
  // 公转位置 + 自转 + 上下悬浮 + 悬停缩放，全部帧插值。
  useFrame(({ camera }, delta) => {
    elapsed.current += delta;
    if (planet.current) {
      // 与 core 的 layout3d 同一套正变换，theta 随时间推进即沿椭圆公转
      // （恒星在焦点：近点段视觉上略快，由参数角均匀推进近似）。
      const theta = app.theta + orbitOmega * elapsed.current;
      const px = -orbit.c + orbit.a * Math.cos(theta);
      const pz0 = orbit.b * Math.sin(theta);
      const sl = Math.sin(orbit.tilt), cl = Math.cos(orbit.tilt);
      planet.current.position.set(px, -pz0 * sl, pz0 * cl);
    }
    if (planet.current && badge.current) {
      // 徽章 billboard：悬在行星朝相机的一侧，且平面永远正对屏幕，图标不变形。
      camDir.copy(camera.position).sub(planet.current.position).normalize();
      badge.current.position.copy(camDir).multiplyScalar(SPHERE_R + 1.5);
      badge.current.quaternion.copy(camera.quaternion);
    }
    if (!spinner.current) return;
    spinner.current.rotation.y += spinSpeed * delta;
    spinner.current.position.y = Math.sin(elapsed.current * 0.9 + floatPhase) * 5;
    const target = hovered ? 1.3 : 1;
    const s = spinner.current.scale.x + (target - spinner.current.scale.x) * Math.min(1, delta * 10);
    spinner.current.scale.setScalar(s);
  });

  // 贴图到位前不挂徽章（避免白方块一闪）。
  const badgeReady = badgeTex !== null;

  return (
    <group ref={planet}>
      {/* 自转组：雕纹球体 + 状态环一起转，球面图案缓缓移动让自转可见。 */}
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
            key={sphereTex ? "sphere-map" : "sphere-plain"}
            map={sphereTex ?? undefined}
            color={sphereTex ? "#ffffff" : app.accent}
            roughness={0.4}
            metalness={0.08}
            transparent
            opacity={active ? 1 : 0.75}
          />
        </mesh>
        {/* 运行状态环：贴着球面的细环。 */}
        <mesh rotation={[Math.PI / 2.6, 0.4, 0]}>
          <torusGeometry args={[SPHERE_R + 7, 2.4, 12, 48]} />
          <meshBasicMaterial color={STATE_COLOR[app.state]} transparent opacity={hovered ? 1 : 0.85} />
        </mesh>
      </group>
      {/* 图标徽章：billboard——始终正对相机，位置悬在行星朝相机的一侧，永远清晰。 */}
      {badgeReady && (
        <mesh ref={badge}>
          <planeGeometry args={[SPHERE_R * 1.3, SPHERE_R * 1.3]} />
          <meshBasicMaterial map={badgeTex} transparent depthWrite={false} />
        </mesh>
      )}
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

function OrbitRing({ a, b, c, tilt }: { a: number; b: number; c: number; tilt: number }) {
  // 用 primitive 挂 THREE.Line 而不是 <line> JSX：后者的类型会被 DOM 的 SVG <line> 撞掉。
  const line = useMemo(() => {
    const pts: THREE.Vector3[] = [];
    const sl = Math.sin(tilt), cl = Math.cos(tilt);
    for (let i = 0; i <= 128; i++) {
      const theta = (i / 128) * Math.PI * 2;
      const px = -c + a * Math.cos(theta);
      const pz0 = b * Math.sin(theta);
      pts.push(new THREE.Vector3(px, -pz0 * sl, pz0 * cl));
    }
    const geometry = new THREE.BufferGeometry().setFromPoints(pts);
    const material = new THREE.LineBasicMaterial({ color: "#8a97c8", transparent: true, opacity: 0.55 });
    return new THREE.Line(geometry, material);
  }, [a, b, c, tilt]);
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
        <OrbitRing key={i} a={o.a} b={o.b} c={o.c} tilt={o.tilt} />
      ))}
      {catalog.apps.map((a, i) => (
        <IconSphere
          key={a.id + a.pos.join()}
          app={a}
          index={i}
          orbit={catalog.orbits[a.orbit]}
          active={hovered === null || hovered === a.id}
          hovered={hovered === a.id}
          onHover={setHovered}
        />
      ))}
      <OrbitControls enablePan={false} minDistance={300} maxDistance={4800} />
    </Canvas>
  );
}
