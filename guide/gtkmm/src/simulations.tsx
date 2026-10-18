import { useState } from "react";
import { motion } from "motion/react";
import { MonitorPlay } from "lucide-react";

interface SimulationProps {
  demoRef?: string;
  note?: string;
  onLaunch?: (demoId: string) => void;
}

function MachineButton({
  children,
  onClick,
  variant = "dark",
}: {
  children: React.ReactNode;
  onClick: () => void;
  variant?: "dark" | "outline";
}) {
  return (
    <motion.button
      whileHover={{ y: -1 }}
      whileTap={{ scale: 0.96 }}
      onClick={onClick}
      className={
        variant === "dark"
          ? "rounded-xl bg-accent px-4 py-2 text-[22px] font-medium text-on-accent shadow-card transition-colors hover:opacity-90"
          : "flex items-center gap-1.5 rounded-xl border border-accent/40 px-4 py-2 text-[22px] font-medium text-accent transition-colors hover:bg-accent-soft"
      }
    >
      {children}
    </motion.button>
  );
}

/**
 * 信号流模拟：页面上点按钮，依次点亮「部件 → clicked 信号 → 处理函数」，
 * 把 GTK 事件 dispatch 的因果顺序画出来。这是模型不是真实现——
 * 简化处由 note 标明，真相锚定在 demo_ref 指向的真机演示上（ADR 0001 决策 3）。
 */
function SignalFlowSim({ demoRef, note, onLaunch }: SimulationProps) {
  const [stage, setStage] = useState<"idle" | "emit" | "dispatch" | "handled">("idle");
  const [count, setCount] = useState(0);

  const step = (next: typeof stage, delay: number) =>
    new Promise((resolve) => setTimeout(() => resolve(setStage(next)), delay));

  return (
    <figure className="my-6 rounded-card bg-surface p-6 shadow-card ring-1 ring-line">
      <figcaption className="mb-4 text-[20px] font-semibold tracking-wide text-muted">
        交互模拟 · CLICKED 信号的旅程
      </figcaption>
      <div className="flex flex-wrap items-center gap-2.5">
        <Node label="Gtk::Button" sub="部件" active={stage !== "idle"} />
        <Arrow active={stage === "emit" || stage === "dispatch"} />
        <Node label="clicked" sub="信号发出" active={stage === "emit" || stage === "dispatch"} />
        <Arrow active={stage === "dispatch"} />
        <Node
          label="on_button_clicked()"
          sub="处理函数"
          active={stage === "handled"}
          detail={count > 0 ? `已调用 ${count} 次` : undefined}
        />
      </div>
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <MachineButton
          onClick={async () => {
            setStage("emit");
            await step("dispatch", 500);
            await step("handled", 500);
            setCount((c) => c + 1);
            await step("idle", 900);
          }}
        >
          模拟点击按钮
        </MachineButton>
        {demoRef && onLaunch && (
          <MachineButton variant="outline" onClick={() => onLaunch(demoRef)}>
            <MonitorPlay className="size-6" /> 在真机上看
          </MachineButton>
        )}
      </div>
      <p className="mt-4 text-[20px] leading-relaxed text-muted">
        {note ?? "模型简化：真实 GTK 由 GDK 事件分发到 main loop，此处省略事件队列与捕获阶段。"}
      </p>
    </figure>
  );
}

type Prediction = "ab" | "ba" | "only-a" | "together";

const PREDICTIONS: { id: Prediction; label: string }[] = [
  { id: "ab", label: "先 A，再 B" },
  { id: "ba", label: "先 B，再 A" },
  { id: "only-a", label: "只调用 A" },
  { id: "together", label: "A 与 B 同时" },
];

