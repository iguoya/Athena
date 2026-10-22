import { useState } from "react";
import { Inline } from "./Inline";
import { answerMatches, candidates } from "./answer";
import type { Check, Task } from "./types";

/** 题面与参考：空行分段，``` 围栏是代码块。 */
export function Rich({ text }: { text: string }) {
  const parts = text.split(/```[a-z]*\n([\s\S]*?)```/g);
  return (
    <>
      {parts.map((p, i) =>
        i % 2 === 1 ? (
          <pre key={i} className="code">{p.replace(/\n$/, "")}</pre>
        ) : (
          p.split(/\n{2,}/).filter((q) => q.trim()).map((q, j) => <p key={`${i}.${j}`} className="para"><Inline text={q.trim()} /></p>)
        ),
      )}
    </>
  );
}

/** 逐行比对输出：忽略行尾空白与首尾空行，Windows 与 Unix 的换行不算差异。 */
export function outputMatches(got: string, want: string): boolean {
  const norm = (s: string) => s.replace(/\r\n/g, "\n").split("\n").map((l) => l.replace(/\s+$/, "")).join("\n").replace(/^\n+|\n+$/g, "");
  return norm(got) === norm(want);
}

const KIND_ZH: Record<Task["kind"], string> = {
  predict: "先预测", selfexplain: "自我解释", quick: "速答", doit: "你来做",
};

/** 一个任务卡：机器判分的任务作答时回调 onAnswer(是否答对)（写进作答记录）；使用者点「继续」回调 onContinue。 */
export function TaskCard({ task, onAnswer, onContinue, onSkip }: { task: Task; onAnswer: (correct: boolean) => void; onContinue: () => void; onSkip?: () => void }) {
  const [text, setText] = useState("");
  const [shown, setShown] = useState(false);
  const [verdict, setVerdict] = useState<null | { ok: boolean; note?: string }>(null);
  const [pick, setPick] = useState<number | null>(null);

  const grade = (check: Check, input: string): { ok: boolean; note?: string } | null => {
    if (check.kind === "numbers") {
      if (candidates(input).length === 0) return { ok: false, note: "没有认出答案。可以写整数、小数、分数（如 3/4），多个数用逗号隔开。" };
      const ok = answerMatches(input, check.answer);
      return { ok, note: ok ? undefined : check.hint };
    }
    if (check.kind === "output") {
      const ok = outputMatches(input, check.expected);
      return { ok, note: ok ? undefined : check.hint };
    }
    return null;
  };

  return (
    <article className={`task task-${task.kind}`}>
      <header><span className="task-kind">{KIND_ZH[task.kind]}</span>{task.kind === "quick" || task.kind === "doit" ? <span className="task-graded">进掌握度</span> : task.kind === "predict" ? <span className="task-ungraded">记命中，不进复习</span> : <span className="task-ungraded">不判分</span>}{onSkip && <button className="link skip" onClick={onSkip}>跳过这个暂停点</button>}</header>

      {task.kind === "selfexplain" && (
        <>
          <Rich text={task.prompt} />
          <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="先写下你的想法，再看对照" rows={3} />
          {!shown ? (
            <button className="primary" disabled={!text.trim()} onClick={() => setShown(true)}>看对照</button>
          ) : (
            <>
              <div className="reveal"><Rich text={task.reference} /></div>
              <button className="primary" onClick={onContinue}>继续</button>
            </>
          )}
        </>
      )}

      {(task.kind === "predict" || task.kind === "quick" || task.kind === "doit") && (
        <>
          <Rich text={task.kind === "predict" ? task.prompt : task.stem} />
          {task.kind === "doit" && (
            <>
              <p className="para muted">骨架代码（不改也能编译运行，改了再跑，把输出贴回来）：</p>
              <pre className="code">{task.skeleton}</pre>
            </>
          )}
          {task.check.kind === "choice" ? (
            <div className="check choice">
              {task.check.options.map((o, i) => (
                <button key={i} className={pick === i ? (o.ok ? "ok" : "bad") : ""} disabled={verdict !== null}
                  onClick={() => { setPick(i); setVerdict({ ok: !!o.ok, note: o.why }); onAnswer(!!o.ok); }}>
                  <Inline text={o.text} />
                </button>
              ))}
            </div>
          ) : (
            <div className="check">
              <label>
                <Inline text={task.check.ask} />
                {task.check.kind === "output" ? (
                  <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4} placeholder="把程序的输出贴在这里" />
                ) : (
                  <input value={text} onChange={(e) => setText(e.target.value)} placeholder="例如 1, -2 或 3/4" />
                )}
              </label>
              <button className="primary" disabled={verdict?.ok === true} onClick={() => { const v = grade(task.check, text); if (!v) return; setVerdict(v); if (!v.note?.startsWith("没有认出")) onAnswer(v.ok); }}>核对</button>
            </div>
          )}
          {verdict && (
            <p className={verdict.ok ? "verdict ok" : "verdict bad"}>
              {verdict.ok ? "对了。" : "还不对。"}{verdict.note && <> <Inline text={verdict.note} /></>}
            </p>
          )}
          {verdict && (
            <div className="sol-wrap">
              <button className="link" onClick={() => setShown((v) => !v)}>{shown ? "收起参考解答" : "查看参考解答"}</button>
              {shown && <div className="sol"><Rich text={task.kind === "predict" ? task.reveal : task.sol} /></div>}
            </div>
          )}
          {verdict && <button className="primary" onClick={onContinue}>继续</button>}
        </>
      )}
    </article>
  );
}
