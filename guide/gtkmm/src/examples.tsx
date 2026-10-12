// 官方示例区块（应用 ADR 0006、0008）：教程节页顶部（正文之前，先演示后读文）
// 的 exercise/ 示例卡。清单驱动（content/demos.json examples 数组，按 page_ref
// 锚定），不为某章手写页面；代码是 exercise/ 的原样镜像，壳逐字返回、这里不加工。
import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { motion } from "motion/react";
import { BookMarked, ChevronDown, ChevronUp, Play } from "lucide-react";
import type { ExampleEntity } from "./types";
import { highlightCode } from "./highlight";

interface SourceFile {
  path: string;
  content: string;
}

export function OfficialExamples({
  examples,
  onLaunch,
}: {
  /** 锚定当前节 + 章级的官方示例（调用方过滤）；空数组不渲染 */
  examples: ExampleEntity[];
  onLaunch: (exampleId: string) => void;
}) {
  const [openId, setOpenId] = useState<string | null>(null);
  const [sources, setSources] = useState<Record<string, SourceFile[] | "error">>({});

  if (examples.length === 0) return null;

  const toggle = (id: string) => {
    if (openId === id) {
      setOpenId(null);
      return;
    }
    setOpenId(id);
    if (!sources[id]) {
      invoke<SourceFile[]>("read_example_sources", { exampleId: id })
        .then((files) => setSources((prev) => ({ ...prev, [id]: files })))
        .catch(() => setSources((prev) => ({ ...prev, [id]: "error" })));
    }
  };

  return (
    <section className="mt-16">
      <div className="flex items-baseline gap-3">
        <h3 className="font-display text-[26px] font-semibold text-accent">
          官方示例 · 教程同款源码
        </h3>
        <p className="text-[18px] text-muted">
          exercise/ 里的逐字镜像（版本随 upstream.json 钉点），可一键编译运行
        </p>
      </div>
      {examples.map((entity) => {
        const open = openId === entity.id;
        const files = sources[entity.id];
        return (
          <motion.div
            key={entity.id}
            whileHover={{ y: -2 }}
            className="my-5 rounded-card bg-surface p-5 shadow-card ring-1 ring-accent/25"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="flex items-center gap-2 font-medium text-accent">
                  <BookMarked className="size-6 shrink-0" /> 官方示例 · {entity.title}
                </p>
                <p className="mt-1.5 text-[22px] leading-relaxed text-fg/80">
                  {entity.purpose}
                </p>
                {entity.note && (
                  <p className="mt-2 text-[18px] text-muted">{entity.note}</p>
                )}
                <p className="mt-2 font-mono text-[18px] text-muted">{entity.source_dir}/</p>
              </div>
              <div className="flex shrink-0 flex-col items-stretch gap-2">
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={() => onLaunch(entity.id)}
                  className="flex items-center justify-center gap-1.5 rounded-xl bg-accent px-4 py-2.5 text-[20px] font-medium text-on-accent shadow-card transition-colors hover:bg-accent/90"
                >
                  <Play className="size-5" /> 编译并运行
                </motion.button>
                <button
                  onClick={() => toggle(entity.id)}
                  className="flex items-center justify-center gap-1 rounded-xl px-4 py-2 text-[18px] text-accent ring-1 ring-accent/40 transition-colors hover:bg-accent/10"
                >
                  {open ? (
                    <><ChevronUp className="size-4" /> 收起源码</>
                  ) : (
                    <><ChevronDown className="size-4" /> 查看源码</>
                  )}
                </button>
              </div>
            </div>
            {open && (
              <div className="mt-4 space-y-4">
                {files === "error" && (
                  <p className="text-[20px] text-muted">
                    源码读取失败——浏览器预览下请在应用内打开。
                  </p>
                )}
                {Array.isArray(files) &&
                  files.map((file) => (
                    <div key={file.path} className="overflow-hidden rounded-card shadow-card ring-1 ring-line">
                      <div className="bg-bg-2 px-4 py-1.5 ring-1 ring-line">
                        <span className="font-mono text-[20px] font-medium text-accent">{file.path}</span>
                      </div>
                      <pre className="max-h-96 overflow-auto bg-[#F6F6F6] p-4 font-mono text-[20px] leading-relaxed text-[#555555]">
                        <code
                          className="hljs"
                          dangerouslySetInnerHTML={{
                            __html: highlightCode(file.content, "cpp"),
                          }}
                        />
                      </pre>
                    </div>
                  ))}
              </div>
            )}
          </motion.div>
        );
      })}
    </section>
  );
}