/**
 * 同一 clicked 上两个处理函数的顺序。学习者先选预测，再点运行看 A → B。
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
        按钮的 signal_clicked() 上依次 connect 了处理函数 A 和 B。先选你的预测，再运行。
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
        <Node label="处理函数 A" sub="先 connect 的" active={stage === "a" || stage === "b"} />
        <Arrow active={stage === "a" || stage === "b"} />
        <Node label="处理函数 B" sub="后 connect 的" active={stage === "b"} />
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
            : "预测不对。实际顺序是先 A 后 B：先 connect 的处理函数先被调用。"}
        </p>
      )}
      <p className="mt-4 text-[20px] leading-relaxed text-muted">
        {note ??
          "模型简化：不画 GDK 事件分发和捕获阶段，也不画窗口的 show / map。真实顺序以真机日志为准。"}
      </p>
    </figure>
  );
}

function ToggleStateSim({ demoRef, note, onLaunch }: SimulationProps) {
  const [active, setActive] = useState(false);
  const [signalLog, setSignalLog] = useState<string[]>([]);
  return (
    <figure className="my-6 rounded-card bg-surface p-6 shadow-card ring-1 ring-line">
      <figcaption className="mb-4 text-[20px] font-semibold tracking-wide text-muted">
        交互模拟 · TOGGLEBUTTON 的状态与 TOGGLED 信号
      </figcaption>
      <div className="flex items-center gap-5">
        <motion.button
          whileTap={{ scale: 0.94 }}
          onClick={() => {
            const next = !active;
            setActive(next);
            setSignalLog((log) => [`toggled（get_active() = ${next}）`, ...log].slice(0, 4));
          }}
          className={`rounded-full border-2 px-6 py-2.5 font-medium transition-colors ${
            active
              ? "border-accent bg-accent-soft text-accent"
              : "border-line bg-surface-2 text-muted"
          }`}
        >
          {active ? "按下（active）" : "弹起（inactive）"}
        </motion.button>
        <div className="flex-1">
          <div className="min-h-16 rounded-xl bg-[#F6F6F6] p-3 font-mono text-[20px] leading-relaxed ring-1 ring-line">
            {signalLog.map((line, index) => (
              <motion.p
                key={`${index}-${line}`}
                initial={{ opacity: 0, x: 8 }}
                animate={{ opacity: index === 0 ? 1 : 0.5, x: 0 }}
                className={index === 0 ? "text-accent font-medium" : "text-muted"}
              >
                signal: {line}
              </motion.p>
            ))}
            {signalLog.length === 0 && (
              <p className="text-muted">点击左侧按钮，信号日志出现在这里</p>
            )}
          </div>
        </div>
      </div>
      <div className="mt-5 flex items-center gap-3">
        {demoRef && onLaunch && (
          <MachineButton variant="outline" onClick={() => onLaunch(demoRef)}>
            <MonitorPlay className="size-6" /> 在真机上看
          </MachineButton>
        )}
      </div>
      <p className="mt-4 text-[20px] leading-relaxed text-muted">
        {note ?? "模型简化：真实切换由按下/释放完成，状态存于部件内部，get_active()/set_active() 读写它。"}
      </p>
    </figure>
  );
}

function Node({
  label,
  sub,
  active,
  detail,
}: {
  label: string;
  sub: string;
  active: boolean;
  detail?: string;
}) {
  return (
    <motion.div
      animate={
        active
          ? { scale: 1.04, boxShadow: "0 8px 24px -10px rgba(61, 111, 180, 0.45)" }
          : { scale: 1, boxShadow: "0 0 0 0 rgba(0,0,0,0)" }
      }
      transition={{ type: "spring", stiffness: 400, damping: 22 }}
      className={`rounded-xl border px-4 py-3 text-center ${
        active ? "border-accent bg-accent-soft" : "border-line bg-surface-2"
      }`}
    >
      <p className={`font-mono text-[22px] font-medium ${active ? "text-accent" : "text-fg/80"}`}>
        {label}
      </p>
      <p className="text-[20px] text-muted">{sub}</p>
      {detail && <p className="mt-1 text-[20px] font-medium text-accent">{detail}</p>}
    </motion.div>
  );
}

function Arrow({ active }: { active: boolean }) {
  return (
    <motion.span
      animate={{ color: active ? "#b02c29" : "#dddddd", scale: active ? 1.15 : 1 }}
      className="text-[30px] font-light"
    >
      →
    </motion.span>
  );
}

export function SimulationView(props: SimulationProps & { sim: string }) {
  switch (props.sim) {
    case "signal-flow":
      return <SignalFlowSim {...props} />;
    case "signal-order":
      return <SignalOrderSim {...props} />;
    case "toggle-state":
      return <ToggleStateSim {...props} />;
    default:
      return <p className="my-4 text-[22px] text-red-700">未知的模拟类型：{props.sim}</p>;
  }
}
