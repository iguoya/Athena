import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";

/**
 * 官方节页的对照翻译稿渲染器。
 * 稿件语法是受限的约定（应用 ADR 0002）：
 *   - `> ` 连续行 = 英文原文块（官方文档原段）
 *   - 紧随的普通段 = 中文翻译
 *   - ``` 围栏 = 代码块（照录不译）
 *   - ## / ### = 官方节/子节标题
 *   - `- ` 列表项（原文块内的 `- ` 为英文列表，块外的为中文列表）
 * 章名、节名、分页一律来自官方 DocBook，渲染顺序即原文顺序。
 */

interface Block {
  type: "heading" | "en" | "zh" | "code" | "list";
  level?: number;
  lang?: string;
  lines: string[];
}

function parse(input: string): Block[] {
  const markdown = input.replace(/\r\n/g, "\n"); // git 工作区可能是 CRLF
  const blocks: Block[] = [];
  const lines = markdown.replace(/^---\n[\s\S]*?\n---\n/, "") // front matter
    .replace(/<!--[\s\S]*?-->\n?/, "") // 头部来源注释
    .split("\n");
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const body: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith("```")) {
        body.push(lines[i]);
        i += 1;
      }
      i += 1; // 收尾 ```
      blocks.push({ type: "code", lang: lang || "text", lines: body });
      continue;
    }
    if (line.startsWith("### ")) {
      blocks.push({ type: "heading", level: 3, lines: [line.slice(4)] });
      i += 1;
      continue;
    }
    if (line.startsWith("## ")) {
      blocks.push({ type: "heading", level: 2, lines: [line.slice(3)] });
      i += 1;
      continue;
    }
    if (line.startsWith("> ") || line === ">") {
      const body: string[] = [];
      while (i < lines.length && (lines[i].startsWith("> ") || lines[i] === ">")) {
        body.push(lines[i] === ">" ? "" : lines[i].slice(2));
        i += 1;
      }
      blocks.push({ type: "en", lines: body });
      continue;
    }
    if (line.startsWith("- ")) {
      const items: string[] = [];
      while (i < lines.length && lines[i].startsWith("- ")) {
        items.push(lines[i].slice(2));
        i += 1;
      }
      blocks.push({ type: "list", lines: items });
      continue;
    }
    if (line.trim() === "") {
      i += 1;
      continue;
    }
    blocks.push({ type: "zh", lines: [line] });
    i += 1;
  }
  return blocks;
}

export function PageView({
  chapterId,
  pageId,
}: {
  chapterId: string;
  pageId: string;
}) {
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const path = `/content/chapters/${chapterId}/${pageId}.md`;
    (async () => {
      try {
        setMarkdown(await invoke<string>("get_page_content", { chapterId, pageId }));
      } catch {
        try {
          const response = await fetch(path);
          if (!response.ok) throw new Error(String(response.status));
          setMarkdown(await response.text());
        } catch (fetchError) {
          if (!cancelled) setError(`读不到对照稿：${fetchError}`);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [chapterId, pageId]);

  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (markdown == null) return <p className="text-muted">正在读取对照稿……</p>;

  const blocks = parse(markdown);
  return (
    <article className="max-w-none">
      {blocks.map((block, index) => {
        switch (block.type) {
          case "heading":
            return block.level === 2 ? (
              <h2
                key={index}
                className="mt-10 border-b border-line pb-2 font-display text-2xl font-semibold text-accent first:mt-0"
              >
                {block.lines[0]}
              </h2>
            ) : (
              <h3 key={index} className="mt-8 font-display text-xl font-semibold text-accent-deep">
                {block.lines[0]}
              </h3>
            );
          case "en":
            return (
              <blockquote
                key={index}
                className="my-4 border-l-4 border-accent/50 bg-surface-2 py-3 pl-4 pr-3 font-display text-[15px] italic leading-relaxed text-fg/75"
              >
                {block.lines.map((line, j) =>
                  line === "" ? (
                    <div key={j} className="h-2" />
                  ) : line.startsWith("- ") ? (
                    <p key={j} className="pl-4">
                      • {line.slice(2)}
                    </p>
                  ) : (
                    <p key={j}>{line}</p>
                  ),
                )}
              </blockquote>
            );
          case "zh":
            return (
              <p key={index} className="my-4 leading-loose text-fg/90">
                {block.lines[0]}
              </p>
            );
          case "list":
            return (
              <ul key={index} className="my-4 list-disc space-y-1 pl-6 leading-loose text-fg/90">
                {block.lines.map((item, j) => (
                  <li key={j}>{item}</li>
                ))}
              </ul>
            );
          case "code":
            return (
              <figure key={index} className="my-5">
                <div className="overflow-hidden rounded-card ring-1 ring-line">
                  <div className="flex items-center bg-bg-2 px-4 py-1.5">
                    <span className="font-mono text-xs font-medium text-accent">{block.lang}</span>
                  </div>
                  <pre className="overflow-x-auto bg-[#F6F6F6] p-4 font-mono text-[13px] leading-relaxed text-[#555555]">
                    <code>{block.lines.join("\n")}</code>
                  </pre>
                </div>
              </figure>
            );
        }
      })}
    </article>
  );
}
