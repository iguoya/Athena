// 并入 guide/gtkmm/src/simulations.tsx：放在 SignalFlowSim 旁边。
// Node、Arrow、MachineButton、SimulationProps 沿用该文件已有定义。
// SimulationView 增加：case "signal-order": return <SignalOrderSim {...props} />;
// 只粘贴本函数。useState、MonitorPlay 该文件已经引入，不要再加 import。

type Prediction = "ab" | "ba" | "only-a" | "together";

const PREDICTIONS: { id: Prediction; label: string }[] = [
  { id: "ab", label: "先 A，再 B" },
  { id: "ba", label: "先 B，再 A" },
  { id: "only-a", label: "只调用 A" },
  { id: "together", label: "A 与 B 同时" },
];

/**
 * 同一 clicked 上两个处理器的顺序。学习者先选预测，再点运行看 A → B。
 * 不画 GDK 分发与捕获，也不画窗口生命周期——那部分只在真机日志里。
 */
function SignalOrderSim({ demoRef, note, onLaunch }: SimulationProps) {
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [stage, setStage] = useState<"idle" | "click" | "a" | "b">("idle");
  const [ran, setRan] = useState(false);
  const [needPick, setNeedPick] = useState(false);

  const step = (next: typeof stage, delay: number) =>
    new Promise((resolve) => setTimeout(() => resolve(setStage(next)), delay));

  const correct = prediction === "ab";

  return (
    <figure className="my-6 rounded-card bg-surface p-6 shadow-card ring-1 ring-line">
      <figcaption className="mb-4 text-[20px] font-semibold tracking-wide text-muted">
        交互模拟 · 同一个 clicked，先调用谁
      </figcaption>
      <p className="mb-4 text-[20px] leading-relaxed text-fg/80">
        按钮的 signal_clicked() 上依次 connect 了处理器 A 和 B。先选你的预测，再运行。
      </p>
      <div className="mb-5 flex flex-wrap gap-2">
        {PREDICTIONS.map((item) => (
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
      <div className="flex flex-wrap items-center gap-2.5">
        <Node label="点击" sub="clicked 发出" active={stage !== "idle"} />
        <Arrow active={stage === "click" || stage === "a" || stage === "b"} />
        <Node label="处理器 A" sub="先 connect 的" active={stage === "a" || stage === "b"} />
        <Arrow active={stage === "a" || stage === "b"} />
        <Node label="处理器 B" sub="后 connect 的" active={stage === "b"} />
      </div>
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <MachineButton
          onClick={async () => {
            if (!prediction) {
              setNeedPick(true);
              return;
            }
            setNeedPick(false);
            setRan(true);
            setStage("click");
            await step("a", 450);
            await step("b", 450);
          }}
        >
          运行
        </MachineButton>
        {ran && (
          <MachineButton
            variant="outline"
            onClick={() => {
              setRan(false);
              setStage("idle");
              setPrediction(null);
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
      {ran && stage === "b" && (
        <p className={`mt-4 text-[20px] font-medium ${correct ? "text-accent" : "text-red-700"}`}>
          {correct
            ? "预测正确：普通 connect 按登记顺序调用，先 A 后 B。"
            : "预测不对。实际顺序是先 A 后 B：先 connect 的处理器先被调用。"}
        </p>
      )}
      <p className="mt-4 text-[20px] leading-relaxed text-muted">
        {note ??
          "模型简化：不画 GDK 事件分发和捕获阶段，也不画窗口的 show / map。真实顺序以真机日志为准。"}
      </p>
    </figure>
  );
}
