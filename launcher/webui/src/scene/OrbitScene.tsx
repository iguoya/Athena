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

// 球面贴图：领域色底 + 图标 4×2 全球平铺。material 随贴图到位用 key 重建——
// 动态挂 map 不触发 shader 重编译，会渲染成无贴图的白球。
type TexStatus = "loading" | "loaded" | "error" | "no-icon";

function useSphereTexture(app: AppDto): { texture: THREE.Texture | null; status: TexStatus } {
  const [texture, setTexture] = useState<THREE.Texture | null>(null);
  const [status, setStatus] = useState<TexStatus>("loading");
  useEffect(() => {
    let alive = true;
    const make = (draw: (ctx: CanvasRenderingContext2D) => void, w = 256, h = 256) => {
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d")!;
      draw(ctx);
      const tex = new THREE.CanvasTexture(canvas);
      tex.colorSpace = THREE.SRGBColorSpace;
      tex.wrapS = THREE.RepeatWrapping;
      return tex;
    };
    const done = (texture: THREE.Texture, st: TexStatus) => {
      if (!alive) return;
      setStatus(st);
      setTexture(texture);
    };
    if (app.icon) {
      const img = new Image();
      // 这个 WebView2 里 img 的 load/error 事件不可靠（永不触发），complete/
      // naturalWidth 属性却是同步可查的——轮询它代替事件。
      img.src = app.icon;
      const poll = setInterval(() => {
        if (!alive) {
          clearInterval(poll);
          return;
        }
        if (img.complete && img.naturalWidth > 0) {
          clearInterval(poll);
          const texture = make((ctx) => {
            ctx.fillStyle = app.accent;
            ctx.fillRect(0, 0, 1024, 512);
            for (let row = 0; row < 2; row++) {
              for (let col = 0; col < 4; col++) {
                ctx.drawImage(img, col * 256 + 63, row * 256 + 63, 130, 130);
              }
            }
          }, 1024, 512);
          done(texture, "loaded");
        } else if (img.complete) {
          clearInterval(poll);
          const fb = makeFallback(app.accent, app.letter);
          done(fb.texture, "error");
        }
      }, 80);
    } else {
      const fb = makeFallback(app.accent, app.letter);
      done(fb.texture, "no-icon");
    }
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [app.id]);
  return { texture, status };
}

function makeFallback(accent: string, letter: string): { texture: THREE.Texture } {
  const mk = (draw: (ctx: CanvasRenderingContext2D) => void, w = 256, h = 256) => {
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d")!;
    draw(ctx);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.wrapS = THREE.RepeatWrapping;
    return tex;
  };
  const texture = mk((ctx) => {
    ctx.fillStyle = accent;
    ctx.fillRect(0, 0, 1024, 512);
    ctx.fillStyle = "rgba(255,255,255,0.4)";
    ctx.font = "600 96px 'Segoe UI', sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    for (let row = 0; row < 2; row++) {
      for (let col = 0; col < 4; col++) {
        ctx.fillText(letter.slice(0, 2), col * 256 + 128, row * 256 + 128);
      }
    }
  }, 1024, 512);
  return { texture };
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
  const { texture: sphereTex } = useSphereTexture(app);
  const spinner = useRef<THREE.Group>(null);
  const planet = useRef<THREE.Group>(null);
  // 自转速度与相位按序号差异化，行星各转各的；相位让悬浮错落。
  const spinSpeed = useMemo(() => 0.35 + ((index * 37) % 40) / 100, [index]);
  const floatPhase = useMemo(() => (index * 137.5 * Math.PI) / 180, [index]);
  // 公转角速度开普勒式递减：内环快、外环慢（半长轴 300 转一圈约 28 秒）。
  // 取负：theta 递减，从黄道北方俯视为逆时针——与自转同向（真实太阳系的
  // prograde 特性：公转与自转继承同一片星云的角动量方向）。
  const orbitOmega = useMemo(() => -0.22 * (300 / orbit.a), [orbit.a]);
  const elapsed = useRef(0);
  // 公转位置 + 自转 + 上下悬浮 + 悬停缩放，全部帧插值。
  useFrame((_, delta) => {
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
    if (!spinner.current) return;
    spinner.current.rotation.y += spinSpeed * delta;
    spinner.current.position.y = Math.sin(elapsed.current * 0.9 + floatPhase) * 5;
    const target = hovered ? 1.3 : 1;
    const s = spinner.current.scale.x + (target - spinner.current.scale.x) * Math.min(1, delta * 10);
    spinner.current.scale.setScalar(s);
  });

  return (
    <group ref={planet}>
      {/* 自转组：雕纹球体 + 状态环一起转，球面图案缓缓移动让自转可见。 */}
      <group ref={spinner}>
        <mesh
          castShadow
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

// 黄道面：单层圆盘，径向渐变的半透明贴图 + 承接行星投影，一个 mesh 干两件事。
function EclipticPlane() {
  const gradTex = useMemo(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext("2d")!;
    const grad = ctx.createRadialGradient(256, 256, 30, 256, 256, 256);
    grad.addColorStop(0, "rgba(84, 104, 164, 0.25)");
    grad.addColorStop(0.55, "rgba(84, 104, 164, 0.12)");
    grad.addColorStop(1, "rgba(84, 104, 164, 0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 512, 512);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    return tex;
  }, []);
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -8, 0]} receiveShadow>
      <circleGeometry args={[2400, 96]} />
      <meshStandardMaterial map={gradTex} transparent depthWrite={false} roughness={1} />
    </mesh>
  );
}

function TigerCore({ hovered }: { hovered: string | null }) {
  // 虎头贴图等图标管线接入后替换成 sprite；骨架阶段用发光核心占位。
  return (
    <group>
      {/* 恒星光：虎头是场景唯一的光源，行星朝向它的一侧亮、背面暗。 */}
      <pointLight color="#ffb45e" intensity={220000} decay={2} distance={8000} />
      <mesh castShadow>
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

// 领域轨道环（ADR 0125）：虎头居中为恒星，每颗应用是一颗贴着自家图标的行星球体；
// 布局坐标全部来自 launcher-core 的 layout3d，前端只渲染。
export default function OrbitScene({ catalog }: { catalog: CatalogDto }) {
  const [hovered, setHovered] = useState<string | null>(null);
  return (
    <Canvas
      shadows
      camera={{ position: [0, 900, 2100], fov: 55, near: 1, far: 8000 }}
      onCreated={({ camera }) => camera.lookAt(0, 0, 0)}
      style={{ background: "radial-gradient(ellipse at center, #ffffff 0%, #eef0fa 60%, #e3e7f6 100%)" }}
    >
      <ambientLight intensity={1.2} />
      <directionalLight
        position={[600, 1200, 800]}
        intensity={1.1}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-left={-2400}
        shadow-camera-right={2400}
        shadow-camera-top={2400}
        shadow-camera-bottom={-2400}
        shadow-camera-near={1}
        shadow-camera-far={6000}
        shadow-bias={-0.0005}
      />
      <EclipticPlane />
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
