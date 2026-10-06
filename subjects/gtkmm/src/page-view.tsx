import { useEffect, useMemo, useState, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";
import { CircleAlert } from "lucide-react";

/**
 * 官方节页渲染器：读段落快照 JSON（scripts/sync_upstream.py 生成）。
 * - 原文段落保留官方内联格式（粗体/斜体/行内代码/链接，受限 markdown）
 * - 代码块逐字照录（应用 ADR 0002：代码不翻译不改写）
 * - figure 渲染官方图片（figures/ 随快照入 content/figures）
 * - 标记 key 的段落是章节重点语句，高亮强调
 */

interface SnapshotBlock {
  type: "para" | "listitem" | "code" | "heading" | "figure";
  text: string;
  sha: string;
  zh?: string | null;
  ref?: string | null;
  key?: boolean;
  status?: "stale" | "untranslated";
  stale_from?: string | null;
}

interface Snapshot {
  chapter: string;
  section: string;
  title: string;
  upstream_commit: string;
  blocks: SnapshotBlock[];
}

interface RenderGroup {
  kind: "heading" | "para" | "list" | "code" | "figure";
  blocks: SnapshotBlock[];
}

function groupBlocks(blocks: SnapshotBlock[]): RenderGroup[] {
  const groups: RenderGroup[] = [];
  for (const block of blocks) {
    const last = groups[groups.length - 1];
    if (block.type === "listitem" && last?.kind === "list") {
      last.blocks.push(block);
    } else {
      groups.push({ kind: block.type === "listitem" ? "list" : block.type, blocks: [block] });
    }
  }
  return groups;
}

/** 受限行内 markdown → JSX：**粗**、*斜*、`代码`、[文字](链接)。 */
function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern =
    /\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`|\[([^\]]+)\]\(([^)]*)\)/g;
  let cursor = 0;
  let match: RegExpExecArray | null;
  let key = 0;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) nodes.push(text.slice(cursor, match.index));
    if (match[1] !== undefined) {
      nodes.push(
        <strong key={key++} className="font-semibold text-fg">
          {match[1]}
        </strong>,
      );
    } else if (match[2] !== undefined) {
      nodes.push(
        <em key={key++} className="italic">
          {match[2]}
        </em>,
      );
    } else if (match[3] !== undefined) {
      nodes.push(
        <code
          key={key++}
          className="rounded bg-[#efefef] px-1.5 py-0.5 font-mono text-[0.85em] text-[#555555] ring-1 ring-line"
        >
          {match[3]}
        </code>,
      );
    } else if (match[4] !== undefined) {
      nodes.push(
        <a
          key={key++}
          href={match[5]}
          target="_blank"
          rel="noreferrer"
          className="font-semibold text-link hover:underline"
        >
          {match[4]}
        </a>,
      );
    }
    cursor = pattern.lastIndex;
  }
  if (cursor < text.length) nodes.push(text.slice(cursor));
  return nodes;
}

function TranslatedText({ text }: { text: string }) {
  return (
    <>
      {text.split("\n").map((line, index) => (
        <p key={index} className="my-3 leading-loose text-fg/90">
          {renderInline(line)}
        </p>
      ))}
    </>
  );
}

function PendingBadge({ stale }: { stale?: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[20px] ring-1 ${
        stale
          ? "bg-amber-500/10 text-amber-700 ring-amber-500/30"
          : "bg-surface-2 text-muted ring-line"
      }`}
    >
      {stale ? "原文已更新 · 译文待复核" : "此段待译"}
      {stale && <CircleAlert className="size-5" />}
    </span>
  );
}

