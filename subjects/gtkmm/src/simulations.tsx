import { useState } from "react";

interface SimulationProps {
  demoRef?: string;
  note?: string;
  onLaunch?: (demoId: string) => void;
}

type Stage = "idle" | "emit" | "dispatch" | "handled";

/**
 * 信号流模拟：页面上点按钮，依次点亮「控件 → clicked 信号 → 处理器」，
 * 把 GTK 事件 dispatch 的因果顺序画出来。这是模型不是真实现——
 * 简化处由 note 标明，真相锚定在 demo_ref 指向的真机演示上（ADR 0001 决策 3）。
 */
function SignalFlowSim({ demoRef, note, onLaunch }: SimulationProps) {
  const [stage, setStage] = useState<Stage>("idle");
  const [count, setCount] = useState(0);

  const step = (next: Stage, delay: number) =>
    new Promise((resolve) => setTimeout(() => resolve(setStage(next)), delay));

  return (
    <figure className="my-5 rounded-xl border border-stone-300 bg-white p-5">
      <figcaption className="mb-3 text-sm font-medium text-stone-500">
        交互模拟 · clicked 信号的旅程
      </figcaption>
      <div className="flex items-center gap-3">
        <Node label="Gtk::Button" sub="控件" active={stage !== "idle"} />
        <Arrow active={stage === "emit" || stage === "dispatch"} />
        <Node label="clicked" sub="信号发出" active={stage === "emit" || stage === "dispatch"} />
        <Arrow active={stage === "dispatch"} />
        <Node
          label="on_button_clicked()"
          sub="处理器"
          active={stage === "handled"}
          detail={count > 0 ? `已调用 ${count} 次` : undefined}
        />
      </div>
      <div className="mt-4 flex items-center gap-3">
        <button
          onClick={async () => {
            setStage("emit");
            await step("dispatch", 500);
            await step("handled", 500);
            setCount((c) => c + 1);
            await step("idle", 900);
          }}
          className="rounded-md bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700"
        >
          模拟点击按钮
        </button>
        {demoRef && onLaunch && (
          <button
            onClick={() => onLaunch(demoRef)}
            className="rounded-md border border-blue-500 px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50"
          >
            在真机上看 →
          </button>
        )}
      </div>
      <p className="mt-3 text-xs text-stone-500">
        {note ?? "模型简化：真实 GTK 由 GDK 事件分发到 main loop，此处省略事件队列与捕获阶段。"}
      </p>
    </figure>
  );
}

function ToggleStateSim({ demoRef, note, onLaunch }: SimulationProps) {
  const [active, setActive] = useState(false);
  const [signalLog, setSignalLog] = useState<string[]>([]);
  return (
    <figure className="my-5 rounded-xl border border-stone-300 bg-white p-5">
      <figcaption className="mb-3 text-sm font-medium text-stone-500">
        交互模拟 · ToggleButton 的状态与 toggled 信号
      </figcaption>
      <button
        onClick={() => {
          const next = !active;
          setActive(next);
          setSignalLog((log) => [`toggled（get_active() = ${next}）`, ...log].slice(0, 4));
        }}
        className={`rounded-full border-2 px-5 py-2 font-medium transition-colors ${
          active
            ? "border-green-600 bg-green-100 text-green-900"
            : "border-stone-400 bg-stone-100 text-stone-600"
        }`}
      >
        {active ? "按下（active）" : "弹起（inactive）"}
      </button>
      <ul className="mt-3 text-xs text-stone-600">
        {signalLog.map((line, index) => (
          <li key={index} className="font-mono">
            signal: {line}
          </li>
        ))}
      </ul>
      <div className="mt-3 flex items-center gap-3">
        {demoRef && onLaunch && (
          <button
            onClick={() => onLaunch(demoRef)}
            className="rounded-md border border-blue-500 px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50"
          >
            在真机上看 →
          </button>
        )}
      </div>
      <p className="mt-3 text-xs text-stone-500">
        {note ?? "模型简化：真实切换由鼠标按下/释放完成，状态存于控件内部，get_active()/set_active() 读写它。"}
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
    <div
      className={`rounded-lg border px-4 py-3 text-center transition-all ${
        active ? "border-blue-500 bg-blue-50 shadow-sm" : "border-stone-300 bg-stone-50"
      }`}
    >
      <p className="font-mono text-sm font-medium text-stone-800">{label}</p>
      <p className="text-xs text-stone-500">{sub}</p>
      {detail && <p className="mt-1 text-xs text-blue-700">{detail}</p>}
    </div>
  );
}

function Arrow({ active }: { active: boolean }) {
  return (
    <span className={`text-xl transition-colors ${active ? "text-blue-500" : "text-stone-300"}`}>
      →
    </span>
  );
}

export function SimulationView(props: SimulationProps & { sim: string }) {
  switch (props.sim) {
    case "signal-flow":
      return <SignalFlowSim {...props} />;
    case "toggle-state":
      return <ToggleStateSim {...props} />;
    default:
      return (
        <p className="my-4 text-sm text-red-700">未知的模拟类型：{props.sim}</p>
      );
  }
}
