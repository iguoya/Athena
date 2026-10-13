import { create } from "zustand";
import type { ViewFocus } from "../scene/viewpoints";

export type ProbeMode = "interior" | "atmosphere";

export type { ViewFocus };

export interface DemoSelection {
  kind: "air" | "ballistic";
  id: string;
}

interface EarthState {
  /** 剖面开关：默认关——第一眼是全球 + 地面视角观空中（内部构成不抢戏）；
      开 = 切掉 x>0、z>0 四分之一，露出两片密度着色的截面。 */
  cutaway: boolean;
  /** 选中的层 id（内部与大气层的 id 不冲突） */
  selectedLayerId: string | null;
  probeMode: ProbeMode;
  /** interior 模式 = 深度（0–6371 km）；atmosphere 模式 = 高度（0–1000 km） */
  probeKm: number;
  showLabels: boolean;
  /** 相机飞行目标；null = 不在飞行中。target 可以不是地心（否则看不了大气薄层） */
  focus: ViewFocus | null;
  /** 相机当前到观察目标的距离（R），由 CameraRig 节流上报，供视野比例尺换算 */
  cameraDistanceR: number;
  /** 自转时间倍率：真实恒星日 86164 s × 倍率 */
  spinScale: number;
  /** 弹道演示的播放倍率（真实时间 ÷ 演示时间），与自转倍率分开：几分钟的飞行不能被 ×600 压成一秒 */
  demoScale: number;
  /** 飞行演示：选中即常驻画线，playing 时标记沿轨迹移动 */
  demo: DemoSelection | null;
  playing: boolean;
  replayKey: number;
  setCutaway: (cutaway: boolean) => void;
  select: (layerId: string | null) => void;
  setProbeMode: (mode: ProbeMode) => void;
  setProbeKm: (km: number) => void;
  toggleLabels: () => void;
  flyTo: (focus: ViewFocus) => void;
  arrive: () => void;
  reportDistance: (distanceR: number) => void;
  setSpinScale: (spinScale: number) => void;
  setDemoScale: (demoScale: number) => void;
  startDemo: (demo: DemoSelection) => void;
  stopDemo: () => void;
  togglePlay: () => void;
  replay: () => void;
}

export const useEarth = create<EarthState>((set) => ({
  cutaway: false,
  selectedLayerId: null,
  probeMode: "interior",
  probeKm: 0,
  showLabels: true,
  focus: null,
  cameraDistanceR: 4.2,
  spinScale: 600,
  demoScale: 15,
  demo: null,
  playing: false,
  replayKey: 0,
  setCutaway: (cutaway) => set({ cutaway }),
  select: (selectedLayerId) => set({ selectedLayerId }),
  setProbeMode: (probeMode) =>
    set({ probeMode, probeKm: probeMode === "interior" ? 0 : 12 }),
  setProbeKm: (probeKm) => set({ probeKm }),
  toggleLabels: () => set((s) => ({ showLabels: !s.showLabels })),
  flyTo: (focus) => set({ focus }),
  arrive: () => set({ focus: null }),
  reportDistance: (cameraDistanceR) => set({ cameraDistanceR }),
  setSpinScale: (spinScale) => set({ spinScale }),
  setDemoScale: (demoScale) => set({ demoScale }),
  startDemo: (demo) => set({ demo, playing: true, replayKey: Date.now() }),
  stopDemo: () => set({ demo: null, playing: false }),
  togglePlay: () => set((s) => (s.demo ? { playing: !s.playing } : {})),
  replay: () => set((s) => (s.demo ? { playing: true, replayKey: Date.now() } : {})),
}));
