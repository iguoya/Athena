import { useState } from "react";
import { invoke } from "./api";
import { Tex } from "./math";
import { SourceBadge } from "./ui";
import type { Answer, ExerciseBlock, RetrievalBlock, SourceRef } from "./types";

type Judge = { ok: boolean; detail: string };

function judge(answer: Answer, pick: number | string): Judge {
  if (answer.type === "choice") {
    const ok = pick === answer.correct;
    return {
      ok,
      detail: ok ? "答对了。" : "不对，再看一遍解析。",
    };
  }
  const value = Number(pick);
  const tol = answer.tolerance ?? 1e-6;
  const ok = Number.isFinite(value) && Math.abs(value - answer.value) <= tol;
  return {
    ok,
    detail: ok ? `答对了。` : `不对。你算的是 ${pick}，再核一遍过程。`,
  };
}

async function savePick(key: string, pick: number | string, ok: boolean) {
  await invoke("save_quiz_picks", {
    quizKey: key,
    picks: JSON.stringify({ pick, ok, at: Date.now() }),
  }).catch(() => {});
}

export function Exercise({
  block,
  onAnswered,
  retrieval = false,
}: {
  block: ExerciseBlock | RetrievalBlock;
  onAnswered: (ids: string[], correct: boolean) => void;
  retrieval?: boolean;
}) {
  const answer: Answer =
    block.kind === "exercise"
      ? block.answer
      : { type: "choice", options: block.options, correct: block.correct };
  const knowledge = block.kind === "exercise" ? block.knowledge : (block.knowledge ?? []);
  const solution = block.kind === "exercise" ? block.solution : block.explain;
  const refs: SourceRef[] = block.source_refs;

  const [pick, setPick] = useState<number | string | null>(null);
  const [result, setResult] = useState<Judge | null>(null);
  const [recorded, setRecorded] = useState(false);

  function submit(value: number | string) {
    setPick(value);
    const j = judge(answer, value);
    setResult(j);
    if (!recorded) {
      setRecorded(true);
      void savePick(block.id, value, j.ok);
      // 节首预测题（retrieval）只记录作答、不写掌握度：预测错只是直觉偏差，
      // 不是没学会——掌握度只由学后的练习作答写入（ADR 0052）。
      if (!retrieval) onAnswered(knowledge, j.ok);
    } else {
      void savePick(block.id, value, j.ok);
    }
  }

  function retry() {
    setPick(null);
    setResult(null);
  }

  const answered = result !== null;

  return (
    <div className={`exercise ${retrieval ? "retrieval" : ""}`}>
      {retrieval && <div className="tag">先答这一题，再看本节</div>}
      <div className="stem">
        <Tex text={retrieval ? (block as RetrievalBlock).prompt : (block as ExerciseBlock).stem} />
      </div>
      {answer.type === "choice" ? (
        <div className="options">
          {answer.options.map((opt, i) => (
            <button
              key={i}
              className={`option ${pick === i ? (answered ? (result!.ok ? "ok" : "bad") : "picked") : ""}`}
              disabled={answered}
              onClick={() => submit(i)}
            >
              <span className="letter">{String.fromCharCode(65 + i)}</span>
              <Tex text={opt} />
            </button>
          ))}
        </div>
      ) : (
        <form
          className="numeric"
          onSubmit={(e) => {
            e.preventDefault();
            const input = new FormData(e.currentTarget).get("value");
            if (input !== null && input !== "") submit(String(input));
          }}
        >
          <input
            name="value"
            type="text"
            inputMode="decimal"
            placeholder="算出结果后填在这里"
            disabled={answered}
          />
          <button type="submit" disabled={answered}>
            提交
          </button>
        </form>
      )}
      {answered && (
        <div className={`verdict ${result!.ok ? "ok" : "bad"}`}>
          <p>{result!.detail}</p>
          <div className="solution">
            <Tex text={solution} />
          </div>
          <SourceBadge refs={refs} />
          {!retrieval && (
            <button className="retry" onClick={retry}>
              重做一遍（进度只记第一次）
            </button>
          )}
        </div>
      )}
    </div>
  );
}
