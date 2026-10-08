// 9 种内容块的渲染器(ADR 0058:内容驱动 UI,不按章手写整页)。
// 行内格式只支持两种:**加粗** 与 `代码`,渲染成 React 节点。
import katex from "katex";
import { Lightbulb, AlertTriangle, XOctagon } from "lucide-react";
import type { ReactNode } from "react";
import type { Block } from "../types";
import { VizRegistry } from "../viz";

/** 极简行内格式:**加粗** 与 `代码`。 */
export function inline(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const token = m[0];
    if (token.startsWith("**")) {
      parts.push(<strong key={key++}>{token.slice(2, -2)}</strong>);
    } else {
      parts.push(<code key={key++}>{token.slice(1, -1)}</code>);
    }
    last = m.index + token.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

function Formula({ latex }: { latex: string }) {
  const html = katex.renderToString(latex, {
    displayMode: true,
    throwOnError: false,
    output: "html",
  });
  return <div className="formula-block overflow-x-auto" dangerouslySetInnerHTML={{ __html: html }} />;
}

export function BlockView({ block }: { block: Block }) {
  switch (block.type) {
    case "lead":
      return (
        <div className="rounded-2xl border-l-4 border-brand-500 bg-gradient-to-r from-brand-50 to-transparent px-5 py-4">
          <p className="prose-lesson text-[15px] text-ink/85">{inline(block.text ?? "")}</p>
        </div>
      );
    case "text":
      return <p className="prose-lesson text-[15px]">{inline(block.text ?? "")}</p>;
    case "formula":
      return (
        <figure className="card px-6 py-5">
          <Formula latex={block.latex ?? ""} />
          {block.caption && (
            <figcaption className="mt-3 text-center text-[13px] text-ink/55">{block.caption}</figcaption>
          )}
        </figure>
      );
    case "compare":
      return (
        <figure>
          <figcaption className="mb-3 text-[15px] font-semibold">{block.title}</figcaption>
          <div className="grid gap-3 md:grid-cols-2">
            {[block.left, block.right].map((side, i) => (
              <div
                key={i}
                className={`card p-5 ${i === 0 ? "border-t-[3px] border-t-brand-500" : "border-t-[3px] border-t-orange-400"}`}
              >
                <div className="mb-2 font-semibold text-ink/90">{side?.title}</div>
                <p className="prose-lesson text-[14px] text-ink/75">{inline(side?.body ?? "")}</p>
              </div>
            ))}
          </div>
        </figure>
      );
    case "steps":
      return (
        <figure className="card p-5">
          <figcaption className="mb-4 font-semibold">{block.title}</figcaption>
          <ol className="space-y-3">
            {(block.items ?? []).map((step, i) => (
              <li key={i} className="flex gap-3">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-500 text-xs font-bold text-white">
                  {i + 1}
                </span>
                <span className="prose-lesson text-[14px]">{inline(step)}</span>
              </li>
            ))}
          </ol>
        </figure>
      );
    case "table":
      return (
        <figure className="card overflow-hidden">
          {block.title && <figcaption className="border-b border-black/5 px-5 py-3 font-semibold">{block.title}</figcaption>}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13.5px]">
              <thead>
                <tr className="bg-brand-50/70">
                  {(block.headers ?? []).map((h, i) => (
                    <th key={i} className="px-4 py-2.5 font-semibold text-brand-800">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(block.rows ?? []).map((row, ri) => (
                  <tr key={ri} className={ri % 2 === 0 ? "bg-white" : "bg-paper/60"}>
                    {row.map((cell, ci) => (
                      <td key={ci} className="prose-lesson px-4 py-2.5 align-top text-ink/80">{inline(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </figure>
      );
    case "code":
      return (
        <figure className="overflow-hidden rounded-2xl bg-ink text-[#e8e6f5]">
          <pre className="overflow-x-auto p-5 font-mono text-[13px] leading-relaxed">
            <code>{block.code}</code>
          </pre>
        </figure>
      );
    case "callout": {
      const kind = block.kind ?? "tip";
      const conf = {
        tip: { icon: Lightbulb, cls: "border-emerald-200 bg-emerald-50", iconCls: "text-emerald-600", label: "要点" },
        warn: { icon: AlertTriangle, cls: "border-amber-200 bg-amber-50", iconCls: "text-amber-600", label: "注意" },
        trap: { icon: XOctagon, cls: "border-rose-200 bg-rose-50", iconCls: "text-rose-600", label: "陷阱" },
      }[kind];
      const Icon = conf.icon;
      return (
        <div className={`rounded-2xl border px-5 py-4 ${conf.cls}`}>
          <div className={`mb-1.5 flex items-center gap-2 text-sm font-bold ${conf.iconCls}`}>
            <Icon size={16} />
            {conf.label}:{block.title}
          </div>
          <p className="prose-lesson text-[14px] text-ink/80">{inline(block.text ?? "")}</p>
        </div>
      );
    }
    case "viz": {
      const Comp = VizRegistry[block.component ?? ""];
      if (!Comp) return <div className="card p-4 text-sm text-rose-600">未注册的可视化组件:{block.component}</div>;
      return (
        <figure>
          <div className="card overflow-hidden">
            <Comp params={block.params ?? {}} />
          </div>
          {block.caption && <figcaption className="mt-2 text-center text-[13px] text-ink/55">{block.caption}</figcaption>}
        </figure>
      );
    }
    default:
      return null;
  }
}

export function LessonBlocks({ blocks }: { blocks: Block[] }) {
  return (
    <div className="space-y-6">
      {blocks.map((b, i) => (
        <BlockView key={i} block={b} />
      ))}
    </div>
  );
}
