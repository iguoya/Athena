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

/** 渲染混排文本：普通文本 + $公式$ + $$块级公式$$。 */
export function Tex({ text }: { text: string }) {
  return (
    <>
      {splitMath(text).map((seg, i) =>
        seg.math ? (
          <span
            key={i}
            className={seg.display ? "math-display" : "math-inline"}
            dangerouslySetInnerHTML={{ __html: renderKatex(seg.body, seg.display) }}
          />
        ) : (
          <span key={i}>{seg.body}</span>
        ),
      )}
    </>
  );
}
