// 并入 guide/gtkmm/src/simulations.tsx：放在 SignalOrderSim 旁边。
// MachineButton、SimulationProps 沿用该文件已有定义。
// SimulationView 增加：case "box-layout": return <BoxLayoutSim {...props} />;
// 只粘贴本函数。useState、MonitorPlay 该文件已经引入，不要再加 import。

type BoxPrediction = "to-b" | "to-a" | "all" | "none";

const BOX_PREDICTIONS: { id: BoxPrediction; label: string }[] = [
  { id: "to-b", label: "多余宽度都归乙" },
  { id: "to-a", label: "多余宽度都归甲" },
  { id: "all", label: "甲乙丙一起变宽" },
  { id: "none", label: "三个宽度都不变" },
];

const BOX_NATURAL = 48;

function boxSlots(width: number, expand: boolean[], spacing: number): number[] {
  const extra = width - BOX_NATURAL * expand.length - spacing * (expand.length - 1);
  const sizes = expand.map(() => BOX_NATURAL);
  const expanding = expand.filter(Boolean).length;
  if (extra <= 0 || expanding === 0) return sizes;
  const share = Math.floor(extra / expanding);
  let remainder = extra - share * expanding;
  return sizes.map((size, index) => {
    if (!expand[index]) return size;
    const next = size + share + (remainder > 0 ? 1 : 0);
    if (remainder > 0) remainder -= 1;
    return next;
  });
}

/**
 * 水平 Box 的宽度分配。先预测「只让乙 hexpand、不居中」时多余宽度归谁，
 * 再打开滑块看另外两种情况。外框用 flex 的固定底宽加增长近似，不是 GTK 测量。
 */
function BoxLayoutSim({ demoRef, note, onLaunch }: SimulationProps) {
  const [prediction, setPrediction] = useState<BoxPrediction | null>(null);
  const [ran, setRan] = useState(false);
  const [needPick, setNeedPick] = useState(false);
  const [width, setWidth] = useState(220);
  const [aExpand, setAExpand] = useState(false);
  const [bExpand, setBExpand] = useState(true);
  const [center, setCenter] = useState(false);
  const [gap, setGap] = useState(false);

  const spacing = gap ? 16 : 0;
  const slots = boxSlots(width, [aExpand, bExpand, false], spacing);
  const correct = prediction === "to-b";
  const names = ["甲", "乙", "丙"];

  return (
    <figure className="my-6 rounded-card bg-surface p-6 shadow-card ring-1 ring-line">
      <figcaption className="mb-4 text-[20px] font-semibold tracking-wide text-muted">
        交互模拟 · 水平 Box 的多余宽度分给谁
      </figcaption>
      <p className="mb-4 text-[20px] leading-relaxed text-fg/80">
        甲、乙、丙排在一个水平 Box 里。只打开乙的 hexpand，对齐保持填满。窗口变宽后，多余的宽度归谁？先选再运行。
      </p>
      <div className="mb-5 flex flex-wrap gap-2">
        {BOX_PREDICTIONS.map((item) => (
          <button
            key={item.id}
            type="button"
            disabled={ran}
            onClick={() => {
              setPrediction(item.id);
              setNeedPick(false);
            }}
            className={`rounded-xl border px-4 py-2 text-[20px] ${
              prediction === item.id
                ? "border-accent bg-accent-soft text-accent"
                : "border-line bg-surface-2 text-fg/80"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>
      {ran && (
        <div className="overflow-x-auto">
          <div
            className="flex items-stretch rounded-xl bg-surface-2 py-2 transition-all duration-500"
            style={{ width }}
          >
            {slots.map((slot, index) => {
              const centered = index === 1 && center && bExpand;
              const buttonWidth = centered ? BOX_NATURAL : slot;
              return (
                <div
                  key={names[index]}
                  className={`flex items-center justify-center ${
                    centered ? "rounded-lg border border-dashed border-accent/50" : ""
                  }`}
                  style={{ width: slot, marginLeft: index === 0 ? 0 : spacing }}
                >
                  <div
                    className="rounded-lg bg-accent py-2 text-center text-on-accent"
                    style={{ width: buttonWidth }}
                  >
                    <p className="text-[20px] font-medium">{names[index]}</p>
                    <p className="text-[18px]">外框 {buttonWidth}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <MachineButton
          onClick={() => {
            if (!prediction) {
              setNeedPick(true);
              return;
            }
            setNeedPick(false);
            setAExpand(false);
            setBExpand(true);
            setCenter(false);
            setGap(false);
            setWidth(220);
            setRan(true);
            window.setTimeout(() => setWidth(460), 40);
          }}
        >
          运行
        </MachineButton>
        {ran && (
          <MachineButton
            variant="outline"
            onClick={() => {
              setRan(false);
              setPrediction(null);
              setWidth(220);
            }}
          >
            再预测一次
          </MachineButton>
        )}
        {demoRef && onLaunch && (
          <MachineButton variant="outline" onClick={() => onLaunch(demoRef)}>
            <MonitorPlay className="size-6" /> 在真机上看
          </MachineButton>
        )}
      </div>
      {needPick && (
        <p className="mt-4 text-[20px] font-medium text-accent">先选一个预测，再点运行。</p>
      )}
      {ran && (
        <p className={`mt-4 text-[20px] font-medium ${correct ? "text-accent" : "text-red-700"}`}>
          {correct
            ? "预测正确：只有乙 hexpand，多余宽度都进乙的那一档。"
            : "预测不对。只有乙会扩展，多余宽度都归乙；甲和丙停在自然宽度。"}
        </p>
      )}
      {ran && (
        <div className="mt-4 flex flex-col gap-3 text-[20px] text-fg/80">
          <label className="flex items-center gap-3">
            模型窗口宽 {width}
            <input
              type="range"
              min={200}
              max={560}
              value={width}
              onChange={(event) => setWidth(Number(event.target.value))}
            />
          </label>
          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={aExpand} onChange={(event) => setAExpand(event.target.checked)} />
              甲 hexpand
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={bExpand} onChange={(event) => setBExpand(event.target.checked)} />
              乙 hexpand
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={center} onChange={(event) => setCenter(event.target.checked)} />
              乙居中
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={gap} onChange={(event) => setGap(event.target.checked)} />
              间距 16
            </label>
          </div>
        </div>
      )}
      <p className="mt-4 text-[20px] leading-relaxed text-muted">
        {note ??
          "模型简化：外框按固定自然宽度加 flex 增长来画，不模拟主题内边距，也不模拟最小宽度。乙居中时虚线是占位、实心块才是按钮。真机标签的 a、b、c 是 get_width()，比外框少一圈内边距，谁变宽与这里一致。"}
      </p>
    </figure>
  );
}
