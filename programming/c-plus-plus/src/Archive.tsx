import { Fragment, useEffect, useRef, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";
import { mountArchivePanel, type ArchiveBlock } from "@athena/viz";

// 历史归档章节的呈现（ADR 0176）：条目来自 content/archive.json，不判分、不计入进度，
// 所以这里没有作答与掌握度。代码视图、批注与运行都由 @athena/viz 的 archive-panel 负责，
// 读文件与运行走本应用 Rust 壳里的 load_case_files / run_archive_case。

type Block =
  | { type: "lead" | "prose"; text: string }
  | { type: "callout"; tone?: string; title?: string; text: string }
  | ArchiveBlock;

export type ArchiveTopic = {
  id: string;
  title: string;
  guide_line: string;
  outline?: Record<string, string>;
  lesson: { blocks: Block[] };
};

export type ArchiveChapter = { id: string; title: string; summary: string; topics: ArchiveTopic[] };

const OUTLINE_LABELS: [string, string][] = [
  ["promise", "读完能做到"],
  ["pain", "为什么值得看"],
  ["model", "这份代码的结构"],
  ["scope", "范围"],
  ["judgment", "怎么判断"],
  ["landing", "落点"],
];

/** guide_line 以 “[组名] ” 开头则取组名，否则归“未分组”。 */
export function groupOf(t: ArchiveTopic): { group: string; line: string } {
  const m = /^\[([^\]]+)\]\s*([\s\S]*)$/.exec(t.guide_line ?? "");
  return m ? { group: m[1], line: m[2] } : { group: "未分组", line: t.guide_line ?? "" };
}

/** 讲解文字里的 **粗体** 与 `代码` 两种行内标记；别的原样显示。 */
function inline(text: string): ReactNode {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) return <code key={i}>{part.slice(1, -1)}</code>;
    return <Fragment key={i}>{part}</Fragment>;
  });
}

function ArchivePanel({ block }: { block: ArchiveBlock }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const host = ref.current;
    if (!host) return;
    mountArchivePanel(host, block, {
      loadFiles: (caseId) => invoke("load_case_files", { caseId }),
      run: (caseId, sources, std, stdin) =>
        invoke("run_archive_case", { caseId, sources, std: std ?? null, stdin: stdin ?? null }),
    });
    return () => {
      host.innerHTML = "";
      host.className = "";
    };
  }, [block]);
  return <div ref={ref} />;
}

export function ArchiveLesson({ topic }: { topic: ArchiveTopic }) {
  const outline = topic.outline ?? {};
  return (
    <article className="archive-lesson mx-auto max-w-5xl">
      <p className="text-sm text-[var(--muted)]">历史归档 · {topic.id}</p>
      <h1 className="mt-1 text-2xl font-semibold">{topic.title}</h1>
      <p className="mt-2 text-sm text-[var(--muted)]">{groupOf(topic).line}</p>
      <div className="mt-6 space-y-4">
        {topic.lesson.blocks.map((b, i) => {
          if (b.type === "archive") return <ArchivePanel key={`${topic.id}:${i}`} block={b} />;
          if (b.type === "callout")
            return (
              <aside key={i} className="rounded border border-[var(--line)] bg-white px-3 py-2 text-sm leading-relaxed">
                {b.title ? <strong>{b.title}：</strong> : null}
                {inline(b.text)}
              </aside>
            );
          return (
            <p key={i} className={b.type === "lead" ? "text-lg leading-relaxed" : "leading-relaxed"}>
              {inline(b.text)}
            </p>
          );
        })}
      </div>
      <details className="mt-6 text-sm text-[var(--muted)]">
        <summary className="cursor-pointer">方向与边界</summary>
        <dl className="mt-2 space-y-2">
          {OUTLINE_LABELS.filter(([k]) => outline[k]).map(([k, label]) => (
            <div key={k}>
              <dt className="font-semibold">{label}</dt>
              <dd>{outline[k]}</dd>
            </div>
          ))}
        </dl>
      </details>
    </article>
  );
}
