import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState } from "react";
import { Inline, renderMath } from "./Inline";
import { answerMatches, candidates } from "./answer";
import type { AttemptRow, Block, Check, Exercise, SectionData, Unit } from "./types";

export type ViewMode = "zh" | "both" | "en";

const ENV_ZH: Record<string, string> = {
  definition: "定义", theorem: "定理", proposition: "命题", lemma: "引理", corollary: "推论",
  example: "例", algorithm: "算法", procedure: "步骤", discussion: "讨论", problem: "问题",
  solution: "解", proof: "证明", proofof: "证明", outcome: "本节目标",
};

/** 一个可译单元：按视图模式显示译文 / 原文 / 对照；没有译文时显示原文并标「待译」。 */
function U({ u, mode }: { u: Unit; mode: ViewMode }) {
  const has = u.zh !== "";
  if (mode === "en" || (!has && mode === "zh")) {
    return (
      <span>
        <Inline text={u.en} />
        {!has && mode === "zh" && <span className="tag-todo">待译</span>}
      </span>
    );
  }
  if (mode === "both" && has) {
    return (
      <span>
        <Inline text={u.zh} />
        <span className="en-under"><Inline text={u.en} /></span>
      </span>
    );
  }
  return <Inline text={has ? u.zh : u.en} />;
}

/** 一幅 TikZ 图：svg 由 render_figures.py 预先编译进 content/figures/；没编好的显示占位。 */
function Fig({ id }: { id: string }) {
  const [svg, setSvg] = useState<string | null | undefined>(undefined);
  useEffect(() => {
    let alive = true;
    invoke<string | null>("get_figure", { figId: id }).then((v) => alive && setSvg(v)).catch(() => alive && setSvg(null));
    return () => { alive = false; };
  }, [id]);
  if (svg === undefined) return null;
  if (!svg) return <div className="figure-note">原书此处有一幅图，尚未移植。</div>;
  return <div className="figure-svg" dangerouslySetInnerHTML={{ __html: svg }} />;
}

function Blocks({ blocks, mode }: { blocks: Block[]; mode: ViewMode }) {
  return (
    <>
      {blocks.map((b, i) => (
        <BlockView key={i} b={b} mode={mode} />
      ))}
    </>
  );
}

