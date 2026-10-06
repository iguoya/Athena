import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { CircleAlert } from "lucide-react";

/**
 * 官方节页渲染器：读段落快照 JSON（scripts/sync_upstream.py 生成，
 * 原文由上游 DocBook 动态提取、中文按段挂载——应用 ADR 0002）。
 * 渲染顺序即官方原文顺序：英文段与中文段逐段配对，未译段明示徽章。
 */

interface SnapshotBlock {
  type: "para" | "listitem" | "code" | "heading" | "figure";
  text: string;
  sha: string;
  zh?: string | null;
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

/** 连续 listitem 聚合成一组列表，其余各块自成一组——保持官方原文顺序。 */
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

function TranslatedText({ text }: { text: string }) {
  // 中文翻译可能含换行（原段落内换行），按段渲染
  return (
    <>
      {text.split("\n").map((line, index) => (
        <p key={index} className="my-3 leading-loose text-fg/90">
          {line}
        </p>
      ))}
    </>
  );
}

function PendingBadge({ stale }: { stale?: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] ring-1 ${
        stale
          ? "bg-amber-500/10 text-amber-700 ring-amber-500/30"
          : "bg-surface-2 text-muted ring-line"
      }`}
    >
      {stale ? "原文已更新 · 译文待复核" : "此段待译"}
      {stale && <CircleAlert className="size-3" />}
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
        setSnapshot(await invoke<Snapshot>("get_page_content", { chapterId, pageId }));
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
                className="mt-9 font-display text-xl font-semibold text-accent-deep"
              >
                {group.blocks[0].text}
              </h3>
            );
          case "code":
            return (
              <figure key={index} className="my-5">
                <div className="overflow-hidden rounded-card ring-1 ring-line">
                  <div className="flex items-center bg-bg-2 px-4 py-1.5">
                    <span className="font-mono text-xs font-medium text-accent">cpp</span>
                  </div>
                  <pre className="overflow-x-auto bg-[#F6F6F6] p-4 font-mono text-[13px] leading-relaxed text-[#555555]">
                    <code>{group.blocks[0].text}</code>
                  </pre>
                </div>
              </figure>
            );
          case "figure":
            return (
              <p
                key={index}
                className="my-4 rounded-card bg-surface-2 px-4 py-3 text-center text-sm text-muted ring-1 ring-line"
              >
                图 · {group.blocks[0].text}
              </p>
            );
          case "list": {
            const allTranslated = group.blocks.every((b) => b.zh);
            return (
              <div key={index} className="my-5">
                <div className="rounded-card bg-surface p-4 shadow-card ring-1 ring-line">
                  <ul className="space-y-2">
                    {group.blocks.map((block) => (
                      <li key={block.sha} className="flex flex-col gap-1">
                        <span className="font-display text-[15px] italic leading-relaxed text-fg/70">
                          • {block.text}
                        </span>
                        {block.zh && (
                          <span className="pl-4 text-sm leading-relaxed text-fg/90">
                            {block.zh}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
                {!allTranslated && (
                  <p className="mt-2">
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
              <div key={index} className="my-5">
                <blockquote
                  className={`border-l-4 bg-surface-2 py-3 pl-4 pr-3 font-display text-[15px] italic leading-relaxed text-fg/75 ${
                    stale ? "border-amber-500/70" : "border-accent/50"
                  }`}
                >
                  {block.text.split("\n").map((line, j) => (
                    <p key={j}>{line}</p>
                  ))}
                </blockquote>
                {block.zh ? (
                  <TranslatedText text={block.zh} />
                ) : block.stale_from ? (
                  <>
                    <p className="my-2 text-xs text-amber-700">
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
