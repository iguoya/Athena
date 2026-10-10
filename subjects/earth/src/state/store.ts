import { create } from "zustand";

export type ProbeMode = "interior" | "atmosphere";

interface EarthState {
  /** 剖面开关：开（默认）= 切掉 x>0、z>0 四分之一，露出两片密度着色的截面 */
  cutaway: boolean;
  /** 选中的层 id（内部与大气层的 id 不冲突） */
  selectedLayerId: string | null;
  probeMode: ProbeMode;
  /** interior 模式 = 深度（0–6371 km）；atmosphere 模式 = 高度（0–1000 km） */
  probeKm: number;
  showLabels: boolean;
  /** 相机目标距离（场景单位 R）；null = 不在飞行中 */
  focusDistance: number | null;
  /** 相机当前距离（R），由 CameraRig 节流上报，供视野比例尺换算 */
  cameraDistanceR: number;
  setCutaway: (cutaway: boolean) => void;
  select: (layerId: string | null) => void;
  setProbeMode: (mode: ProbeMode) => void;
  setProbeKm: (km: number) => void;
  toggleLabels: () => void;
  flyTo: (distanceR: number) => void;
  arrive: () => void;
  reportDistance: (distanceR: number) => void;
}

export const useEarth = create<EarthState>((set) => ({
  cutaway: true,
  selectedLayerId: null,
  probeMode: "interior",
  probeKm: 0,
  showLabels: true,
  focusDistance: null,
  cameraDistanceR: 4.2,
  setCutaway: (cutaway) => set({ cutaway }),
  select: (selectedLayerId) => set({ selectedLayerId }),
  setProbeMode: (probeMode) =>
    set({ probeMode, probeKm: probeMode === "interior" ? 0 : 12 }),
  setProbeKm: (probeKm) => set({ probeKm }),
  toggleLabels: () => set((s) => ({ showLabels: !s.showLabels })),
  flyTo: (focusDistance) => set({ focusDistance }),
  arrive: () => set({ focusDistance: null }),
  reportDistance: (cameraDistanceR) => set({ cameraDistanceR }),
}));
