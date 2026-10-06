import { motion } from "motion/react";
import {
  Check,
  FlaskConical,
  Info,
  Lightbulb,
  MonitorPlay,
  TriangleAlert,
  X,
} from "lucide-react";
import type { Block, ExperimentEntity, ManifestEntity, QuizItem } from "./types";
import { SimulationView } from "./simulations";

interface BlockViewProps {
  block: Block;
  demos: Map<string, ManifestEntity>;
  experiments: Map<string, ExperimentEntity>;
  onLaunch: (demoId: string) => void;
  onAnswer: (itemId: string, correct: boolean) => void;
  scopeId: string;
}

function QuizView({
  item,
  onAnswer,
  itemId,
}: {
  item: QuizItem;
  itemId: string;
  onAnswer: (itemId: string, correct: boolean) => void;
}) {
  const answered = window.localStorage.getItem(`answer:${itemId}`);
  const reveal = answered != null;
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="my-5 rounded-card bg-surface p-5 shadow-card ring-1 ring-line"
    >
      <p className="mb-4 font-medium text-fg">{item.stem}</p>
      <div className="flex flex-col gap-2.5">
        {item.options.map((option, index) => {
          const isAnswer = index === item.answer;
          const chosen = answered === String(index);
          return (
            <motion.button
              key={index}
              whileHover={reveal ? undefined : { x: 4 }}
              whileTap={reveal ? undefined : { scale: 0.98 }}
              disabled={reveal}
              onClick={() => {
                window.localStorage.setItem(`answer:${itemId}`, String(index));
                onAnswer(itemId, isAnswer);
              }}
              className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors ${
                reveal
                  ? isAnswer
                    ? "border-accent-deep/50 bg-accent-soft text-fg"
                    : chosen
                      ? "border-red-300 bg-red-50 text-fg/70"
                      : "border-line text-muted"
                  : "border-line bg-surface-2 hover:border-accent/40 hover:bg-accent-soft"
              }`}
            >
              <span
                className={`grid size-6 shrink-0 place-items-center rounded-full text-xs font-semibold ${
                  reveal && isAnswer
                    ? "bg-accent-deep text-white"
                    : reveal && chosen
                      ? "bg-red-400 text-white"
                      : "bg-surface-2 text-muted ring-1 ring-line"
                }`}
              >
                {reveal && isAnswer ? (
                  <Check className="size-3.5" />
                ) : reveal && chosen ? (
                  <X className="size-3.5" />
                ) : (
                  String.fromCharCode(65 + index)
                )}
              </span>
              <span className="flex-1">{option}</span>
              {reveal && isAnswer && (
                <span className="text-xs font-medium text-accent-deep">正确答案</span>
              )}
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
}

export function BlockView(props: BlockViewProps) {
  const { block, demos, experiments, onLaunch, onAnswer, scopeId } = props;
  switch (block.type) {
    case "text":
      return <p className="my-4 leading-loose text-fg/90">{block.text}</p>;
    case "code":
      return (
        <motion.figure
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          className="my-5"
        >
          <div className="overflow-hidden rounded-card shadow-card ring-1 ring-line">
            <div className="flex items-center bg-bg-2 px-4 py-1.5 ring-1 ring-line">
              <span className="font-mono text-xs font-medium text-accent">{block.lang}</span>
            </div>
            <pre className="overflow-x-auto bg-[#F6F6F6] p-4 font-mono text-[15px] leading-relaxed text-[#555555] ring-1 ring-line">
              <code>{block.source}</code>
            </pre>
          </div>
          {block.caption && (
            <figcaption className="mt-2 text-xs text-muted">{block.caption}</figcaption>
          )}
        </motion.figure>
      );
    case "callout": {
      const style =
        block.variant === "warning"
          ? { ring: "ring-amber-500/30", bg: "bg-amber-500/10", fg: "text-amber-700", Icon: TriangleAlert }
          : block.variant === "tip"
            ? { ring: "ring-accent/30", bg: "bg-link/10", fg: "text-link", Icon: Lightbulb }
            : { ring: "ring-accent/25", bg: "bg-accent-soft", fg: "text-accent", Icon: Info };
      return (
        <aside className={`my-5 flex gap-3 rounded-card p-4 text-sm ring-1 ${style.ring} ${style.bg}`}>
          <style.Icon className={`mt-0.5 size-4.5 shrink-0 ${style.fg}`} />
          <p className="leading-relaxed text-fg/90">{block.text}</p>
        </aside>
      );
    }
    case "simulation":
      return (
        <SimulationView
          sim={block.sim}
          demoRef={block.demo_ref}
          note={block.note}
          onLaunch={onLaunch}
        />
      );
    case "demo": {
      const entity = demos.get(block.demo_ref) ?? experiments.get(block.demo_ref);
      return (
        <motion.div
          whileHover={{ y: -2 }}
          className="my-5 rounded-card bg-surface p-5 shadow-card ring-1 ring-accent/25"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="flex items-center gap-2 font-medium text-accent">
                <MonitorPlay className="size-4" /> 真机演示 · {entity?.title ?? block.demo_ref}
              </p>
              <p className="mt-1.5 text-sm leading-relaxed text-fg/80">
                {entity?.purpose ?? block.caption}
              </p>
            </div>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => onLaunch(block.demo_ref)}
              className="shrink-0 rounded-xl bg-accent px-4 py-2.5 text-sm font-medium text-on-accent shadow-card transition-colors hover:bg-accent/90"
            >
              运行演示
            </motion.button>
          </div>
        </motion.div>
      );
    }
    case "experiment": {
      const entity = experiments.get(block.demo_ref);
      return (
        <motion.div
          whileHover={{ y: -2 }}
          className="my-5 rounded-card bg-surface p-5 shadow-card ring-1 ring-accent-deep/40"
        >
          <p className="flex items-center gap-2 font-medium text-accent-deep">
            <FlaskConical className="size-4" /> 骨架实验 · {entity?.title ?? block.demo_ref}
          </p>
          <p className="mt-1.5 text-sm leading-relaxed text-fg/80">{entity?.purpose}</p>
          {entity?.acceptance && (
            <p className="mt-2 text-xs text-muted">
              <span className="font-medium text-fg/70">跑通标准：</span>
              {entity.acceptance}
            </p>
          )}
          <p className="mt-2 font-mono text-xs text-muted">{entity?.skeleton_dir}</p>
        </motion.div>
      );
    }
    case "observation_quiz":
    case "quiz":
      return (
        <QuizView
          item={block}
          itemId={`${scopeId}:${block.id ?? block.stem.slice(0, 12)}`}
          onAnswer={onAnswer}
        />
      );
  }
}
