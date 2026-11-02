import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import * as THREE from "three";
import { openApp, stopApp, type AppDto, type CatalogDto, type OrbitDto, type PlanetDto } from "../api";

// 星系（ADR 0125 修订）：一恒星、多行星、多卫星。
// 恒星 = 绑定到中心的应用；每个分组是一颗行星，独占一条椭圆轨道，绑定了应用的分组里
// 那个应用就是行星本身；组内其余应用是卫星，围着本组行星转。
// 半径常量与 core 的 layout3d 一致（STAR_R / PLANET_R / MOON_R），改一处要改两处。
const STAR_R = 92;
const PLANET_R = 44;
const MOON_R = 18;

const STATE_COLOR: Record<AppDto["state"], string> = {
  stopped: "#b0b4c8",
  starting: "#ff9800",
  ready: "#2e9e44",
};

/** 球面贴图所需的最小视觉信息：应用与「无应用的组球」共用。 */
interface Visual {
  id: string;
  icon: string | null;
  groupColor: string;
  accent: string;
  letter: string;
}

// 球面贴图：领域色底 + 图标 2×2 全球平铺。material 随贴图到位用 key 重建——
// 动态挂 map 不触发 shader 重编译，会渲染成无贴图的白球。
function useSphereTexture(v: Visual): THREE.Texture | null {
  const [texture, setTexture] = useState<THREE.Texture | null>(null);
  useEffect(() => {
    let alive = true;
    const done = (tex: THREE.Texture) => {
      if (alive) setTexture(tex);
    };
    if (v.icon) {
      const img = new Image();
      // 这个 WebView2 里 img 的 load/error 事件不可靠（永不触发），complete/
      // naturalWidth 属性却是同步可查的——轮询它代替事件。
      img.src = v.icon;
      const poll = setInterval(() => {
        if (!alive) {
          clearInterval(poll);
          return;
        }
        if (img.complete && img.naturalWidth > 0) {
          clearInterval(poll);
          done(
            makeTexture((ctx) => {
              ctx.fillStyle = v.groupColor;
              ctx.fillRect(0, 0, 1024, 512);
              for (let row = 0; row < 2; row++) {
                for (let col = 0; col < 2; col++) {
                  ctx.drawImage(img, col * 512 + 136, row * 256 + 8, 240, 240);
                }
              }
            }),
          );
        } else if (img.complete) {
          clearInterval(poll);
          done(makeFallback(v.accent, v.letter));
        }
      }, 80);
      return () => {
        alive = false;
        clearInterval(poll);
      };
    }
    done(makeFallback(v.accent, v.letter));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [v.id, v.icon]);
  return texture;
}

function makeTexture(draw: (ctx: CanvasRenderingContext2D) => void): THREE.Texture {
  const canvas = document.createElement("canvas");
  canvas.width = 1024;
  canvas.height = 512;
  draw(canvas.getContext("2d")!);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = THREE.RepeatWrapping;
  return tex;
}

function makeFallback(accent: string, letter: string): THREE.Texture {
  return makeTexture((ctx) => {
    ctx.fillStyle = accent;
    ctx.fillRect(0, 0, 1024, 512);
    ctx.fillStyle = "rgba(255,255,255,0.4)";
    ctx.font = "600 96px 'Segoe UI', sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    for (let row = 0; row < 2; row++) {
      for (let col = 0; col < 2; col++) {
        ctx.fillText(letter.slice(0, 2), col * 512 + 256, row * 256 + 128);
      }
    }
  });
}

interface BodyProps {
  visual: Visual;
  radius: number;
  label: string;
  /** 小字补注（待学 / 未安装）。 */
  notes: string[];
  state: AppDto["state"] | null;
  /** 点击行为；组球（没绑定应用）没有。 */
  appId: string | null;
  index: number;
  dim: number;
  active: boolean;
  hovered: boolean;
  glow?: boolean;
  fontSize: number;
  onHover: (id: string | null) => void;
}

