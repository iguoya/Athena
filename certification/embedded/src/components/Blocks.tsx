// 9 种内容块的渲染器(ADR 0058:内容驱动 UI,不按章手写整页)。
import { useMemo } from "react";
import katex from "katex";
import { Lightbulb, AlertTriangle, XOctagon } from "lucide-react";
import type { Block } from "../types";
import { resolveViz } from "../viz";
import { InlineText } from "./InlineText";
import { cn } from "@/lib/utils";

const CALLOUT = {
  tip: { icon: Lightbulb, cls: "border-emerald-200 bg-emerald-50", iconCls: "text-emerald-600", label: "要点" },
  warn: { icon: AlertTriangle, cls: "border-amber-200 bg-amber-50", iconCls: "text-amber-600", label: "注意" },
  trap: { icon: XOctagon, cls: "border-rose-200 bg-rose-50", iconCls: "text-rose-600", label: "陷阱" },
} as const;

export default function Blocks({ block }: { block: Block }) {
  const formulaHtml = useMemo(
    () =>
      block.type === "formula"
        ? katex.renderToString(block.latex ?? "", {
            displayMode: true,
            throwOnError: false,
            output: "html",
          })
        : "",
    [block],
  );

  switch (block.type) {
    case "lead":
      return (
        <div
          className="rounded-2xl border-l-4 px-5 py-4"
          style={{
            borderLeftColor: "var(--tk-accent)",
            background: "linear-gradient(to right, var(--tk-accent-soft), transparent)",
          }}
        >
          <p
            className="prose-lesson text-[15px]"
            style={{ color: "color-mix(in srgb, var(--tk-fg) 88%, transparent)" }}
          >
            <InlineText text={block.text} />
          </p>
        </div>
      );

    case "text":
      return (
        <p className="prose-lesson text-[15px]">
          <InlineText text={block.text} />
        </p>
      );

    case "formula":
      return (
        <figure className="tk-card px-6 py-5">
          <div
            className="formula-block overflow-x-auto"
            dangerouslySetInnerHTML={{ __html: formulaHtml }}
          />
          {block.caption && (
            <figcaption className="mt-3 text-center text-[13px]" style={{ color: "var(--tk-muted)" }}>
              {block.caption}
            </figcaption>
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
                className="tk-card border-t-[3px] p-5"
                style={{ borderTopColor: i === 0 ? "var(--tk-accent)" : "#fb923c" }}
              >
                <div
                  className="mb-2 font-semibold"
                  style={{ color: "color-mix(in srgb, var(--tk-fg) 92%, transparent)" }}
                >
                  {side?.title}
                </div>
                <p
                  className="prose-lesson text-[14px]"
                  style={{ color: "color-mix(in srgb, var(--tk-fg) 76%, transparent)" }}
                >
                  <InlineText text={side?.body} />
                </p>
              </div>
            ))}
          </div>
        </figure>
      );

    case "steps":
      return (
        <figure className="tk-card p-5">
          <figcaption className="mb-4 font-semibold">{block.title}</figcaption>
          <ol className="space-y-3">
            {(block.items ?? []).map((step, i) => (
              <li key={i} className="flex gap-3">
                <span className="accent-gradient mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white">
                  {i + 1}
                </span>
                <span className="prose-lesson text-[14px]">
                  <InlineText text={step} />
                </span>
              </li>
            ))}
          </ol>
        </figure>
      );

    case "table":
      return (
        <figure className="tk-card overflow-hidden">
          {block.title && (
            <figcaption
              className="border-b px-5 py-3 font-semibold"
              style={{ borderColor: "var(--tk-line)" }}
            >
              {block.title}
            </figcaption>
          )}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13.5px]">
              <thead>
                <tr className="accent-soft">
                  {(block.headers ?? []).map((h, i) => (
                    <th
                      key={i}
                      className="px-4 py-2.5 font-semibold"
                      style={{ color: "var(--tk-accent-deep)" }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(block.rows ?? []).map((row, ri) => (
                  <tr
                    key={ri}
                    style={{
                      background:
                        ri % 2 === 0
                          ? "transparent"
                          : "color-mix(in srgb, var(--tk-bg) 55%, transparent)",
                    }}
                  >
                    {row.map((cell, ci) => (
                      <td
                        key={ci}
                        className="prose-lesson px-4 py-2.5 align-top"
                        style={{ color: "color-mix(in srgb, var(--tk-fg) 80%, transparent)" }}
                      >
                        <InlineText text={cell} />
                      </td>
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
        <figure className="overflow-hidden rounded-2xl" style={{ background: "#1d3129" }}>
          <pre className="overflow-x-auto p-5 font-mono text-[13px] leading-relaxed text-[#d9f2e6]">
            <code>{block.code}</code>
          </pre>
        </figure>
      );

    case "callout": {
      const callout = CALLOUT[block.kind ?? "tip"];
      return (
        <div className={cn("rounded-2xl border px-5 py-4", callout.cls)}>
          <div className={cn("mb-1.5 flex items-center gap-2 text-sm font-bold", callout.iconCls)}>
            <callout.icon size={16} />
            {callout.label}:{block.title}
          </div>
          <p
            className="prose-lesson text-[14px]"
            style={{ color: "color-mix(in srgb, var(--tk-fg) 82%, transparent)" }}
          >
            <InlineText text={block.text} />
          </p>
        </div>
      );
    }

    case "viz": {
      const Viz = resolveViz(block.component ?? "");
      return (
        <figure>
          <div className="tk-card overflow-hidden">
            {Viz ? (
              <Viz params={block.params ?? {}} />
            ) : (
              <div className="p-4 text-sm text-rose-600">未注册的可视化组件:{block.component}</div>
            )}
          </div>
          {block.caption && (
            <figcaption className="mt-2 text-center text-[13px]" style={{ color: "var(--tk-muted)" }}>
              {block.caption}
            </figcaption>
          )}
        </figure>
      );
    }
  }
}