export function PageView({
  chapterId,
  pageId,
}: {
  chapterId: string;
  pageId: string;
}) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const path = `/content/chapters/${chapterId}/${pageId}.json`;
    (async () => {
      try {
        const raw = await invoke<unknown>("get_page_content", { chapterId, pageId });
        setSnapshot(typeof raw === "string" ? (JSON.parse(raw) as Snapshot) : (raw as Snapshot));
      } catch {
        try {
          const response = await fetch(path);
          if (!response.ok) throw new Error(String(response.status));
          setSnapshot((await response.json()) as Snapshot);
        } catch (fetchError) {
          if (!cancelled) setError(`读不到段落快照：${fetchError}`);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [chapterId, pageId]);

  const groups = useMemo(() => (snapshot ? groupBlocks(snapshot.blocks) : []), [snapshot]);

  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (snapshot == null) return <p className="text-muted">正在读取段落快照……</p>;

  return (
    <article className="max-w-none">
      {groups.map((group, index) => {
        switch (group.kind) {
          case "heading":
            return (
              <h3
                key={index}
                className="mt-9 font-display text-[30px] font-semibold text-accent-deep"
              >
                {renderInline(group.blocks[0].text)}
              </h3>
            );
          case "code":
            return (
              <figure key={index} className="my-5">
                <div className="overflow-hidden rounded-card ring-1 ring-line">
                  <div className="flex items-center bg-bg-2 px-4 py-1.5">
                    <span className="font-mono text-[20px] font-medium text-accent">cpp</span>
                  </div>
                  <pre className="overflow-x-auto bg-[#F6F6F6] p-5 font-mono text-[20px] leading-relaxed text-[#555555]">
                    <code>{group.blocks[0].text}</code>
                  </pre>
                </div>
              </figure>
            );
          case "figure": {
            const block = group.blocks[0];
            return (
              <figure key={index} className="my-6">
                {block.ref && (
                  <img
                    src={`/content/${block.ref}`}
                    alt={block.text}
                    loading="lazy"
                    className="mx-auto max-w-3xl rounded-card bg-white p-3 shadow-card ring-1 ring-line"
                  />
                )}
                <figcaption className="mt-2 text-center text-[20px] text-muted">
                  图 · {block.text}
                </figcaption>
              </figure>
            );
          }
          case "list": {
            const isKey = group.blocks.some((b) => b.key);
            return (
              <div
                key={index}
                className={`my-5 rounded-card p-5 ring-1 ${
                  isKey ? "bg-accent-soft/60 ring-accent/40" : "bg-surface ring-line shadow-card"
                }`}
              >
                <ul className="space-y-3">
                  {group.blocks.map((block) => (
                    <li key={block.sha} className="flex flex-col gap-1.5">
                      <span className="font-display text-[22px] italic leading-relaxed text-fg/70">
                        • {renderInline(block.text)}
                      </span>
                      {block.zh && (
                        <span className="pl-5 text-[25px] leading-relaxed text-fg/90">
                          {renderInline(block.zh)}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
                {!group.blocks.every((b) => b.zh) && (
                  <p className="mt-3">
                    <PendingBadge />
                  </p>
                )}
              </div>
            );
          }
          case "para": {
            const block = group.blocks[0];
            const stale = block.status === "stale";
            return (
              <div key={index} className="my-6">
                <blockquote
                  className={`border-l-4 bg-surface-2 py-4 pl-5 pr-4 font-display text-[22px] italic leading-relaxed text-fg/75 ${
                    stale
                      ? "border-amber-500/70"
                      : block.key
                        ? "border-accent bg-accent-soft/60"
                        : "border-accent/50"
                  }`}
                >
                  {block.text.split("\n").map((line, j) => (
                    <p key={j}>{renderInline(line)}</p>
                  ))}
                  {block.key && (
                    <span className="mt-2 block text-[20px] font-medium not-italic text-accent">
                      ★ 本节重点
                    </span>
                  )}
                </blockquote>
                {block.zh ? (
                  <div
                    className={
                      block.key
                        ? "rounded-card bg-accent-soft/40 px-5 py-2 ring-1 ring-accent/20"
                        : ""
                    }
                  >
                    <TranslatedText text={block.zh} />
                  </div>
                ) : block.stale_from ? (
                  <>
                    <p className="my-2 text-[20px] text-amber-700">
                      以下为原文变更前的旧译文，待复核：
                    </p>
                    <TranslatedText text={block.stale_from} />
                    <p className="mt-2">
                      <PendingBadge stale />
                    </p>
                  </>
                ) : (
                  <p className="mt-2">
                    <PendingBadge />
                  </p>
                )}
              </div>
            );
          }
        }
      })}
    </article>
  );
}