// 一颗球：自转 + 上下悬浮 + 悬停放大 + 图标贴图 + 标题。恒星、行星、卫星同一套。
function Body(p: BodyProps) {
  const tex = useSphereTexture(p.visual);
  const spinner = useRef<THREE.Group>(null);
  const spinSpeed = useMemo(() => 0.35 + ((p.index * 37) % 40) / 100, [p.index]);
  const phase = useMemo(() => (p.index * 137.5 * Math.PI) / 180, [p.index]);
  const t = useRef(0);
  useFrame((_, delta) => {
    t.current += delta;
    if (!spinner.current) return;
    spinner.current.rotation.y += spinSpeed * delta;
    spinner.current.position.y = Math.sin(t.current * 0.9 + phase) * p.radius * 0.12;
    const target = p.hovered ? 1.25 : 1;
    const s = spinner.current.scale.x + (target - spinner.current.scale.x) * Math.min(1, delta * 10);
    spinner.current.scale.setScalar(s);
  });
  const clickable = p.appId !== null;
  return (
    <>
      <group ref={spinner}>
        <mesh
          castShadow
          onClick={(e) => {
            if (!clickable) return;
            e.stopPropagation();
            openApp(p.appId!).catch(console.error);
          }}
          onContextMenu={(e) => {
            if (!clickable) return;
            e.stopPropagation();
            e.nativeEvent.preventDefault();
            if (p.state && p.state !== "stopped") stopApp(p.appId!).catch(console.error);
          }}
          onPointerOver={(e) => {
            e.stopPropagation();
            p.onHover(p.visual.id);
          }}
          onPointerOut={() => p.onHover(null)}
        >
          <sphereGeometry args={[p.radius, 48, 48]} />
          <meshStandardMaterial
            key={tex ? "sphere-map" : "sphere-plain"}
            map={tex ?? undefined}
            color={tex ? "#ffffff" : p.visual.groupColor}
            roughness={0.4}
            metalness={0.08}
            transparent
            opacity={(p.active ? 1 : 0.75) * p.dim}
            // 恒星自发光：它是场景唯一的光源，不能被自己的光照成暗面。
            emissive={p.glow ? "#ffffff" : "#000000"}
            emissiveMap={p.glow ? tex ?? undefined : undefined}
            emissiveIntensity={p.glow ? 0.55 : 0}
          />
        </mesh>
      </group>
      <Html position={[0, -(p.radius + 18 + p.fontSize), 0]} center distanceFactor={900} zIndexRange={[10, 0]}>
        <div
          style={{
            color: "#3a3a44",
            fontSize: p.fontSize,
            textShadow: "0 1px 2px rgba(255,255,255,0.9)",
            whiteSpace: "nowrap",
            textAlign: "center",
            pointerEvents: "none",
            opacity: (p.active ? 1 : 0.6) * (p.dim < 1 ? 0.7 : 1),
            transition: "opacity 140ms",
          }}
        >
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            {p.label}
            {p.notes.map((n) => (
              <span key={n} style={{ opacity: 0.65 }}>· {n}</span>
            ))}
            {p.state && (
              <span style={{
                width: 7, height: 7, borderRadius: "50%",
                background: STATE_COLOR[p.state], display: "inline-block",
              }} />
            )}
          </span>
        </div>
      </Html>
    </>
  );
}

function notesOf(app: AppDto): string[] {
  const n: string[] = [];
  if (app.lifecycle === "built") n.push("待学");
  if (app.installed === false) n.push("未安装");
  return n;
}

function dimOf(app: AppDto): number {
  // 建成待学（ADR 0139）降视觉权重；未安装的更淡。
  return (app.lifecycle === "built" ? 0.55 : 1) * (app.installed === false ? 0.4 : 1);
}

// 卫星公转角速度：内环快外环慢（r=80 约 7 秒一圈），与半径 1.5 次方成反比。
const moonOmega = (r: number) => 0.9 * Math.pow(80 / r, 1.5);

function Moon({
  app, index, hovered, active, onHover,
}: {
  app: AppDto;
  index: number;
  hovered: string | null;
  active: boolean;
  onHover: (id: string | null) => void;
}) {
  const orbit = useRef<THREE.Group>(null);
  const moon = app.moon!;
  const omega = moonOmega(moon.radius);
  const elapsed = useRef(0);
  useFrame((_, delta) => {
    elapsed.current += delta;
    if (!orbit.current) return;
    const th = moon.theta + omega * elapsed.current;
    orbit.current.position.set(moon.radius * Math.cos(th), 0, moon.radius * Math.sin(th));
  });
  return (
    <group ref={orbit}>
      <Body
        visual={app}
        radius={MOON_R}
        label={app.title}
        notes={notesOf(app)}
        state={app.state}
        appId={app.id}
        index={index}
        dim={dimOf(app)}
        active={active}
        hovered={hovered === app.id}
        fontSize={12}
        onHover={onHover}
      />
    </group>
  );
}

