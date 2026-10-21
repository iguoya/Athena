import { invoke } from "@tauri-apps/api/core";
import { useEffect, useMemo, useState } from "react";
import { Inline, renderMath } from "./Inline";
import type { AttemptRow, Block, Exercise, SectionData } from "./types";

const ENV_ZH: Record<string, string> = {
  note: "注", warning: "警告", tip: "提示", seealso: "另见",
  important: "重要", attention: "注意", hint: "提示",
};

/** 一幅插图：svg 由 scripts/render_figures.py 预先渲染进 content/figures/；缺图时显示占位。 */
function Fig({ id }: { id: string }) {
  const [svg, setSvg] = useState<string | null | undefined>(undefined);
  useEffect(() => {
    let alive = true;
    invoke<string | null>("get_figure", { figId: id }).then((v) => alive && setSvg(v)).catch(() => alive && setSvg(null));
    return () => { alive = false; };
  }, [id]);
  if (svg === undefined) return null;
  if (!svg) return <div className="figure-note">原书此处有一幅图（{id}），尚未渲染。</div>;
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

/** 题面的中文与代码：空行分段，``` 围栏是代码块。 */
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

function Blocks({ blocks }: { blocks: Block[] }) {
  return (
    <>
      {blocks.map((b, i) => (
        <BlockView key={i} b={b} />
      ))}
    </>
  );
}

function BlockView({ b }: { b: Block }) {
  switch (b.k) {
    case "p":
      return <p className="para"><Inline text={b.t} /></p>;
    case "heading":
      return b.level && b.level >= 4 ? <h4 className="sub-heading"><Inline text={b.t} /></h4> : <h3 className="sub-heading"><Inline text={b.t} /></h3>;
    case "math":
      return <div className="display-math" dangerouslySetInnerHTML={{ __html: renderMath(b.tex, true) }} />;
    case "box":
      return (
        <section className={`box box-${b.env}`}>
          <header>
            <span className="box-kind">{ENV_ZH[b.env] ?? b.env}</span>
            {b.title && <span className="box-title"><Inline text={b.title} /></span>}
          </header>
          <Blocks blocks={b.blocks} />
        </section>
      );
    case "list": {
      const Tag = b.ordered ? "ol" : "ul";
      return (
        <Tag className={b.ordered ? "list-ord" : "list-bul"}>
          {b.items.map((it, i) => (
            <li key={i}><Blocks blocks={it} /></li>
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
          {b.caption && <figcaption><Inline text={b.caption} /></figcaption>}
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
          <Blocks blocks={b.blocks} />
        </section>
      );
    case "dl":
      return (
        <dl className="deflist">
          {b.items.map((it, i) => (
            <div key={i} className="def-item">
              <dt><Inline text={it.term} /></dt>
              <dd><Blocks blocks={it.blocks} /></dd>
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
                  <td key={i}><Inline text={c} /></td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
  }
}

function ExerciseCard({
  ex, sectionId, last, onAttempt,
}: {
  ex: Exercise; sectionId: string;
  last?: AttemptRow; onAttempt: (itemId: string, correct: boolean) => void;
}) {
  const check = ex.check;
  const [pick, setPick] = useState<number | null>(null);
  const [verdict, setVerdict] = useState<null | { ok: boolean; note?: string }>(null);
  const [showSol, setShowSol] = useState(false);
  const itemId = `${sectionId}.${ex.id}`;

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
        <span className="ex-n">{ex.id}</span>
        {last && <span className={last.correct ? "ex-state ok" : "ex-state bad"}>{last.correct ? "最近一次答对" : "最近一次答错"}</span>}
      </header>
      <Rich text={ex.stem} />

      {check?.kind === "choice" && (
        <div className="check choice">
          {check.ask && <div className="check-ask"><Inline text={check.ask} /></div>}
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
            {showSol ? "收起参考解答" : "自己证明后再对照参考解答"}
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

/** 基础 / 进阶：stage 2 的函数与图默认折叠；折叠后下面没有内容的小标题也一并去掉。 */
export function visibleBlocks(blocks: Block[], advanced: boolean): { blocks: Block[]; hidden: number } {
  const hide = (b: Block) => !advanced && (b.k === "def" || b.k === "figure") && b.stage === 2;
  const hidden = blocks.filter((b) => hide(b) && b.k === "def").length;
  let out = blocks.filter((b) => !hide(b));
  for (;;) {
    const next = out.filter((b, k) => {
      if (b.k !== "heading") return true;
      const nx = out[k + 1];
      return !(nx === undefined || (nx.k === "heading" && (nx.level ?? 9) <= (b.level ?? 9)));
    });
    if (next.length === out.length) break;
    out = next;
  }
  return { blocks: out, hidden };
}

export function SectionView({
  data, exercises, advanced, onAdvanced, attempts, onAttempt,
}: {
  data: SectionData; exercises: Exercise[] | null; advanced: boolean; onAdvanced: (v: boolean) => void;
  attempts: AttemptRow[]; onAttempt: (itemId: string, correct: boolean) => void;
}) {
  const shown = useMemo(() => visibleBlocks(data.blocks, advanced), [data.blocks, advanced]);
  const lastBy = new Map<string, AttemptRow>();
  for (const a of attempts) if (a.knowledge_id === data.id) lastBy.set(a.item_id, a); // 已按 answered_at 升序，后者覆盖前者
  return (
    <div className="section-view">
      <h1>{data.title}</h1>
      {!advanced && shown.hidden > 0 && (
        <p className="stage-note">
          本章先只讲基础部分。另有 {shown.hidden} 个进阶函数已折叠。
          <button className="link" onClick={() => onAdvanced(true)}>展开进阶内容</button>
        </p>
      )}
      <Blocks blocks={shown.blocks} />
      {exercises && exercises.length > 0 && (
        <div className="exercises">
          <h2>原书习题<small>{exercises.length} 道 · 判分做思路与辨析，证明本身对照参考解答自评</small></h2>
          {exercises.map((ex) => (
            <ExerciseCard key={ex.id} ex={ex} sectionId={data.id} last={lastBy.get(`${data.id}.${ex.id}`)} onAttempt={onAttempt} />
          ))}
        </div>
      )}
    </div>
  );
}
