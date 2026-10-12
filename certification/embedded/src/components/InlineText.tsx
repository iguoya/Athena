// 极简行内格式(ADR 0058):**加粗** 与 `代码`,渲染成 React 片段。
import { Fragment } from "react";

const TOKEN = /(\*\*[^*]+\*\*|`[^`]+`)/g;

export function InlineText({ text }: { text?: string }) {
  const source = text ?? "";
  const parts: React.ReactNode[] = [];
  let last = 0;
  let key = 0;
  let m: RegExpExecArray | null;
  TOKEN.lastIndex = 0;
  while ((m = TOKEN.exec(source)) !== null) {
    if (m.index > last) parts.push(source.slice(last, m.index));
    const token = m[0];
    parts.push(
      token.startsWith("**") ? (
        <strong key={key++}>{token.slice(2, -2)}</strong>
      ) : (
        <code key={key++}>{token.slice(1, -1)}</code>
      ),
    );
    last = m.index + token.length;
  }
  if (last < source.length) parts.push(source.slice(last));
  return <Fragment>{parts}</Fragment>;
}
