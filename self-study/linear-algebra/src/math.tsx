import type { ReactNode } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

type Segment = { math: boolean; display: boolean; body: string };

/** 文本按公式分段：$$...$$ 块级、$...$ 行内；其余是普通文本。 */
export function splitMath(text: string): Segment[] {
  const out: Segment[] = [];
  let rest = text;
  const re = /\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/;
  for (;;) {
    const m = rest.match(re);
    if (!m) {
      if (rest) out.push({ math: false, display: false, body: rest });
      break;
    }
    const idx = m.index ?? 0;
    if (idx > 0) out.push({ math: false, display: false, body: rest.slice(0, idx) });
    out.push({ math: true, display: m[1] !== undefined, body: m[1] ?? m[2] });
    rest = rest.slice(idx + m[0].length);
  }
  return out;
}

function renderKatex(body: string, display: boolean): string {
  try {
    return katex.renderToString(body, { displayMode: display, throwOnError: true });
  } catch {
    // 公式写错时显示原文，不让整节白屏；提交前 lint 会拦语法错误。
    return `<code class="katex-error">${body}</code>`;
  }
}

/**
 * 渲染混排文本：普通文本 + $公式$ + $$块级公式$$，外加行内加粗 **...**。
 * 加粗可以跨公式（如 **$k$ 阶子式**），所以状态在各段之间传递。这里只认加粗，
 * 其余 Markdown 一概不解析，避免内容里的星号、下划线被误判。
 */
export function Tex({ text }: { text: string }) {
  let bold = false;
  const nodes: ReactNode[] = [];
  splitMath(text).forEach((seg, i) => {
    if (seg.math) {
      const el = (
        <span
          key={i}
          className={seg.display ? "math-display" : "math-inline"}
          dangerouslySetInnerHTML={{ __html: renderKatex(seg.body, seg.display) }}
        />
      );
      nodes.push(bold ? <strong key={i}>{el}</strong> : el);
      return;
    }
    seg.body.split("**").forEach((part, j) => {
      if (j > 0) bold = !bold;
      if (!part) return;
      nodes.push(bold ? <strong key={`${i}-${j}`}>{part}</strong> : <span key={`${i}-${j}`}>{part}</span>);
    });
  });
  return <>{nodes}</>;
}

type ProseRun = { kind: "p" | "ul" | "ol"; lines: string[] };

/** 一段文字按行分组：连续的「- 」行成无序列表，连续的「1. 」行成有序列表，其余行并成一段。 */
function proseRuns(para: string): ProseRun[] {
  const runs: ProseRun[] = [];
  for (const line of para.split("\n")) {
    if (line.trim() === "") continue;
    const kind = /^- /.test(line) ? "ul" : /^\d+\. /.test(line) ? "ol" : "p";
    const last = runs[runs.length - 1];
    if (last && last.kind === kind) last.lines.push(line);
    else runs.push({ kind, lines: [line] });
  }
  return runs;
}

/**
 * 正文块：空行分段；段内连续的「- 」行是无序列表，连续的「1. 」行是有序列表，其余是普通段落。
 * 公式块 $$...$$ 内部不要出现空行；列表项只占一行。
 */
export function Prose({ text }: { text: string }) {
  return (
    <>
      {text.split(/\n\s*\n/).flatMap((para, i) =>
        proseRuns(para).map((run, j) => {
          const key = `${i}-${j}`;
          if (run.kind === "p") {
            return (
              <p key={key}>
                <Tex text={run.lines.join("\n")} />
              </p>
            );
          }
          const items = run.lines.map((l, k) => (
            <li key={k}>
              <Tex text={l.replace(run.kind === "ul" ? /^- / : /^\d+\. /, "")} />
            </li>
          ));
          return run.kind === "ul" ? <ul key={key}>{items}</ul> : <ol key={key}>{items}</ol>;
        }),
      )}
    </>
  );
}