// 卫星环的轨迹线：在行星周围画一圈淡线，让「围着转」看得见。
function MoonRing({ radius, color }: { radius: number; color: string }) {
  const line = useMemo(() => {
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i <= 96; i++) {
      const th = (i / 96) * Math.PI * 2;
      pts.push(new THREE.Vector3(radius * Math.cos(th), 0, radius * Math.sin(th)));
    }
    const geometry = new THREE.BufferGeometry().setFromPoints(pts);
    const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.35 });
    return new THREE.Line(geometry, material);
  }, [radius, color]);
  return <primitive object={line} />;
}

function Planet({
  planet, orbit, app, moons, index, hovered, onHover,
}: {
  planet: PlanetDto;
  orbit: OrbitDto;
  app: AppDto | null;
  moons: AppDto[];
  index: number;
  hovered: string | null;
  onHover: (id: string | null) => void;
}) {
  const group = useRef<THREE.Group>(null);
  // 公转角速度开普勒式递减：内环快、外环慢（半长轴 420 转一圈约 31 秒）。
  // 取负：theta 递减，从黄道北方俯视为逆时针——与自转同向。
  const omega = useMemo(() => -0.2 * (420 / orbit.a), [orbit.a]);
  const elapsed = useRef(0);
  useFrame((_, delta) => {
    elapsed.current += delta;
    if (!group.current) return;
    // 与 core 的 layout3d 同一套正变换，theta 随时间推进即沿椭圆公转。
    const th = planet.theta + omega * elapsed.current;
    const px = -orbit.c + orbit.a * Math.cos(th);
    const pz0 = orbit.b * Math.sin(th);
    const sl = Math.sin(orbit.tilt), cl = Math.cos(orbit.tilt);
    group.current.position.set(px, -pz0 * sl, pz0 * cl);
  });

  const visual: Visual = app ?? {
    id: `group:${planet.group}`,
    icon: null,
    groupColor: planet.color,
    accent: planet.color,
    letter: planet.group.slice(0, 1),
  };
  const planetId = visual.id;
  const rings = useMemo(
    () => Array.from(new Set(moons.map((m) => m.moon!.ring))).sort((a, b) => a - b),
    [moons],
  );
  const ringRadius = (ring: number) => moons.find((m) => m.moon!.ring === ring)!.moon!.radius;
  // 悬停本组任何一员，整组保持高亮：行星与卫星是一个整体。
  const groupIds = useMemo(() => [planetId, ...moons.map((m) => m.id)], [planetId, moons]);
  const groupHot = hovered !== null && groupIds.includes(hovered);
  const active = hovered === null || groupHot;

  return (
    <group ref={group}>
      <Body
        visual={visual}
        radius={PLANET_R}
        label={app ? app.title : planet.group}
        notes={app ? notesOf(app) : []}
        state={app ? app.state : null}
        appId={app ? app.id : null}
        index={index}
        dim={app ? dimOf(app) : 1}
        active={active}
        hovered={hovered === planetId}
        fontSize={15}
        onHover={onHover}
      />
      {/* 卫星面略倾斜且逐环交替，免得所有环共面成一张唱片。 */}
      {rings.map((ring) => (
        <group key={ring} rotation={[(ring % 2 === 0 ? 1 : -1) * 0.32, 0, 0]}>
          <MoonRing radius={ringRadius(ring)} color={planet.color} />
          {moons
            .filter((m) => m.moon!.ring === ring)
            .map((m, i) => (
              <Moon
                key={m.id}
                app={m}
                index={index * 7 + ring * 3 + i}
                hovered={hovered}
                active={active}
                onHover={onHover}
              />
            ))}
        </group>
      ))}
    </group>
  );
}

