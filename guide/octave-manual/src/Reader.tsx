import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState } from "react";
import { Inline, renderMath } from "./Inline";
import { answerMatches, candidates } from "./answer";
import type { AttemptRow, Block, Exercise, SectionData, Unit } from "./types";

export type ViewMode = "zh" | "both" | "en";

const ENV_ZH: Record<string, string> = {
  note: "注", warning: "警告", tip: "提示", seealso: "另见", versionadded: "新增", versionchanged: "变更",
  deprecated: "已弃用", important: "重要", attention: "注意", hint: "提示",
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

/** 一幅插图：svg 由 scripts/render_figures.py 预先渲染进 content/figures/；缺图时显示占位。 */
function Fig({ id }: { id: string }) {
  const [svg, setSvg] = useState<string | null | undefined>(undefined);
  useEffect(() => {
    let alive = true;
    invoke<string | null>("get_figure", { figId: id }).then((v) => alive && setSvg(v)).catch(() => alive && setSvg(null));
    return () => { alive = false; };
  }, [id]);
  if (svg === undefined) return null;
  if (!svg) return <div className="figure-note">手册此处有一幅图（{id}），尚未渲染。</div>;
  return <div className="figure-svg" dangerouslySetInnerHTML={{ __html: svg }} />;
}

/** 交互式会话（doctest）：`>>>`/`...` 开头的是输入，其余是工具的输出。逐字显示，不做语法高亮。 */
function CodeBlock({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <pre className="code">
      {lines.map((l, i) => (
        <span key={i} className={/^(>>>|\.\.\.)( |$)/.test(l) ? "code-in" : "code-out"}>{l + "\n"}</span>
      ))}
    </pre>
  );
}

/** 练习的中文题面与做法：空行分段，``` 围栏是代码块。 */
function Rich({ text }: { text: string }) {
  const parts = text.split(/```[a-z]*\n([\s\S]*?)```/g);
  return (
    <>
      {parts.map((p, i) =>
        i % 2 === 1 ? (
          <CodeBlock key={i} text={p.replace(/\n$/, "")} />
        ) : (
          p.split(/\n{2,}/).filter((q) => q.trim()).map((q, j) => <p key={`${i}.${j}`} className="para"><Inline text={q.trim()} /></p>)
        ),
      )}
    </>
  );
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
      return b.level && b.level >= 4 ? <h4 className="sub-heading"><U u={b.t} mode={mode} /></h4> : <h3 className="sub-heading"><U u={b.t} mode={mode} /></h3>;
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
    case "code":
      return <CodeBlock text={b.text} />;
    case "figure":
      return (
        <figure className="figure">
          <Fig id={b.id} />
          {b.caption && <figcaption><U u={b.caption} mode={mode} /></figcaption>}
        </figure>
      );
    case "def":
      return (
        <section className="fn-card" id={`fn-${b.name}`}>
          <header>
            <span className="fn-kind">函数</span>
            <span className="fn-name">{b.name}</span>
          </header>
          <pre className="sig">{b.sigs.join("\n")}</pre>
          <Blocks blocks={b.blocks} mode={mode} />
        </section>
      );
    case "dl":
      return (
        <dl className="deflist">
          {b.items.map((it, i) => (
            <div key={i} className="def-item">
              <dt><U u={it.term} mode={mode} /></dt>
              <dd><Blocks blocks={it.blocks} mode={mode} /></dd>
            </div>
          ))}
        </dl>
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
  ex, n, sectionId, last, onAttempt,
}: {
  ex: Exercise; n: number; sectionId: string;
  last?: AttemptRow; onAttempt: (itemId: string, correct: boolean) => void;
}) {
  const check = ex.check;
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
        <span className="ex-n">试一试 {n}</span>
        {last && <span className={last.correct ? "ex-state ok" : "ex-state bad"}>{last.correct ? "最近一次答对" : "最近一次答错"}</span>}
      </header>
      <Rich text={ex.stem} />

      {check?.kind === "numbers" && (
        <div className="check">
          <label>
            <Inline text={check.ask} />
            <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && submitNumbers()} placeholder="先在工具里做，再填结果；例如 1, -2 或 3/4" />
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

      {ex.sol && (
        <div className="sol-wrap">
          <button className="link" onClick={() => setShowSol((v) => !v)}>
            {showSol ? "收起参考做法" : "查看参考做法"}
          </button>
          {showSol && (
            <div className="sol">
              <Rich text={ex.sol} />
            </div>
          )}
        </div>
      )}
    </article>
  );
}

export function SectionView({
  data, exercises, mode, attempts, onAttempt,
}: {
  data: SectionData; exercises: Exercise[] | null; mode: ViewMode;
  attempts: AttemptRow[]; onAttempt: (itemId: string, correct: boolean) => void;
}) {
  const lastBy = new Map<string, AttemptRow>();
  for (const a of attempts) if (a.knowledge_id === data.id) lastBy.set(a.item_id, a); // 已按 answered_at 升序，后者覆盖前者
  return (
    <div className="section-view">
      <h1>{data.title_zh}<small>{data.title_en}</small></h1>
      <Blocks blocks={data.blocks} mode={mode} />
      {exercises && exercises.length > 0 && (
        <div className="exercises">
          <h2>试一试<small>{exercises.length} 道 · 在本机 Octave 里动手，再回来核对结果</small></h2>
          {exercises.map((ex, i) => (
            <ExerciseCard key={ex.id} ex={ex} n={i + 1} sectionId={data.id} last={lastBy.get(`${data.id}.${ex.id}`)} onAttempt={onAttempt} />
          ))}
        </div>
      )}
    </div>
  );
}