function BlockView({ b, mode }: { b: Block; mode: ViewMode }) {
  switch (b.k) {
    case "p":
      return <p className="para"><U u={b.t} mode={mode} /></p>;
    case "heading":
      return <h3 className="sub-heading"><U u={b.t} mode={mode} /></h3>;
    case "math":
      return <div className="display-math" dangerouslySetInnerHTML={{ __html: renderMath(b.tex, true) }} />;
    case "box":
      return (
        <section className={`box box-${b.env}`}>
          <header>
            <span className="box-kind">{ENV_ZH[b.env] ?? b.env}</span>
            {b.title && <span className="box-title"><U u={b.title} mode={mode} /></span>}
          </header>
          <Blocks blocks={b.blocks} mode={mode} />
        </section>
      );
    case "solution":
    case "proof":
    case "proofof":
      return (
        <section className={`box box-${b.k}`}>
          <header>
            <span className="box-kind">{ENV_ZH[b.k]}</span>
            {b.title && <span className="box-title"><U u={b.title} mode={mode} /></span>}
          </header>
          <Blocks blocks={b.blocks} mode={mode} />
          <span className="qed">■</span>
        </section>
      );
    case "outcome":
      return (
        <section className="box box-outcome">
          <header><span className="box-kind">{ENV_ZH.outcome}</span></header>
          <Blocks blocks={b.blocks} mode={mode} />
        </section>
      );
    case "list": {
      const Tag = b.ordered ? "ol" : "ul";
      return (
        <Tag className={b.ordered ? "list-ord" : "list-bul"}>
          {b.items.map((it, i) => (
            <li key={i}><Blocks blocks={it} mode={mode} /></li>
          ))}
        </Tag>
      );
    }
    case "figure":
      return (
        <figure className="figure">
          {b.figs.length === 0 && <div className="figure-note">原书此处有一幅图，尚未移植。</div>}
          {b.figs.map((f) => <Fig key={f} id={f} />)}
          {b.caption && <figcaption><U u={b.caption} mode={mode} /></figcaption>}
        </figure>
      );
    case "table":
      return (
        <table className="book-table">
          <tbody>
            {b.rows.map((row, r) => (
              <tr key={r}>
                {row.map((c, i) => (
                  <td key={i}>{typeof c === "string" ? <Inline text={c} /> : <U u={c} mode={mode} />}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
  }
}

function ExerciseCard({
  ex, n, mode, check, sectionId, last, onAttempt,
}: {
  ex: Exercise; n: number; mode: ViewMode; check?: Check; sectionId: string;
  last?: AttemptRow; onAttempt: (itemId: string, correct: boolean) => void;
}) {
  const [input, setInput] = useState("");
  const [pick, setPick] = useState<number | null>(null);
  const [verdict, setVerdict] = useState<null | { ok: boolean; note?: string }>(null);
  const [showSol, setShowSol] = useState(false);
  const itemId = `${sectionId}.${ex.id}`;

  const submitNumbers = () => {
    if (check?.kind !== "numbers") return;
    if (candidates(input).length === 0) {
      // 没认出任何数：提示写法，不记作答（不是答错，是没读懂输入）
      setVerdict({ ok: false, note: "没有认出答案。可以写整数、小数、分数（如 3/4）、根号（sqrt(2)），多个数用逗号隔开。" });
      return;
    }
    const ok = answerMatches(input, check.answer);
    setVerdict({ ok, note: ok ? undefined : check.hint });
    onAttempt(itemId, ok);
  };
  const submitChoice = (i: number) => {
    if (check?.kind !== "choice") return;
    setPick(i);
    const o = check.options[i];
    setVerdict({ ok: !!o.ok, note: o.why });
    onAttempt(itemId, !!o.ok);
  };

  return (
    <article className="exercise" id={`ex-${ex.id}`}>
      <header>
        <span className="ex-n">习题 {n}</span>
        {last && <span className={last.correct ? "ex-state ok" : "ex-state bad"}>{last.correct ? "最近一次答对" : "最近一次答错"}</span>}
      </header>
      <Blocks blocks={ex.stem} mode={mode} />

      {check?.kind === "numbers" && (
        <div className="check">
          <label>
            <Inline text={check.ask} />
            <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && submitNumbers()} placeholder="先自己算，再填；例如 1, -2 或 3/4" />
          </label>
          <button onClick={submitNumbers}>核对</button>
        </div>
      )}
      {check?.kind === "choice" && (
        <div className="check choice">
          {check.options.map((o, i) => (
            <button key={i} className={pick === i ? (o.ok ? "ok" : "bad") : ""} onClick={() => submitChoice(i)}>
              <Inline text={o.text} />
            </button>
          ))}
        </div>
      )}
      {verdict && (
        <p className={verdict.ok ? "verdict ok" : "verdict bad"}>
          {verdict.ok ? "对了。" : "还不对。"}
          {verdict.note && <> <Inline text={verdict.note} /></>}
        </p>
      )}

      {ex.sol.length > 0 && (
        <div className="sol-wrap">
          <button className="link" onClick={() => setShowSol((v) => !v)}>
            {showSol ? "收起原书解答" : check ? "查看原书解答" : "先自己做，再看原书解答"}
          </button>
          {showSol && (
            <div className="sol">
              <Blocks blocks={ex.sol} mode={mode} />
            </div>
          )}
        </div>
      )}
    </article>
  );
}

export function SectionView({
  data, checks, mode, attempts, onAttempt,
}: {
  data: SectionData; checks: Record<string, Check> | null; mode: ViewMode;
  attempts: AttemptRow[]; onAttempt: (itemId: string, correct: boolean) => void;
}) {
  const lastBy = new Map<string, AttemptRow>();
  for (const a of attempts) if (a.knowledge_id === data.id) lastBy.set(a.item_id, a); // 已按 answered_at 升序，后者覆盖前者
  return (
    <div className="section-view">
      <h1>{data.title_zh}<small>{data.title_en}</small></h1>
      <Blocks blocks={data.blocks} mode={mode} />
      {data.exercises.length > 0 && (
        <div className="exercises">
          <h2>习题<small>原书 {data.exercises.length} 道</small></h2>
          {data.exercises.map((ex, i) => (
            <ExerciseCard
              key={ex.id} ex={ex} n={i + 1} mode={mode} check={checks?.[ex.id]}
              sectionId={data.id} last={lastBy.get(`${data.id}.${ex.id}`)} onAttempt={onAttempt}
            />
          ))}
        </div>
      )}
    </div>
  );
}
