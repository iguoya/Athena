// 导引正文里的极简内联标记：**加粗** 与 [文字](#锚点)。导引不需要完整的 Markdown。
import { Fragment, type ReactNode } from "react";

function renderBold(text: string, keyPrefix: string): ReactNode[] {
  const parts = text.split(/\*\*([^*]+)\*\*/g);
  return parts.map((p, j) =>
    j % 2 === 1 ? <strong key={`${keyPrefix}-b${j}`}>{p}</strong> : <Fragment key={`${keyPrefix}-f${j}`}>{p}</Fragment>,
  );
}

export default function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const out: ReactNode[] = [];
  // 先按链接切，链接内不再处理加粗（内容里没有这种组合）。
  const linkRe = /\[([^\]]+)\]\(#([^)]+)\)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = linkRe.exec(text)) !== null) {
    if (m.index > last) out.push(...renderBold(text.slice(last, m.index), `${keyPrefix}-t${i++}`));
    out.push(
      <a key={`${keyPrefix}-a${i++}`} href={`#${m[2]}`}>
        {m[1]}
      </a>,
    );
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(...renderBold(text.slice(last), `${keyPrefix}-t${i++}`));
  return out;
}
