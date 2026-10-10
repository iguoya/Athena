import { formatKm, viewportWidthKm, AtmosphereChart, InteriorChart } from "./panels/ProfileChart";
import { LayerDetail } from "./panels/LayerDetail";
import { LayerList } from "./panels/LayerList";
import { ProbePanel } from "./panels/ProbePanel";
import { EarthCanvas } from "./scene/EarthCanvas";
import { ATMOS_FOCUS_TARGET, EarthScene } from "./scene/EarthScene";import { data } from "./content/load";
import { useEarth } from "./state/store";

const FOV = 40;

const SPIN_OPTIONS = [
  { label: "真实", scale: 1, title: "真实速度：恒星日 23h56m，肉眼几乎看不出转动" },
  { label: "×600", scale: 600, title: "模拟时间流速 600 倍：约 2.4 分钟自转一圈" },
  { label: "×3600", scale: 3600, title: "模拟时间流速 3600 倍：24 秒自转一圈，昼夜交替明显" },
];

function ScaleHud() {
  const cameraDistanceR = useEarth((s) => s.cameraDistanceR);
  const cutaway = useEarth((s) => s.cutaway);
  return (
    <div className="pointer-events-none absolute bottom-3 left-3 space-y-1 text-xs text-slate-300">
      <div className="rounded bg-slate-900/70 px-2 py-1 backdrop-blur">
        当前视野宽度 ≈ {formatKm(viewportWidthKm(cameraDistanceR, FOV))}
      </div>
      {cutaway && (
        <div className="rounded bg-slate-900/70 px-2 py-1 backdrop-blur">
          剖面截面按 PREM 密度着色（1–13.5 g/cm³，viridis 色标）· 拖动旋转 · 右键平移 · 滚轮缩放
        </div>
      )}
    </div>
  );
}

export function App() {
  const cutaway = useEarth((s) => s.cutaway);
  const setCutaway = useEarth((s) => s.setCutaway);
  const showLabels = useEarth((s) => s.showLabels);
  const toggleLabels = useEarth((s) => s.toggleLabels);
  const flyTo = useEarth((s) => s.flyTo);
  const spinScale = useEarth((s) => s.spinScale);
  const setSpinScale = useEarth((s) => s.setSpinScale);

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
          <button
            onClick={() => setCutaway(!cutaway)}
            className={`rounded-md px-2.5 py-1.5 font-medium transition-colors ${
              cutaway
                ? "bg-sky-600 text-white"
                : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
            }`}
          >
            四分之一剖面
          </button>
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
          <span className="mx-1 text-slate-300">|</span>
          <button
            onClick={() => flyTo({ target: [0, 0, 0], distance: 3.4 })}
            className="rounded-md bg-white px-2.5 py-1.5 font-medium text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
          >
            全貌
          </button>
          <button
            onClick={() => flyTo({ target: ATMOS_FOCUS_TARGET, distance: 0.5 })}
            className="rounded-md bg-white px-2.5 py-1.5 font-medium text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
          >
            贴近大气层
          </button>
        </div>
      </header>
      <main className="flex min-h-0 flex-1">
        <div className="relative min-w-0 flex-1 bg-[#0b1020]">
          <EarthCanvas>
            <EarthScene />
          </EarthCanvas>
          <ScaleHud />
        </div>
        <aside className="w-[340px] shrink-0 space-y-3 overflow-y-auto border-l border-slate-200 bg-slate-50 p-3">
          <LayerDetail />
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

