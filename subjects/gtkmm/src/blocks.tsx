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
  return (
    <div className="my-4 rounded-lg border border-stone-300 bg-stone-50 p-4">
      <p className="mb-3 text-stone-800">{item.stem}</p>
      <div className="flex flex-col gap-2">
        {item.options.map((option, index) => {
          const isAnswer = index === item.answer;
          const chosen = answered === String(index);
          const reveal = answered != null;
          return (
            <button
              key={index}
              disabled={reveal}
              onClick={() => {
                window.localStorage.setItem(`answer:${itemId}`, String(index));
                onAnswer(itemId, isAnswer);
              }}
              className={`rounded-md border px-3 py-2 text-left transition-colors ${
                reveal
                  ? isAnswer
                    ? "border-green-600 bg-green-50 text-green-900"
                    : chosen
                      ? "border-red-400 bg-red-50 text-red-900"
                      : "border-stone-200 text-stone-500"
                  : "border-stone-300 bg-white hover:border-blue-500 hover:bg-blue-50"
              }`}
            >
              {option}
              {reveal && isAnswer && <span className="ml-2 text-xs">✓ 正确答案</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function BlockView(props: BlockViewProps) {
  const { block, demos, experiments, onLaunch, onAnswer, scopeId } = props;
  switch (block.type) {
    case "text":
      return <p className="my-3 leading-relaxed text-stone-800">{block.text}</p>;
    case "code":
      return (
        <figure className="my-4">
          <pre className="overflow-x-auto rounded-lg bg-stone-900 p-4 text-sm leading-relaxed text-stone-100">
            <code>{block.source}</code>
          </pre>
          {block.caption && (
            <figcaption className="mt-1 text-xs text-stone-500">{block.caption}</figcaption>
          )}
        </figure>
      );
    case "callout":
      return (
        <aside
          className={`my-4 rounded-lg border-l-4 p-4 text-sm ${
            block.variant === "warning"
              ? "border-amber-500 bg-amber-50 text-amber-900"
              : block.variant === "tip"
                ? "border-green-600 bg-green-50 text-green-900"
                : "border-blue-500 bg-blue-50 text-blue-900"
          }`}
        >
          {block.text}
        </aside>
      );
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
        <div className="my-4 rounded-lg border border-blue-200 bg-blue-50/60 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-medium text-blue-900">
                真机演示 · {entity?.title ?? block.demo_ref}
              </p>
              <p className="mt-1 text-sm text-stone-700">{entity?.purpose ?? block.caption}</p>
            </div>
            <button
              onClick={() => onLaunch(block.demo_ref)}
              className="shrink-0 rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              运行演示
            </button>
          </div>
        </div>
      );
    }
    case "experiment": {
      const entity = experiments.get(block.demo_ref);
      return (
        <div className="my-4 rounded-lg border border-orange-300 bg-orange-50 p-4">
          <p className="font-medium text-orange-900">
            骨架实验 · {entity?.title ?? block.demo_ref}
          </p>
          <p className="mt-1 text-sm text-stone-700">{entity?.purpose}</p>
          {entity?.acceptance && (
            <p className="mt-2 text-xs text-stone-600">
              跑通标准：{entity.acceptance}
            </p>
          )}
          <p className="mt-2 font-mono text-xs text-stone-500">
            骨架：{entity?.skeleton_dir}（只读；复制到工作区后修改，可一键重置）
          </p>
        </div>
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
