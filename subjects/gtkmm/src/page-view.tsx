import { useEffect, useMemo, useState, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";
import { CircleAlert } from "lucide-react";

/** 标注数据（content/vocab.json，App 启动时注入）。 */
export interface VocabEntry {
  term: string;
  pos?: string;
  cn: string;
  note?: string;
}
export interface PatternEntry {
  pattern: string;
  cn: string;
}
/** 词族映射：变体（derived/derives/…）→ 基词。同族共用认识状态。 */
const TERM_LOOKUP = new Map<string, { kind: "vocab" | "pattern"; entry: VocabEntry & PatternEntry; base: string }>();

function familyVariants(term: string): string[] {
  const variants = [term];
  if (!term.includes(" ")) {
    variants.push(term + "s");
    if (/(?:s|x|ch|sh)$/.test(term)) variants.push(term + "es");
    if (/e$/.test(term)) variants.push(term + "d");
    else variants.push(term + "ed", term.slice(-1) + "ed" === term + "ed" ? term + "ed" : term + term.slice(-1) + "ed");
    if (/[^wxy]$/.test(term)) variants.push(term + "ing");
    if (/e$/.test(term)) variants.push(term.slice(0, -1) + "ing");
    variants.push(term + "ly");
  }
  return [...new Set(variants)];
}

export function setAnnotationData(vocab: VocabEntry[], patterns: PatternEntry[]) {
  TERM_LOOKUP.clear();
  for (const v of vocab)
    for (const variant of familyVariants(v.term))
      TERM_LOOKUP.set(variant.toLowerCase(), { kind: "vocab", entry: v as VocabEntry & PatternEntry, base: v.term });
  for (const pt of patterns)
    TERM_LOOKUP.set(pt.pattern.toLowerCase(), { kind: "pattern", entry: pt as VocabEntry & PatternEntry, base: pt.pattern });
}

/** 词汇状态（learning.db 派生）：known=已认识；unknown=生词。 */
export interface WordStatus {
  known: Set<string>;
  unknown: Set<string>;
}

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

/** 分句：英文按 .!?，中文按 。！？；保留标点（逐句对照用）。 */
function splitSentences(text: string, lang: "en" | "zh"): string[] {
  const parts = lang === "en"
    ? text.replace(/\s*\n\s*/g, " ").split(/(?<=[.!?])\s+/)
    : text.split(/(?<=[。！？；])/);
  return parts.map((s) => s.trim()).filter(Boolean);
}

/** 译文揭示控件：训练模式下默认折叠，点击揭示并自评（看懂了/标记复习）。 */
function ZhReveal({
  sha,
  en,
  zh,
  sentenceMode,
  hidden,
  known,
  hard,
  onReveal,
  onRate,
}: {
  sha: string;
  en: string;
  zh: string;
  sentenceMode: boolean;
  hidden: boolean;
  known: boolean;
  hard: boolean;
  onReveal: () => void;
  onRate: (sha: string, understood: boolean) => void;
}) {
  if (!hidden) {
    const rated = known || hard;
    const pairs = sentenceMode
      ? (() => {
          const enSents = splitSentences(en, "en");
          const zhSents = splitSentences(zh, "zh");
          const rows: { en: string; zh?: string }[] = enSents.map((s) => ({ en: s }));
          zhSents.forEach((s, i) => {
            if (rows[i]) rows[i].zh = s;
            else rows.push({ en: "", zh: s });
          });
          return rows;
        })()
      : null;
    return (
      <div>
        {pairs ? (
          <div className="divide-y divide-line/60">
            {pairs.map((row, i) => (
              <div key={i} className="py-1.5">
                {row.en && <p className="font-serif text-[24px] leading-relaxed text-fg/60">{renderInline(row.en)}</p>}
                {row.zh && <p className="text-[27px] leading-loose text-fg/90">{renderInline(row.zh)}</p>}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[29px] leading-loose text-fg/90">{renderInline(flow(zh))}</p>
        )}
        {rated ? (
          <span
            className={`mt-1 inline-block rounded-full px-2.5 py-0.5 text-[20px] ring-1 ${
              known
                ? "bg-green-50 text-green-700 ring-green-500/30"
                : "bg-amber-500/10 text-amber-700 ring-amber-500/30"
            }`}
          >
            {known ? "✓ 已读懂" : "📋 待复习"}
          </span>
        ) : (
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
        )}
      </div>
    );
  }
  return (
    <button
      onClick={onReveal}
      className="rounded-lg border border-dashed border-line px-4 py-1.5 text-[20px] text-muted transition-colors hover:border-accent/40 hover:text-accent"
    >
      显示译文
    </button>
  );
}

/** 段内换行是 DocBook 源的排版产物：折叠为空格，按页面宽度自由断行。 */
const flow = (s: string) => s.replace(/\s*\n\s*/g, " ");

function AnnotatedTerm({
  kind,
  term,
  display,
  entry,
  status,
  onRate,
}: {
  kind: "vocab" | "pattern";
  term: string;
  display: string;
  entry: VocabEntry | PatternEntry;
  status: "known" | "unknown" | undefined;
  onRate: (term: string, known: boolean) => void;
}) {
  const [open, setOpen] = useState(false);
  const isVocab = kind === "vocab";
  const underline = status === "unknown"
    ? "underline decoration-solid decoration-amber-500 decoration-2 underline-offset-4"
    : status === "known"
      ? "underline decoration-dotted decoration-green-600/60 underline-offset-4"
      : "underline decoration-dotted decoration-accent/50 underline-offset-4";
  const pos = isVocab ? (entry as VocabEntry).pos : undefined;
  const note = (entry as VocabEntry).note || "";
  return (
    <span className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        className={`${underline} cursor-help text-left font-serif`}
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
          {note && <span className="mt-1 block text-[20px] leading-relaxed text-muted">{note}</span>}
          <span className="mt-3 flex gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRate(term, true);
                setOpen(false);
              }}
              className={`rounded-lg border px-3 py-1 text-[20px] ${
                status === "known"
                  ? "border-green-500 bg-green-50 text-green-700"
                  : "border-green-500/40 text-green-700 hover:bg-green-50"
              }`}
            >
              认识
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRate(term, false);
                setOpen(false);
              }}
              className={`rounded-lg border px-3 py-1 text-[20px] ${
                status === "unknown"
                  ? "border-amber-500 bg-amber-50 text-amber-700"
                  : "border-amber-500/40 text-amber-700 hover:bg-amber-50"
              }`}
            >
              不认识
            </button>
          </span>
        </span>
      )}
    </span>
  );
}

