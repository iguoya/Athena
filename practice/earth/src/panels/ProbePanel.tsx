import {
  atmosphereLayerAtHeight,
  data,
  densityAt,
  interiorLayerAtDepth,
  interiorTempAt,
  ussaPressureAt,
  ussaTempAt,
  USSA_MAX_HEIGHT_KM,
} from "../content/load";
import { useEarth } from "../state/store";

/** 径向探针：滑杆沿剖面移动，3D 里的黄点与两张图表的虚线同步。 */
export function ProbePanel() {
  const probeMode = useEarth((s) => s.probeMode);
  const probeKm = useEarth((s) => s.probeKm);
  const setProbeMode = useEarth((s) => s.setProbeMode);
  const setProbeKm = useEarth((s) => s.setProbeKm);
  const select = useEarth((s) => s.select);

  const interior = probeMode === "interior";
  const layer = interior
    ? interiorLayerAtDepth(probeKm)
    : atmosphereLayerAtHeight(probeKm);

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50/60 p-3">
      <div className="mb-2 flex items-center gap-1">
        {(["interior", "atmosphere"] as const).map((mode) => (
          <button
            key={mode}
            onClick={() => setProbeMode(mode)}
            className={`rounded-md px-2 py-1 text-xs font-medium transition-colors ${
              probeMode === mode
                ? "bg-amber-600 text-white"
                : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
            }`}
          >
            {mode === "interior" ? "向内（深度）" : "向上（高度）"}
          </button>
        ))}
      </div>
      <input
        type="range"
        min={0}
        max={interior ? Math.round(data.shape.meanRadiusKm) : 1000}
        step={1}
        value={probeKm}
        onChange={(event) => setProbeKm(Number(event.target.value))}
        className="w-full accent-amber-600"
        aria-label={interior ? "探针深度" : "探针高度"}
      />
      <div className="mt-1.5 grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-slate-600">
        <span className="font-semibold text-slate-800 tabular-nums">
          {interior ? `深度 ${probeKm.toLocaleString()} km` : `高度 ${probeKm.toLocaleString()} km`}
        </span>
        <button
          onClick={() => layer && select(layer.id)}
          className="justify-self-end text-right font-medium text-sky-700 hover:underline"
        >
          {layer?.name ?? (interior ? "—" : "行星际空间")}
        </button>
        {interior ? (
          <>
            <span>
              密度 <b className="tabular-nums">{densityAt(probeKm).toFixed(2)}</b> g/cm³（PREM）
            </span>
            <span>
              温度 ≈{" "}
              <b className="tabular-nums">{Math.round(interiorTempAt(probeKm)).toLocaleString()}</b>{" "}
              °C
              <span className="text-slate-400">（示意）</span>
            </span>
          </>
        ) : (
          <>
            <span>
              {probeKm <= USSA_MAX_HEIGHT_KM ? (
                <>
                  温度{" "}
                  <b className="tabular-nums">{ussaTempAt(probeKm).toFixed(1)}</b> °C（USSA1976）
                </>
              ) : (
                <span className="text-slate-400">86 km 以上无标准模型</span>
              )}
            </span>
            <span>
              {probeKm <= USSA_MAX_HEIGHT_KM ? (
                <>
                  气压 <b className="tabular-nums">{ussaPressureAt(probeKm).toFixed(3)}</b> hPa
                </>
              ) : (
                <span className="text-slate-400">参考值见热层描述</span>
              )}
            </span>
          </>
        )}
      </div>
    </div>
  );
}
