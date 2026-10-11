import { useEffect, useMemo, useState, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";
import { CircleAlert } from "lucide-react";
import { highlightCode } from "./highlight";

/**
 * 官方节页渲染器：读段落快照 JSON（scripts/sync_upstream.py 生成）。
 * - 原文段落保留官方内联格式（粗体/斜体/行内代码/链接，受限 markdown）
 * - 代码块逐字照录（应用 ADR 0002：代码不翻译不改写）
 * - figure 渲染官方图片；key 段落重点强调；划词即查；英译训练模式
 * - 阅读单元优先按 PO 翻译单元分组（应用 ADR 0005，scripts/align_po.py 对齐）；
 *   未对齐的段按词数兜底聚合
 */

interface SnapshotBlock {
  type: "para" | "listitem" | "code" | "heading" | "figure";
  text: string;
  sha: string;
  zh?: string | null;
  ref?: string | null;
  file?: string | null;
  source_url?: string | null;
  /** 有序列表项的编号前缀（"1."）；variablelist 项为 term 原文 */
  marker?: string;
  /** 提示框类型（note/tip/warning/important/caution），来自官网 admonition */
  admonition?: string;
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

/** PO 翻译单元（content/po-units/<章>.json，scripts/align_po.py 生成）：
 *  官网 PO 的一条翻译单元 ↔ 本节连续若干段落；id 锚定首段 sha，
 *  与「看懂了」的 unitSha、自译存储键同口径（应用 ADR 0005）。 */
export interface PoUnit {
  id: string;
  shas: string[];
  zh: string | null;
}

/** 标注数据（content/vocab.json，App 启动时注入）。 */
export interface VocabEntry {
  term: string;
  pos?: string;
  cn: string;
  note?: string;
  example?: string;
  example_cn?: string;
  /** 编程领域术语：不在正文标注，集中到术语附注 */
  domain?: boolean;
}
export interface PatternEntry {
  pattern: string;
  cn: string;
}
/** 词族映射：变体（derived/derives/…）→ 基词。同族共用认识状态。 */
const TERM_LOOKUP = new Map<
  string,
  { kind: "vocab" | "pattern"; entry: VocabEntry & PatternEntry; base: string }
>();

function familyVariants(term: string): string[] {
  const variants = [term];
  if (!term.includes(" ")) {
    variants.push(term + "s");
    if (/(?:s|x|ch|sh)$/.test(term)) variants.push(term + "es");
    if (/e$/.test(term)) variants.push(term + "d");
    else variants.push(term + "ed");
    if (/[^wxy]$/.test(term)) variants.push(term + "ing");
    if (/e$/.test(term)) variants.push(term.slice(0, -1) + "ing");
    variants.push(term + "ly");
  }
  return [...new Set(variants)];
}

export function setAnnotationData(vocab: VocabEntry[], patterns: PatternEntry[]) {
  TERM_LOOKUP.clear();
  // 正文只标注普通疑难词；编程领域术语集中到「术语附注」（应用 ADR 0002 的门槛约定）
  for (const v of vocab) {
    if (v.domain) continue;
    for (const variant of familyVariants(v.term))
      TERM_LOOKUP.set(variant.toLowerCase(), {
        kind: "vocab",
        entry: v as VocabEntry & PatternEntry,
        base: v.term,
      });
  }
  for (const pt of patterns)
    TERM_LOOKUP.set(pt.pattern.toLowerCase(), {
      kind: "pattern",
      entry: pt as VocabEntry & PatternEntry,
      base: pt.pattern,
    });
}

export function buildAnnotationMatcher() {
  const terms = [...TERM_LOOKUP.keys()];
  if (!terms.length) {
    annotationMatcher = null;
    return;
  }
  const escaped = terms
    .sort((a, b) => b.length - a.length)
    .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  annotationMatcher = new RegExp(`\\b(?:${escaped.join("|")})\\b`, "gi");
}

/** 段内换行是 DocBook 源的排版产物：折叠为空格，按页面宽度自由断行。 */
const flow = (s: string) => s.replace(/\s*\n\s*/g, " ");

function splitSentences(text: string, lang: "en" | "zh"): string[] {
  const parts =
    lang === "en"
      ? text.replace(/\s*\n\s*/g, " ").split(/(?<=[.!?])\s+/)
      : text.split(/(?<=[。！？；])/);
  return parts.map((s) => s.trim()).filter(Boolean);
}

let annotationMatcher: RegExp | null = null;

function AnnotatedTerm({
  kind,
  display,
  entry,
}: {
  kind: "vocab" | "pattern";
  display: string;
  entry: VocabEntry & PatternEntry;
}) {
  const [open, setOpen] = useState(false);
  const isVocab = kind === "vocab";
  const pos = isVocab ? (entry as VocabEntry).pos : undefined;
  const note = (entry as VocabEntry).note || "";
  return (
    <span className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        className="cursor-help text-left font-serif underline decoration-dotted decoration-accent/50 underline-offset-4"
      >
        {display}
      </button>
      {open && (
        <span className="absolute left-0 top-full z-40 mt-2 block w-72 rounded-xl bg-white p-4 text-left shadow-card ring-1 ring-line">
          <span className="block font-serif text-[24px] font-semibold text-fg">
            {display}
            {pos && <span className="ml-2 text-[20px] italic text-muted">{pos}</span>}
          </span>
          <span className="mt-1 block text-[22px] text-accent-deep">{entry.cn}</span>
          {note && (
            <span className="mt-1 block text-[20px] leading-relaxed text-muted">{note}</span>
          )}
          {entry.example && <ExampleArea curated={{ en: entry.example, cn: entry.example_cn ?? "" }} />}
        </span>
      )}
    </span>
  );
}

function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern =
    /\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`|\[([^\]]+)\]\(([^)]*)\)/g;
  let cursor = 0;
  let match: RegExpExecArray | null;
  let key = 0;
  const pushPlain = (raw: string) => {
    if (!annotationMatcher) {
      nodes.push(raw);
      return;
    }
    let last = 0;
    let m: RegExpExecArray | null;
    annotationMatcher.lastIndex = 0;
    while ((m = annotationMatcher.exec(raw)) !== null) {
      if (m.index > last) nodes.push(raw.slice(last, m.index));
      const hit = TERM_LOOKUP.get(m[0].toLowerCase());
      if (hit) {
        nodes.push(
          <AnnotatedTerm
            key={`ann-${key++}`}
            kind={hit.kind}
            display={m[0]}
            entry={hit.entry}
          />,
        );
      } else {
        nodes.push(m[0]);
      }
      last = m.index + m[0].length;
    }
    if (last < raw.length) nodes.push(raw.slice(last));
  };
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) pushPlain(text.slice(cursor, match.index));
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
      // 官网内部链接（linkend → # 锚点）：应用有自己的左侧目录导航，
      // 锚点无处跳转，降级为不可点的强调文本，语义（引用关系）仍在
      if (match[5].startsWith("#")) {
        nodes.push(
          <span key={key++} className="font-semibold text-link">
            {match[4]}
          </span>,
        );
      } else {
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
    }
    cursor = pattern.lastIndex;
  }
  if (cursor < text.length) pushPlain(text.slice(cursor));
  return nodes;
}

function TranslatedText({ text }: { text: string }) {
  return <p className="text-[29px] leading-loose text-fg/90">{renderInline(flow(text))}</p>;
}

/** 学习者自译：官方快照待译/待复核/已有译文（订正候选）的段落都允许
 *  写下自己的译文并保存（learning.db my_translations，按单元锚点存，
 *  随进度库走）。保存空内容即清除。已有官方译文时官方译文照旧显示，
 *  自译只是并排的订正候选，不覆盖内容层（应用 ADR 0004、0005）。 */
function SelfTranslation({
  sha,
  text,
  onSave,
  hasOfficial = false,
  actionLabel = "✍️ 自己译",
}: {
  sha: string;
  text?: string;
  onSave: (sha: string, text: string) => void;
  /** 该位置已有官方译文（整条或单段）：空文本态只显示订正入口，不再标「待译」 */
  hasOfficial?: boolean;
  /** 入口按钮文案：待译段「✍️ 自己译」，官方译文段「✎ 我的译法」 */
  actionLabel?: string;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const start = () => {
    setDraft(text ?? "");
    setEditing(true);
  };
  if (editing) {
    return (
      <div className="mt-2 rounded-xl bg-surface p-4 ring-1 ring-accent/40">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={Math.min(10, Math.max(3, Math.ceil(draft.length / 40)))}
          autoFocus
          placeholder="写下你自己的译文…（清空后保存即删除）"
          className="w-full resize-y rounded-lg bg-surface-2 p-3 text-[24px] leading-relaxed text-fg outline-none ring-1 ring-line focus:ring-accent/50"
        />
        <div className="mt-2 flex gap-2">
          <button
            onClick={() => {
              onSave(sha, draft);
              setEditing(false);
            }}
            className="rounded-lg bg-accent px-4 py-1.5 text-[20px] font-medium text-on-accent transition-colors hover:bg-accent/90"
          >
            保存译文
          </button>
          <button
            onClick={() => setEditing(false)}
            className="rounded-lg border border-line px-4 py-1.5 text-[20px] text-muted transition-colors hover:text-fg"
          >
            取消
          </button>
        </div>
      </div>
    );
  }
  if (text) {
    return (
      <div className="mt-2 rounded-r-xl border-l-4 border-accent-deep/60 bg-accent-soft/40 py-3 pl-4 pr-3">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[20px] font-medium text-accent-deep">我的译文</span>
          <button
            onClick={start}
            className="text-[20px] text-muted transition-colors hover:text-accent"
          >
            ✎ 编辑
          </button>
        </div>
        <p className="mt-1 text-[27px] leading-loose text-fg/90">{renderInline(text)}</p>
      </div>
    );
  }
  if (hasOfficial) {
    return (
      <p className="mt-2">
        <button
          onClick={start}
          className="rounded-lg border border-dashed border-accent/40 px-3 py-0.5 text-[20px] text-accent transition-colors hover:bg-accent-soft"
        >
          {actionLabel}
        </button>
      </p>
    );
  }
  return (
    <p className="mt-2">
      <span className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-2 py-0.5 text-[20px] text-muted ring-1 ring-line">
        此段待译
      </span>
      <button
        onClick={start}
        className="ml-2 rounded-lg border border-dashed border-accent/40 px-3 py-0.5 text-[20px] text-accent transition-colors hover:bg-accent-soft"
      >
        {actionLabel}
      </button>
    </p>
  );
}

/** 自评行：看懂了 / 标记复习（或状态徽章）。 */
function RatingRow({
  sha,
  knownParas,
  hardParas,
  onRate,
}: {
  sha: string;
  knownParas: Set<string>;
  hardParas: Set<string>;
  onRate: (sha: string, understood: boolean) => void;
}) {
  const known = knownParas.has(sha);
  const hard = hardParas.has(sha);
  if (known || hard) {
    return (
      <span
        className={`mt-1 inline-block rounded-full px-2.5 py-0.5 text-[20px] ring-1 ${
          known
            ? "bg-green-50 text-green-700 ring-green-500/30"
            : "bg-amber-500/10 text-amber-700 ring-amber-500/30"
        }`}
      >
        {known ? "✓ 已读懂" : "📋 待复习"}
      </span>
    );
  }
  return (
    <div className="mt-1.5 flex gap-2">
      <button
        onClick={() => onRate(sha, true)}
        className="rounded-lg border border-green-500/40 px-3 py-1 text-[20px] text-green-700 transition-colors hover:bg-green-50"
      >
        👍 看懂了
      </button>
      <button
        onClick={() => onRate(sha, false)}
        className="rounded-lg border border-amber-500/40 px-3 py-1 text-[20px] text-amber-700 transition-colors hover:bg-amber-50"
      >
        📋 标记复习
      </button>
    </div>
  );
}

/** 例句区：只展示词表内置的精选例句（content/vocab.json），不联网拉取——
 *  在线词典接口慢且不稳定，卡住的是整个弹卡。 */
function ExampleArea({ curated }: { curated: { en: string; cn: string } }) {
  return (
    <div className="mt-2 border-t border-line pt-2">
      <p className="text-[20px] leading-relaxed text-fg/80">例句：{curated.en}</p>
      <p className="text-[20px] leading-relaxed text-muted">{curated.cn}</p>
    </div>
  );
}

/** 官方插图：走 Tauri command 通道读图（data URL，模块级缓存）。
 *
 * 与快照 JSON 同一条路：开发模式不依赖 vite 对仓库根的静态服务，
 * 发行包不受资源目录布局影响。command 不在（纯浏览器模式）时降级
 * 到 /content/ 静态路径；仍失败时显示占位框并报出文件名，不再静默裂图。 */
const FIGURE_CACHE = new Map<string, string>();

function FigureImage({ imageRef, alt }: { imageRef: string; alt: string }) {
  const [src, setSrc] = useState<string | null>(FIGURE_CACHE.get(imageRef) ?? null);
  const [staticFallback, setStaticFallback] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (FIGURE_CACHE.has(imageRef) || staticFallback) return;
    let cancelled = false;
    (async () => {
      try {
        const dataUrl = await invoke<string>("get_figure", { imageRef });
        FIGURE_CACHE.set(imageRef, dataUrl);
        if (!cancelled) setSrc(dataUrl);
      } catch {
        if (!cancelled) setStaticFallback(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [imageRef, staticFallback]);

  if (failed) {
    return (
      <div className="mx-auto flex max-w-3xl flex-col items-center gap-1 rounded-card border border-dashed border-line bg-surface-2 px-6 py-8 text-center">
        <span className="text-[22px] text-muted">图片加载失败</span>
        <span className="font-mono text-[20px] text-muted/70">{imageRef}</span>
      </div>
    );
  }
  return (
    <img
      src={src ?? (staticFallback ? `/content/${imageRef}` : undefined)}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
      className="mx-auto max-w-3xl rounded-card bg-white p-3 shadow-card ring-1 ring-line"
    />
  );
}

/** 官网 admonition 的提示框样式（应用配色体系内）。 */
const ADMONITION_STYLE: Record<string, { icon: string; label: string; box: string; text: string }> = {
  note: { icon: "ℹ️", label: "说明", box: "border-blue-500/50 bg-blue-50/70", text: "text-blue-700" },
  tip: { icon: "💡", label: "技巧", box: "border-green-500/50 bg-green-50/70", text: "text-green-700" },
  warning: { icon: "⚠️", label: "警告", box: "border-amber-500/60 bg-amber-50/70", text: "text-amber-700" },
  important: { icon: "❗", label: "重要", box: "border-violet-500/50 bg-violet-50/70", text: "text-violet-700" },
  caution: { icon: "🚫", label: "注意", box: "border-red-500/50 bg-red-50/70", text: "text-red-700" },
};

/** 阅读单元：优先按 PO 翻译单元分组（unit），无映射的段按词数兜底聚合。 */
function ReadUnit({
  blocks,
  unit,
  hidden,
  sentenceMode,
  knownParas,
  hardParas,
  myTranslations,
  onSaveMyTranslation,
  onRevealAll,
  onRate,
}: {
  blocks: SnapshotBlock[];
  /** PO 翻译单元；未对齐的兜底组没有 */
  unit?: PoUnit;
  hidden: boolean;
  sentenceMode: boolean;
  knownParas: Set<string>;
  hardParas: Set<string>;
  myTranslations: Record<string, string>;
  onSaveMyTranslation: (sha: string, text: string) => void;
  onRevealAll: () => void;
  onRate: (sha: string, understood: boolean) => void;
}) {
  const unitSha = blocks[0].sha; // 整个单元一次「看懂了」；多段 PO 单元即其首段
  const unitKnown = knownParas.has(unitSha);
  // 多段 PO 单元：译文按单元整条呈现（官方整条 msgstr / 单元级自译），
  // 段级不再逐段显示译文（应用 ADR 0005）
  const isMulti = !!unit && unit.shas.length > 1;
  const zhOf = (block: SnapshotBlock) => {
    if (block.zh) {
      const zhBody = sentenceMode ? (
        (() => {
          const enSents = splitSentences(flow(block.text), "en");
          const zhSents = splitSentences(block.zh, "zh");
          const rows: { en: string; zh?: string }[] = enSents.map((s) => ({ en: s }));
          zhSents.forEach((s, i) => {
            if (rows[i]) rows[i].zh = s;
            else rows.push({ en: "", zh: s });
          });
          return (
            <div className="mt-1 divide-y divide-line/60">
              {rows.map((row, i) => (
                <div key={i} className="py-1">
                  {row.en && (
                    <p className="font-serif text-[24px] leading-relaxed text-fg/60">
                      {renderInline(row.en)}
                    </p>
                  )}
                  {row.zh && (
                    <p className="text-[27px] leading-loose text-fg/90">{renderInline(row.zh)}</p>
                  )}
                </div>
              ))}
            </div>
          );
        })()
      ) : (
        <TranslatedText text={block.zh} />
      );
      // 官方译文照旧显示；学习者的订正候选并排其下，不覆盖内容层（应用 ADR 0004）
      return (
        <>
          {zhBody}
          <SelfTranslation
            sha={block.sha}
            text={myTranslations[block.sha]}
            onSave={onSaveMyTranslation}
            hasOfficial
            actionLabel="✎ 我的译法"
          />
        </>
      );
    }
    if (block.stale_from) {
      return (
        <>
          <p className="my-2 text-[20px] text-amber-700">以下为原文变更前的旧译文，待复核：</p>
          <TranslatedText text={block.stale_from} />
          <p className="mt-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[20px] text-amber-700 ring-1 ring-amber-500/30">
              原文已更新 · 译文待复核 <CircleAlert className="size-5" />
            </span>
          </p>
          <SelfTranslation
            sha={block.sha}
            text={myTranslations[block.sha]}
            onSave={onSaveMyTranslation}
          />
        </>
      );
    }
    return (
      <SelfTranslation
        sha={block.sha}
        text={myTranslations[block.sha]}
        onSave={onSaveMyTranslation}
      />
    );
  };

  return (
    <div className="my-6">
      {blocks.map((block) => {
        const isKnown = unitKnown;
        if (block.type === "listitem") {
          const marker = block.marker ? (
            // marker 是官网原文的纯文本（编号或 term），不参与 markdown 解析
            <span className="mr-1.5 inline-block min-w-8 font-semibold text-accent-deep">
              {block.marker}
            </span>
          ) : (
            <span className="mr-1.5">•</span>
          );
          return (
            <div key={block.sha} className="mb-3">
              <span
                className={`block rounded-lg px-2 py-1 font-serif text-[28px] leading-relaxed ${
                  isKnown ? "bg-green-50/80 text-fg/55" : "text-fg/60"
                }`}
              >
                {marker}
                {renderInline(flow(block.text))}
              </span>
              {/* 三种译态（官方译文/旧译文待复核/待译）都交 zhOf 统一处理；
                  多段 PO 单元的译文按单元整条呈现，段级不显示 */}
              {!hidden && !isMulti && (
                <div className="pl-5">{zhOf(block)}</div>
              )}
            </div>
          );
        }
        if (block.admonition) {
          const style = ADMONITION_STYLE[block.admonition] ?? ADMONITION_STYLE.note;
          return (
            <div
              key={block.sha}
              className={`my-5 rounded-r-xl border-l-4 px-5 py-3 ${style.box} ${
                isKnown ? "opacity-60" : ""
              }`}
            >
              <span className={`flex items-center gap-1.5 text-[20px] font-medium ${style.text}`}>
                {style.icon} {style.label}
              </span>
              <p className="font-serif text-[28px] leading-relaxed text-fg/70">
                {renderInline(flow(block.text))}
              </p>
              {!hidden && !isMulti && zhOf(block)}
            </div>
          );
        }
        return (
          <div key={block.sha} className="my-5">
            <blockquote
              className={`border-l-4 py-4 pl-5 pr-4 font-serif text-[28px] leading-relaxed ${
                block.status === "stale"
                  ? "border-amber-500/70 bg-surface-2 text-fg/60"
                  : isKnown
                    ? "border-green-500/60 bg-green-50/70 text-fg/55"
                    : block.key
                      ? "border-accent bg-accent-soft/60 text-fg/60"
                      : "border-accent/50 bg-surface-2 text-fg/60"
              }`}
            >
              <p>{renderInline(flow(block.text))}</p>
              {block.key && (
                <span className="mt-2 block text-[20px] font-medium not-italic text-accent">
                  ★ 本节重点
                </span>
              )}
            </blockquote>
            {!hidden && !isMulti && zhOf(block)}
          </div>
        );
      })}
      {!hidden && isMulti && (
        <div className="mt-3">
          {unit.zh ? <TranslatedText text={unit.zh} /> : null}
          <SelfTranslation
            sha={unitSha}
            text={myTranslations[unitSha]}
            onSave={onSaveMyTranslation}
            hasOfficial={!!unit.zh}
            actionLabel={unit.zh ? "✎ 我的译法" : "✍️ 自己译"}
          />
        </div>
      )}
      {!hidden && (
        <RatingRow
          sha={unitSha}
          knownParas={knownParas}
          hardParas={hardParas}
          onRate={onRate}
        />
      )}
      {hidden && (
        <button
          onClick={onRevealAll}
          className="rounded-lg border border-dashed border-line px-5 py-2 text-[20px] text-muted transition-colors hover:border-accent/40 hover:text-accent"
        >
          显示译文（{blocks.filter((b) => b.zh).length} 段）
        </button>
      )}
    </div>
  );
}

/** 阅读单元分组：优先按 PO 翻译单元（应用 ADR 0005，官网口径）；
 *  未对齐的段按词数兜底聚合。标题/代码/图打断。 */
type RenderGroup =
  | { kind: "heading" | "code" | "figure"; blocks: SnapshotBlock[] }
  | { kind: "read"; blocks: SnapshotBlock[]; unit?: PoUnit };

/** 词数：英文按空格分词，CJK 每字记一词。 */
function wordCount(text: string): number {
  return (
    (text.match(/[A-Za-z0-9]+/g) || []).length +
    (text.match(/[一-鿿]/g) || []).length
  );
}

function groupBlocks(
  blocks: SnapshotBlock[],
  unitLimit: number,
  unitOf: Map<string, PoUnit>,
): RenderGroup[] {
  const groups: RenderGroup[] = [];
  let pendingWords = 0;
  let i = 0;
  while (i < blocks.length) {
    const block = blocks[i];
    if (block.type === "para" || block.type === "listitem") {
      const unit = unitOf.get(block.sha);
      // PO 单元由首段触发整组消费；各段必须紧邻（映射过期则放弃该组走兜底）
      if (unit && unit.id === block.sha) {
        const segs = blocks.slice(i, i + unit.shas.length);
        if (segs.length === unit.shas.length && segs.every((b, k) => b.sha === unit.shas[k])) {
          groups.push({ kind: "read", blocks: segs, unit });
          i += segs.length;
          pendingWords = 0;
          continue;
        }
      }
      if (unit) {
        // 单元的非首段（首段没能成组）：独立成组，不混入兜底聚合
        groups.push({ kind: "read", blocks: [block], unit });
        i += 1;
        pendingWords = 0;
        continue;
      }
      const last = groups[groups.length - 1];
      if (last?.kind === "read" && !last.unit && pendingWords < unitLimit) {
        last.blocks.push(block);
        pendingWords += wordCount(block.text);
      } else {
        groups.push({ kind: "read", blocks: [block] });
        pendingWords = wordCount(block.text);
      }
      i += 1;
      continue;
    }
    groups.push({ kind: block.type, blocks: [block] });
    i += 1;
  }
  return groups;
}

export function PageView({
  chapterId,
  pageId,
  zhHidden,
  sentenceMode,
  unitWords,
  knownParas,
  hardParas,
  myTranslations,
  onSaveMyTranslation,
  onRate,
  optional,
}: {
  chapterId: string;
  pageId: string;
  zhHidden: boolean;
  sentenceMode: boolean;
  /** 一个翻译单元的目标词数（设置「按多少词划分翻译单元」） */
  unitWords: number;
  knownParas: Set<string>;
  hardParas: Set<string>;
  /** 学习者自译（段落 sha → 译文），只作用于待译/待复核段落 */
  myTranslations: Record<string, string>;
  onSaveMyTranslation: (sha: string, text: string) => void;
  onRate: (sha: string, understood: boolean) => void;
  /** 快照不存在时静默不渲染（参考层的多节条目没有单页快照，属预期） */
  optional?: boolean;
}) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [revealed, setRevealed] = useState<Set<string>>(new Set());
  /** 当前节各段所属的 PO 翻译单元（sha → unit）；null = 未加载或未对齐 */
  const [unitOf, setUnitOf] = useState<Map<string, PoUnit> | null>(null);
  const reveal = (sha: string) => setRevealed((prev) => new Set(prev).add(sha));

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const ingest = (pages: Record<string, PoUnit[]> | null) => {
        const map = new Map<string, PoUnit>();
        for (const u of pages?.[pageId] ?? []) for (const sha of u.shas) map.set(sha, u);
        if (!cancelled) setUnitOf(map);
      };
      try {
        ingest(await invoke<Record<string, PoUnit[]> | null>("get_po_units", { chapterId }));
      } catch {
        // 纯浏览器模式：读静态文件；读不到视为该章未对齐
        try {
          const response = await fetch(`/content/po-units/${chapterId}.json`);
          if (!response.ok) throw new Error(String(response.status));
          ingest((await response.json()) as Record<string, PoUnit[]>);
        } catch {
          if (!cancelled) setUnitOf(null);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [chapterId, pageId]);

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

  const groups = useMemo(
    () => (snapshot ? groupBlocks(snapshot.blocks, unitWords, unitOf ?? new Map()) : []),
    [snapshot, unitWords, unitOf],
  );

  if (error) return optional ? null : <p className="text-sm text-red-700">{error}</p>;
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
                {renderInline(flow(group.blocks[0].text))}
              </h3>
            );
          case "code": {
            const block = group.blocks[0];
            return (
              <figure key={index} className="my-5">
                <div className="overflow-hidden rounded-card ring-1 ring-line">
                  <div className="flex items-center justify-between bg-bg-2 px-4 py-1.5">
                    <span className="font-mono text-[20px] font-medium text-accent">
                      {block.file ?? "cpp"}
                    </span>
                    {block.source_url && (
                      <a
                        href={block.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[20px] text-link hover:underline"
                      >
                        完整源码 ↗
                      </a>
                    )}
                  </div>
                  <pre className="overflow-x-auto bg-[#F6F6F6] p-5 font-mono text-[20px] leading-relaxed text-[#555555]">
                    <code
                      className="hljs"
                      dangerouslySetInnerHTML={{
                        // 节页源码块全部是教程 C++（提取层保证），语言固定传 cpp
                        __html: highlightCode(block.text, "cpp"),
                      }}
                    />
                  </pre>
                </div>
              </figure>
            );
          }
          case "figure": {
            const block = group.blocks[0];
            return (
              <figure key={index} className="my-6">
                {block.ref && <FigureImage imageRef={block.ref} alt={block.text} />}
                {/* 游离 screenshot 没有题注（官网行为），不渲染空「图 ·」行 */}
                {block.text && (
                  <figcaption className="mt-2 text-center text-[20px] text-muted">
                    图 · {flow(block.text)}
                  </figcaption>
                )}
              </figure>
            );
          }
          case "read": {
            const unitKey = `read:${group.blocks[0].sha}`;
            const hidden = zhHidden && !revealed.has(unitKey);
            return (
              <ReadUnit
                key={index}
                blocks={group.blocks}
                unit={group.unit}
                hidden={hidden}
                sentenceMode={sentenceMode}
                knownParas={knownParas}
                hardParas={hardParas}
                myTranslations={myTranslations}
                onSaveMyTranslation={onSaveMyTranslation}
                onRevealAll={() => reveal(unitKey)}
                onRate={onRate}
              />
            );
          }
        }
      })}
    </article>
  );
}
