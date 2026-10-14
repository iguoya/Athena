import katex from "katex";
import { Fragment, useMemo } from "react";
import { MACROS } from "./macros";
import { splitInline } from "./inline";

export function renderMath(tex: string, display: boolean): string {
  try {
    return katex.renderToString(tex, { macros: { ...MACROS }, throwOnError: true, displayMode: display, strict: "ignore" });
  } catch {
    // check-math.mjs 保证快照里没有这种情况；译文里手滑写错时给出可见的红字而不是整页崩溃
    return `<span class="math-error">${tex.replace(/</g, "&lt;")}</span>`;
  }
}

/** 文字里的 **粗体** 与 *斜体*（公式片段已被 splitInline 隔开，不会被误伤）。 */
function Emph({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return (
    <>
      {parts.map((p, i) => {
        if (p.startsWith("**") && p.endsWith("**") && p.length > 4) return <strong key={i}>{p.slice(2, -2)}</strong>;
        if (p.startsWith("*") && p.endsWith("*") && p.length > 2) return <em key={i}>{p.slice(1, -1)}</em>;
        return <Fragment key={i}>{p}</Fragment>;
      })}
    </>
  );
}

export function Inline({ text }: { text: string }) {
  const segs = useMemo(() => splitInline(text), [text]);
  return (
    <>
      {segs.map((s, i) =>
        s.k === "math" ? (
          <span key={i} dangerouslySetInnerHTML={{ __html: renderMath(s.v, false) }} />
        ) : (
          <Emph key={i} text={s.v} />
        ),
      )}
    </>
  );
}
