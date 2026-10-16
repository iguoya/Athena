import type { ReactNode } from "react";

/** 任务书里实际出现的那几种标记：标题、列表、行内代码、粗体。不引 Markdown 库。 */

function inline(text: string, keyPrefix: string): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /\*\*([^*]+)\*\*|`([^`]+)`/g;
  let last = 0;
  let n = 0;
  for (let m = re.exec(text); m; m = re.exec(text)) {
    if (m.index > last) out.push(text.slice(last, m.index));
    if (m[1] !== undefined) {
      out.push(<strong key={`${keyPrefix}-b${n}`}>{m[1]}</strong>);
    } else {
      out.push(
        <code
          key={`${keyPrefix}-c${n}`}
          className="rounded bg-paper px-1 py-0.5 font-mono text-[0.85em] text-ink-900"
        >
          {m[2]}
        </code>,
      );
    }
    n += 1;
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export default function TaskMarkdown({ text }: { text: string }) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  let k = 0;
  while (i < lines.length) {
    const line = lines[i];
    const heading = /^(#{1,3}) (.+)$/.exec(line);
    if (heading) {
      const level = heading[1].length;
      const className =
        level === 1
          ? "mt-4 mb-1 text-base font-bold text-ink-900"
          : "mt-4 mb-1 text-sm font-semibold text-ink-900";
      const Tag = level === 1 ? "h3" : "h4";
      blocks.push(
        <Tag key={k} className={className}>
          {inline(heading[2], `h${k}`)}
        </Tag>,
      );
      k += 1;
      i += 1;
      continue;
    }
    if (/^[-*] /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        let item = lines[i].slice(2);
        i += 1;
        while (i < lines.length && /^[ \t]+\S/.test(lines[i])) {
          item += " " + lines[i].trim();
          i += 1;
        }
        items.push(item);
      }
      const id = k;
      k += 1;
      blocks.push(
        <ul key={id} className="my-1 list-disc space-y-0.5 pl-5 text-sm leading-relaxed text-ink-700">
          {items.map((item, j) => (
            <li key={j}>{inline(item, `u${id}-${j}`)}</li>
          ))}
        </ul>,
      );
      continue;
    }
    if (/^\d+\. /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        let item = lines[i].replace(/^\d+\. /, "");
        i += 1;
        while (i < lines.length && /^[ \t]+\S/.test(lines[i])) {
          item += " " + lines[i].trim();
          i += 1;
        }
        items.push(item);
      }
      const id = k;
      k += 1;
      blocks.push(
        <ol key={id} className="my-1 list-decimal space-y-0.5 pl-5 text-sm leading-relaxed text-ink-700">
          {items.map((item, j) => (
            <li key={j}>{inline(item, `o${id}-${j}`)}</li>
          ))}
        </ol>,
      );
      continue;
    }
    if (line.trim() === "") {
      i += 1;
      continue;
    }
    const id = k;
    k += 1;
    blocks.push(
      <p key={id} className="my-1 text-sm leading-relaxed text-ink-700">
        {inline(line, `p${id}`)}
      </p>,
    );
    i += 1;
  }
  return <div>{blocks}</div>;
}
