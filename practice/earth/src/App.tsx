import { useEffect } from "react";
import { AviationView } from "./panels/AviationView";
import { formatKm, viewportWidthKm, AtmosphereChart, InteriorChart } from "./panels/ProfileChart";
import { DemoPanel } from "./panels/DemoPanel";
import { LayerDetail } from "./panels/LayerDetail";
import { LayerList } from "./panels/LayerList";
import { ProbePanel } from "./panels/ProbePanel";
import { EarthCanvas } from "./scene/EarthCanvas";
import { EarthScene } from "./scene/EarthScene";
import { GLOBAL_VIEW_FOCUS, GROUND_VIEW_FOCUS } from "./scene/viewpoints";
import { KEYPOINT_CATEGORY_NAMES, KEYPOINT_COLORS, data } from "./content/load";
import { useEarth, type ViewMode } from "./state/store";

const FOV = 40;

const SPIN_OPTIONS = [
  { label: "真实", scale: 1, title: "真实速度：恒星日 23h56m，肉眼几乎看不出转动" },
  { label: "×600", scale: 600, title: "模拟时间流速 600 倍：约 2.4 分钟自转一圈" },
  { label: "×3600", scale: 3600, title: "模拟时间流速 3600 倍：24 秒自转一圈，昼夜交替明显" },
];

const VIEW_OPTIONS: { mode: ViewMode; label: string; title: string }[] = [
  { mode: "aviation", label: "航空视角", title: "0–50 km 的空中事务专题：飞行器、鸟类与现象的海拔剖面" },
  { mode: "space", label: "太空视角", title: "全球 3D：地面视角观空中，层界环与居民标尺按真实高度" },
  { mode: "interior", label: "内部剖面", title: "四分之一剖切看地球内部：PREM 密度着色的截面" },
];

/** 居民锚点图例：颜色 → 类型（数据来自 keyPoints 的 category） */
function LegendHud() {
  return (
    <div className="pointer-events-none absolute right-3 top-3 rounded bg-slate-900/70 px-2.5 py-1.5 text-xs text-slate-300 backdrop-blur">
      <div className="mb-1 font-medium text-slate-200">空中居民</div>
      <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
        {Object.entries(KEYPOINT_CATEGORY_NAMES).map(([key, name]) => (
          <span key={key} className="flex items-center gap-1.5">
            <span style={{ color: KEYPOINT_COLORS[key] }}>●</span>
            {name}
          </span>
        ))}
      </div>
    </div>
  );
}

function ScaleHud() {
  const cameraDistanceR = useEarth((s) => s.cameraDistanceR);
  const view = useEarth((s) => s.view);
  return (
    <div className="pointer-events-none absolute bottom-3 left-3 space-y-1 text-xs text-slate-300">
      <div className="rounded bg-slate-900/70 px-2 py-1 backdrop-blur">
        当前视野宽度 ≈ {formatKm(viewportWidthKm(cameraDistanceR, FOV))}
      </div>
      {view === "interior" ? (
        <div className="rounded bg-slate-900/70 px-2 py-1 backdrop-blur">
          剖面截面按 PREM 密度着色（1–13.5 g/cm³，viridis 色标）· 拖动旋转 · 右键平移 · 滚轮缩放
        </div>
      ) : (
        <div className="rounded bg-slate-900/70 px-2 py-1 backdrop-blur">
          太空视角：层界环与居民标尺按真实高度 · 50 km 内的细分看「航空视角」
        </div>
      )}
    </div>
  );
}

export function App() {
  const view = useEarth((s) => s.view);
  const setView = useEarth((s) => s.setView);
  const showLabels = useEarth((s) => s.showLabels);
  const toggleLabels = useEarth((s) => s.toggleLabels);
  const flyTo = useEarth((s) => s.flyTo);
  const spinScale = useEarth((s) => s.spinScale);
  const setSpinScale = useEarth((s) => s.setSpinScale);

  // 切进 3D 视图时把相机放到该视图的观察点；航空视图是 2D 剖面，不消费相机。
  useEffect(() => {
    if (view === "space") flyTo(GROUND_VIEW_FOCUS);
    if (view === "interior") flyTo(GLOBAL_VIEW_FOCUS);
  }, [view, flyTo]);

  return (
    <div className="flex h-screen flex-col bg-slate-50 text-slate-900">
      <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-2.5">
        <h1 className="text-base font-semibold">
          {data.meta.title}
          <span className="ml-2 rounded-full bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-800">
            真实比例 · 垂直方向未放大
          </span>
        </h1>
        <div className="ml-auto flex items-center gap-1.5 text-xs">
          <div className="flex items-center overflow-hidden rounded-md ring-1 ring-slate-200">
            {VIEW_OPTIONS.map((option, index) => (
              <button
                key={option.mode}
                onClick={() => setView(option.mode)}
                title={option.title}
                className={`px-3 py-1.5 font-medium transition-colors ${
                  index > 0 ? "border-l border-slate-200" : ""
                } ${
                  view === option.mode
                    ? "bg-sky-600 text-white"
                    : "bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
          <button
            onClick={toggleLabels}
            className={`rounded-md px-2.5 py-1.5 font-medium transition-colors ${
              showLabels
                ? "bg-sky-600 text-white"
                : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
            }`}
          >
            标注
          </button>
          {view !== "aviation" && (
            <>
              <span className="mx-1 text-slate-300">|</span>
              <div className="flex items-center overflow-hidden rounded-md ring-1 ring-slate-200">
                {SPIN_OPTIONS.map((option, index) => (
                  <button
                    key={option.scale}
                    onClick={() => setSpinScale(option.scale)}
                    title={option.title}
                    className={`px-2.5 py-1.5 font-medium transition-colors ${
                      index > 0 ? "border-l border-slate-200" : ""
                    } ${
                      spinScale === option.scale
                        ? "bg-sky-600 text-white"
                        : "bg-white text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    自转 {option.label}
                  </button>
                ))}
              </div>
              {view === "space" && (
                <button
                  onClick={() => flyTo(GLOBAL_VIEW_FOCUS)}
                  className="rounded-md bg-white px-2.5 py-1.5 font-medium text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
                >
                  全貌
                </button>
              )}
            </>
          )}
        </div>
      </header>
      <main className="flex min-h-0 flex-1">
        <div className="relative min-w-0 flex-1 bg-[#0b1020]">
          {view === "aviation" ? (
            <AviationView />
          ) : (
            <EarthCanvas>
              <EarthScene />
            </EarthCanvas>
          )}
          {view !== "aviation" && (
            <>
              <ScaleHud />
              {view === "space" && <LegendHud />}
            </>
          )}
        </div>
        <aside className="w-[340px] shrink-0 space-y-3 overflow-y-auto border-l border-slate-200 bg-slate-50 p-3">
          <LayerDetail />
          <DemoPanel />
          <ProbePanel />
          <LayerList />
          <section className="rounded-lg border border-slate-200 bg-white p-3">
            <AtmosphereChart />
          </section>
          <section className="rounded-lg border border-slate-200 bg-white p-3">
            <InteriorChart />
          </section>
          <p className="px-1 pb-2 text-xs leading-relaxed text-slate-400">{data.meta.note}</p>
        </aside>
      </main>
    </div>
  );
}

