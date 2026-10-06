import { useEffect, useMemo, useState, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";
import { CircleAlert } from "lucide-react";
import { highlightCode } from "./highlight";

/**
 * 官方节页渲染器：读段落快照 JSON（scripts/sync_upstream.py 生成）。
 * - 原文段落保留官方内联格式（粗体/斜体/行内代码/链接，受限 markdown）
 * - 代码块逐字照录（应用 ADR 0002：代码不翻译不改写）
 * - figure 渲染官方图片；key 段落重点强调；划词即查；英译训练模式
 * - 连续短文字段合并为一个「阅读单元」：一个显示译文按钮，减少点击负担
 */

interface SnapshotBlock {
  type: "para" | "listitem" | "code" | "heading" | "figure";
  text: string;
  sha: string;
  zh?: string | null;
  ref?: string | null;
  file?: string | null;
  source_url?: string | null;
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
  term,
  display,
  entry,
}: {
  kind: "vocab" | "pattern";
  term: string;
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
          {(entry.example || !/\s/.test(term)) && (
            <ExampleArea
              term={term}
              curated={
                entry.example
                  ? { en: entry.example, cn: entry.example_cn ?? "" }
                  : undefined
              }
            />
          )}
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
            term={hit.base}
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
  return <p className="text-[29px] leading-loose text-fg/90">{renderInline(flow(text))}</p>;
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

/** 例句区：词表精选例句优先；否则在线拉取（dictionaryapi.dev，模块级缓存）。 */
const EXAMPLE_CACHE = new Map<
  string,
  { phonetic?: string; examples: string[]; defs: string[] }
>();

function ExampleArea({
  term,
  curated,
}: {
  term: string;
  curated?: { en: string; cn: string };
}) {
  const [data, setData] = useState(EXAMPLE_CACHE.get(term.toLowerCase()) ?? null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (EXAMPLE_CACHE.has(term.toLowerCase()) || /\s/.test(term)) return;
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch(
          `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(term)}`,
        );
        if (!response.ok) throw new Error(String(response.status));
        const entries = await response.json();
        const phonetic =
          entries[0]?.phonetic ??
          entries[0]?.phonetics?.find((ph: { text?: string }) => ph.text)?.text;
        const examples: string[] = [];
        const defs: string[] = [];
        for (const meaning of entries[0]?.meanings ?? []) {
          for (const def of meaning.definitions ?? []) {
            if (def.example && examples.length < 2) examples.push(def.example);
            if (defs.length < 2) defs.push(`[${meaning.partOfSpeech}] ${def.definition}`);
          }
        }
        const payload = { phonetic, examples, defs };
        EXAMPLE_CACHE.set(term.toLowerCase(), payload);
        if (!cancelled) setData(payload);
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [term]);

  return (
    <div className="mt-2 border-t border-line pt-2">
      {curated && (
        <div className="mb-1">
          <p className="text-[20px] leading-relaxed text-fg/80">例句：{curated.en}</p>
          <p className="text-[20px] leading-relaxed text-muted">{curated.cn}</p>
        </div>
      )}
      {data?.examples.map((ex, i) => (
        <p key={i} className="font-serif text-[20px] italic leading-relaxed text-fg/75">
          {ex}
        </p>
      ))}
      {data?.phonetic && !curated && (
        <p className="font-mono text-[20px] text-muted">{data.phonetic}</p>
      )}
      {failed && !curated && (
        <p className="text-[20px] text-muted">例句需联网获取（当前不可用）。</p>
      )}
      {!curated && !data && !failed && <p className="text-[20px] text-muted">正在获取例句……</p>}
    </div>
  );
}

/** 阅读单元：连续短文字段合并（一个显示译文按钮），长段独立成单元。 */
function ReadUnit({
  blocks,
  hidden,
  sentenceMode,
  knownParas,
  hardParas,
  onRevealAll,
  onRate,
}: {
  blocks: SnapshotBlock[];
  hidden: boolean;
  sentenceMode: boolean;
  knownParas: Set<string>;
  hardParas: Set<string>;
  onRevealAll: () => void;
  onRate: (sha: string, understood: boolean) => void;
}) {
  const unitSha = blocks[0].sha; // 整个单元一次「看懂了」
  const unitKnown = knownParas.has(unitSha);
  const zhOf = (block: SnapshotBlock) => {
    if (block.zh) {
      if (sentenceMode) {
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
      }
      return <TranslatedText text={block.zh} />;
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
        </>
      );
    }
    return (
      <p className="mt-2">
        <span className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-2 py-0.5 text-[20px] text-muted ring-1 ring-line">
          此段待译
        </span>
      </p>
    );
  };

  return (
    <div className="my-6">
      {blocks.map((block) => {
        const isKnown = unitKnown;
        if (block.type === "listitem") {
          return (
            <div key={block.sha} className="mb-3">
              <span
                className={`block rounded-lg px-2 py-1 font-serif text-[28px] leading-relaxed ${
                  isKnown ? "bg-green-50/80 text-fg/55" : "text-fg/60"
                }`}
              >
                • {renderInline(flow(block.text))}
              </span>
              {!hidden && block.zh && (
                <div className="pl-5">{zhOf(block)}</div>
              )}
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
            {!hidden && zhOf(block)}
          </div>
        );
      })}
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

/** 阅读单元分组：连续文字块合并；长段（>280 字符）独立；标题/代码/图打断。 */
type RenderGroup =
  | { kind: "heading" | "code" | "figure"; blocks: SnapshotBlock[] }
  | { kind: "read"; blocks: SnapshotBlock[] };

/** 词数：英文按空格分词，CJK 每字记一词。 */
function wordCount(text: string): number {
  return (
    (text.match(/[A-Za-z0-9]+/g) || []).length +
    (text.match(/[一-鿿]/g) || []).length
  );
}

function groupBlocks(blocks: SnapshotBlock[]): RenderGroup[] {
  const groups: RenderGroup[] = [];
  let unitWords = 0;
  for (const block of blocks) {
    if (block.type === "para" || block.type === "listitem") {
      const last = groups[groups.length - 1];
      // 聚合到 ~100 词为一个阅读单元：一次「看懂了」
      if (last?.kind === "read" && unitWords < 100) {
        last.blocks.push(block);
        unitWords += wordCount(block.text);
      } else {
        groups.push({ kind: "read", blocks: [block] });
        unitWords = wordCount(block.text);
      }
      continue;
    }
    groups.push({ kind: block.type, blocks: [block] });
  }
  return groups;
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
  zhHidden: boolean;
  sentenceMode: boolean;
  knownParas: Set<string>;
  hardParas: Set<string>;
  onRate: (sha: string, understood: boolean) => void;
}) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [revealed, setRevealed] = useState<Set<string>>(new Set());
  const reveal = (sha: string) => setRevealed((prev) => new Set(prev).add(sha));

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
          case "read": {
            const unitKey = `read:${group.blocks[0].sha}`;
            const hidden = zhHidden && !revealed.has(unitKey);
            return (
              <ReadUnit
                key={index}
                blocks={group.blocks}
                hidden={hidden}
                sentenceMode={sentenceMode}
                knownParas={knownParas}
                hardParas={hardParas}
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