function OrbitRing({ a, b, c, tilt }: { a: number; b: number; c: number; tilt: number }) {
  // 用 primitive 挂 THREE.Line 而不是 <line> JSX：后者的类型会被 DOM 的 SVG <line> 撞掉。
  const line = useMemo(() => {
    const pts: THREE.Vector3[] = [];
    const sl = Math.sin(tilt), cl = Math.cos(tilt);
    for (let i = 0; i <= 192; i++) {
      const theta = (i / 192) * Math.PI * 2;
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
function EclipticPlane({ radius }: { radius: number }) {
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
      <circleGeometry args={[radius, 96]} />
      <meshStandardMaterial map={gradTex} transparent depthWrite={false} roughness={1} />
    </mesh>
  );
}

// 恒星：绑定到中心的应用（目前是北极星），点击打开；没有就是占位的发光球。
function Star({ app, hovered, onHover }: { app: AppDto | null; hovered: string | null; onHover: (id: string | null) => void }) {
  const visual: Visual = app ?? { id: "star", icon: null, groupColor: "#e8862e", accent: "#e8862e", letter: "" };
  return (
    <group>
      {/* 恒星光：场景唯一的光源，行星朝向它的一侧亮、背面暗。 */}
      <pointLight color="#ffe2b0" intensity={260000} decay={2} distance={12000} />
      <Body
        visual={visual}
        radius={STAR_R}
        label={app ? app.title : ""}
        notes={app ? notesOf(app) : []}
        state={app ? app.state : null}
        appId={app ? app.id : null}
        index={0}
        dim={app ? dimOf(app) : 1}
        active={hovered === null || hovered === visual.id}
        hovered={hovered === visual.id}
        glow
        fontSize={17}
        onHover={onHover}
      />
    </group>
  );
}

export default function OrbitScene({ catalog, paused }: { catalog: CatalogDto; paused: boolean }) {
  const [hovered, setHovered] = useState<string | null>(null);
  const byId = useMemo(() => new Map(catalog.apps.map((a) => [a.id, a])), [catalog.apps]);
  const star = catalog.apps.find((a) => a.role === "star") ?? null;
  const moonsOf = useMemo(() => {
    const m = new Map<number, AppDto[]>();
    for (const a of catalog.apps) {
      if (a.role !== "moon" || !a.moon) continue;
      m.set(a.moon.group, [...(m.get(a.moon.group) ?? []), a]);
    }
    return m;
  }, [catalog.apps]);
  // 整个星系的尺度由最外轨道决定：镜头、黄道盘、阴影范围都跟着它走。
  const maxA = catalog.orbits.reduce((m, o) => Math.max(m, o.a), 600);
  return (
    <Canvas
      shadows
      // 挂起时彻底停帧：托盘隐藏时 WebView 的遮挡检测通常已停掉 rAF，
      // frameloop="never" 是双保险，保证常驻状态下一帧都不画。
      frameloop={paused ? "never" : "always"}
      camera={{ position: [0, maxA * 0.55, maxA * 1.15], fov: 55, near: 1, far: maxA * 6 }}
      onCreated={({ camera }) => camera.lookAt(0, 0, 0)}
      style={{ background: "radial-gradient(ellipse at center, #ffffff 0%, #eef0fa 60%, #e3e7f6 100%)" }}
    >
      <ambientLight intensity={1.2} />
      <directionalLight
        position={[maxA * 0.25, maxA * 0.5, maxA * 0.35]}
        intensity={1.1}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-left={-maxA * 1.3}
        shadow-camera-right={maxA * 1.3}
        shadow-camera-top={maxA * 1.3}
        shadow-camera-bottom={-maxA * 1.3}
        shadow-camera-near={1}
        shadow-camera-far={maxA * 3}
        shadow-bias={-0.0005}
      />
      <EclipticPlane radius={maxA * 1.15} />
      <Star app={star} hovered={hovered} onHover={setHovered} />
      {catalog.orbits.map((o, i) => (
        <OrbitRing key={i} a={o.a} b={o.b} c={o.c} tilt={o.tilt} />
      ))}
      {catalog.planets.map((p, i) => (
        <Planet
          key={p.group}
          planet={p}
          orbit={catalog.orbits[p.orbit]}
          app={p.appId ? byId.get(p.appId) ?? null : null}
          moons={moonsOf.get(p.orbit) ?? []}
          index={i}
          hovered={hovered}
          onHover={setHovered}
        />
      ))}
      <OrbitControls enablePan={false} minDistance={200} maxDistance={maxA * 3.2} />
    </Canvas>
  );
}