/** 受限行内 markdown → JSX：**粗**、*斜*、`代码`、[文字](链接)。 */
let annotationMatcher: RegExp | null = null;
let wordStatus: WordStatus | undefined;
let onRateWord: ((term: string, known: boolean) => void) | null = null;
export function setWordStatus(status: WordStatus | undefined) {
  wordStatus = status;
}
export function setOnRateWord(fn: (term: string, known: boolean) => void) {
  onRateWord = fn;
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
            term={hit.base}
            display={m[0]}
            entry={hit.entry}
            status={wordStatus?.known.has(hit.base)
              ? "known"
              : wordStatus?.unknown.has(hit.base)
                ? "unknown"
                : undefined}
            onRate={onRateWord ?? (() => {})}
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
  if (cursor < text.length) pushPlain(text.slice(cursor));
  return nodes;
}

function TranslatedText({ text }: { text: string }) {
  return (
    <>
      {/* 段内换行是 DocBook 源的排版产物：折叠为空格，按页面宽度自由断行 */}
      <p className="leading-loose text-fg/90">
        {renderInline(text.replace(/\s*\n\s*/g, " "))}
      </p>
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
  zhHidden,
  sentenceMode,
  knownParas,
  hardParas,
  onRate,
}: {
  chapterId: string;
  pageId: string;
  /** 英译训练模式：中文默认隐藏，点击揭示 */
  zhHidden: boolean;
  /** 逐句对照：揭示译文后按句交错显示 */
  sentenceMode: boolean;
  /** 已自评「看懂了」的段落 sha */
  knownParas: Set<string>;
  /** 被标记「需复习」的段落 sha */
  hardParas: Set<string>;
  onRate: (sha: string, understood: boolean) => void;
}) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [revealed, setRevealed] = useState<Set<string>>(new Set());
  const reveal = (sha: string) =>
    setRevealed((prev) => new Set(prev).add(sha));

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
                {renderInline(flow(group.blocks[0].text))}
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
                  图 · {flow(block.text)}
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
                      <span className="font-serif text-[28px] leading-relaxed text-fg/60">
                        • {renderInline(flow(block.text))}
                      </span>
                      {block.zh && (
                        <span className="pl-5">
                          <ZhReveal
                            sha={block.sha}
                            en={flow(block.text)}
                            zh={block.zh}
                            sentenceMode={sentenceMode}
                            hidden={zhHidden && !revealed.has(block.sha)}
                            known={knownParas.has(block.sha)}
                            hard={hardParas.has(block.sha)}
                            onReveal={() => reveal(block.sha)}
                            onRate={onRate}
                          />
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
                  className={`border-l-4 bg-surface-2 py-4 pl-5 pr-4 font-serif text-[28px] leading-relaxed text-fg/60 ${
                    stale
                      ? "border-amber-500/70"
                      : block.key
                        ? "border-accent bg-accent-soft/60"
                        : "border-accent/50"
                  }`}
                >
                  <p>{renderInline(block.text.replace(/\s*\n\s*/g, " "))}</p>
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
                    <ZhReveal
                      sha={block.sha}
                      en={flow(block.text)}
                      zh={block.zh}
                      sentenceMode={sentenceMode}
                      hidden={zhHidden && !revealed.has(block.sha)}
                      known={knownParas.has(block.sha)}
                      hard={hardParas.has(block.sha)}
                      onReveal={() => reveal(block.sha)}
                      onRate={onRate}
                    />
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
