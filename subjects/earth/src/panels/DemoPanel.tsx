import { useState } from "react";
import { ballisticPath, demoSeconds, routeDistanceKm, stageHeights } from "../content/demo";
import { data } from "../content/load";
import { useEarth } from "../state/store";

const formatMinutes = (seconds: number): string => {
  const minutes = seconds / 60;
  if (minutes < 60) return `${Math.round(minutes)} 分钟`;
  return `${(minutes / 60).toFixed(1)} 小时`;
};

/** 飞行演示：民航/战斗机沿大圆航线飞行，东风系列画教学示意弹道（数据口径见面板底部）。 */
export function DemoPanel() {
  const [kind, setKind] = useState<"air" | "ballistic">("air");
  const [aircraftId, setAircraftId] = useState(data.demos.aircraft[0].id);
  const [routeId, setRouteId] = useState(data.demos.routes[0].id);
  const [ballisticId, setBallisticId] = useState(data.demos.ballistics[0].id);
  const demo = useEarth((s) => s.demo);
  const playing = useEarth((s) => s.playing);
  const startDemo = useEarth((s) => s.startDemo);
  const stopDemo = useEarth((s) => s.stopDemo);
  const replay = useEarth((s) => s.replay);
  const togglePlay = useEarth((s) => s.togglePlay);
  const spinScale = useEarth((s) => s.spinScale);
  const demoScale = useEarth((s) => s.demoScale);
  const setDemoScale = useEarth((s) => s.setDemoScale);

  const route = data.demos.routes.find((r) => r.id === routeId)!;
  const craft = data.demos.aircraft.find((a) => a.id === aircraftId)!;
  const ballistic = data.demos.ballistics.find((b) => b.id === ballisticId)!;
  const airSeconds = demoSeconds("air", {
    routeKm: routeDistanceKm(route),
    speedKmh: craft.cruiseSpeedKmh,
  });
  const heights = stageHeights(
    ballisticPath(
      data.demos.launch,
      ballistic,
      ballistic.id === "df-17" ? "glide" : "arc",
    ),
  );
  const activeId = kind === "air" ? routeId : ballisticId;
  const active = demo?.kind === kind && demo.id === activeId;

  const start = () =>
    startDemo(kind === "air" ? { kind: "air", id: routeId } : { kind: "ballistic", id: ballisticId });

  return (
    <div className="rounded-lg border border-emerald-200 bg-emerald-50/60 p-3 text-sm">
      <div className="mb-2 flex items-center gap-1">
        {(["air", "ballistic"] as const).map((k) => (
          <button
            key={k}
            onClick={() => setKind(k)}
            className={`rounded-md px-2 py-1 text-xs font-medium transition-colors ${
              kind === k
                ? "bg-emerald-600 text-white"
                : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
            }`}
          >
            {k === "air" ? "民航 / 战斗机" : "弹道示意（东风系列）"}
          </button>
        ))}
      </div>

      {kind === "air" ? (
        <div className="space-y-1.5 text-xs text-slate-600">
          <label className="flex items-center gap-2">
            航线
            <select
              value={routeId}
              onChange={(event) => setRouteId(event.target.value)}
              className="flex-1 rounded border border-slate-200 bg-white px-1.5 py-1"
            >
              {data.demos.routes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2">
            机型
            <select
              value={aircraftId}
              onChange={(event) => setAircraftId(event.target.value)}
              className="flex-1 rounded border border-slate-200 bg-white px-1.5 py-1"
            >
              {data.demos.aircraft.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </label>
          <p className="leading-relaxed">
            巡航 <b>{craft.cruiseHeightKm} km</b> ·{" "}
            <b className="tabular-nums">{craft.cruiseSpeedKmh}</b> km/h · 大圆距离{" "}
            <b className="tabular-nums">{Math.round(routeDistanceKm(route))}</b> km · 真实用时约{" "}
            <b>{formatMinutes(airSeconds)}</b>（当前时钟 ×{spinScale}，模拟{" "}
            {airSeconds / spinScale < 1
              ? `${Math.round((airSeconds / spinScale) * 60)} 秒`
              : `${formatMinutes(airSeconds / spinScale)}`}
            ）
          </p>
          <p className="text-slate-500">{craft.note}</p>
        </div>
      ) : (
        <div className="space-y-1.5 text-xs text-slate-600">
          <label className="flex items-center gap-2">
            型号
            <select
              value={ballisticId}
              onChange={(event) => setBallisticId(event.target.value)}
              className="flex-1 rounded border border-slate-200 bg-white px-1.5 py-1"
            >
              {data.demos.ballistics.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </label>
          <p className="leading-relaxed">
            射程 <b className="tabular-nums">{ballistic.rangeKm.toLocaleString()}</b> km（公开报道
            估计）· 顶点 ≈ <b className="tabular-nums">{ballistic.apogeeKm}</b> km · 真实全程约{" "}
            <b>{ballistic.stageMinutes}</b> 分钟（×{demoScale} 下约{" "}
            {Math.max(1, Math.round((ballistic.stageMinutes * 60) / demoScale))} 秒）
          </p>
          <p className="leading-relaxed">
            射高（示意剖面）：<span className="text-red-500">助推</span> 0 → {heights.boostEndKm} km ·{" "}
            <span className="text-amber-500">中段</span> 顶点 ≈ {heights.apexKm} km
            {heights.apexKm > 100 ? "（太空）" : ""} ·{" "}
            <span className="text-purple-500">再入</span> {heights.reentryStartKm} km → 0
          </p>
          <div className="flex items-center gap-1">
            播放速度
            {[
              { scale: 6, label: "慢" },
              { scale: 15, label: "中" },
              { scale: 40, label: "快" },
            ].map((option) => (
              <button
                key={option.scale}
                onClick={() => setDemoScale(option.scale)}
                className={`rounded-md px-2 py-0.5 ${
                  demoScale === option.scale
                    ? "bg-emerald-600 text-white"
                    : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
          <p className="text-slate-500">{ballistic.note}</p>
        </div>
      )}

      <div className="mt-2 flex items-center gap-1.5">
        <button
          onClick={start}
          className="rounded-md bg-emerald-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-emerald-700"
        >
          {kind === "air" ? "起飞" : "发射"}
        </button>
        {demo && active && (
          <>
            <button
              onClick={replay}
              className="rounded-md bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
            >
              重播
            </button>
            <button
              onClick={togglePlay}
              className="rounded-md bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
            >
              {playing ? "暂停" : "继续"}
            </button>
            <button
              onClick={stopDemo}
              className="rounded-md bg-white px-2.5 py-1.5 text-xs font-medium text-slate-500 ring-1 ring-slate-200 hover:bg-slate-50"
            >
              清除
            </button>
          </>
        )}
        {demo && !active && (
          <span className="text-xs text-slate-400">已选其他演示，重新点起飞/发射可切换</span>
        )}
      </div>
      <p className="mt-2 text-[11px] leading-relaxed text-slate-400">
        {kind === "air" ? data.demos.airNote : data.demos.ballisticNote}
      </p>
    </div>
  );
}
