import { Fragment, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";
import { mountArchivePanel, type ArchiveBlock } from "@athena/viz";

// 归档型应用的前端：左侧条目导航（按 guide_line 里的 [分组] 归类），右侧是条目的讲解块与归档面板。
// 课表来自共用壳的 load_curriculum（它已把 content/archive.json 接在末尾，ADR 0176）。
// 条目不判分、不计入进度，所以这里没有作答、掌握度、测验——不是遗漏。

type Block =
  | { type: "lead" | "prose"; text: string }
  | { type: "callout"; tone?: string; title?: string; text: string }
  | ArchiveBlock;

type Topic = {
  id: string;
  title: string;
  guide_line: string;
  outline?: Record<string, string>;
  lesson: { blocks: Block[] };
};

type Chapter = { id: string; title: string; summary: string; layer?: string; topics: Topic[] };
type Curriculum = { title?: string; tagline?: string; chapters: Chapter[] };
type AppInfo = { title: string; compiler: string };

const OUTLINE_LABELS: [string, string][] = [
  ["promise", "读完能做到"],
  ["pain", "为什么值得看"],
  ["model", "这份代码的结构"],
  ["scope", "范围"],
  ["judgment", "怎么判断"],
  ["landing", "落点"],
];

/** guide_line 以 “[组名] ” 开头则取组名，否则归“未分组”。 */
function groupOf(t: Topic): { group: string; line: string } {
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

function Lesson({ topic }: { topic: Topic }) {
  const outline = topic.outline ?? {};
  return (
    <article className="lesson">
      <h2>{topic.title}</h2>
      <p className="muted">{groupOf(topic).line}</p>
      {topic.lesson.blocks.map((b, i) => {
        if (b.type === "archive") return <ArchivePanel key={`${topic.id}:${i}`} block={b} />;
        if (b.type === "callout")
          return (
            <aside key={i} className="callout">
              {b.title && <strong>{b.title}</strong>}
              <p>{inline(b.text)}</p>
            </aside>
          );
        return (
          <p key={i} className={b.type === "lead" ? "lead" : undefined}>
            {inline(b.text)}
          </p>
        );
      })}
      <details className="outline">
        <summary>方向与边界</summary>
        <dl>
          {OUTLINE_LABELS.filter(([k]) => outline[k]).map(([k, label]) => (
            <div key={k}>
              <dt>{label}</dt>
              <dd>{outline[k]}</dd>
            </div>
          ))}
        </dl>
      </details>
    </article>
  );
}

export default function App() {
  const [info, setInfo] = useState<AppInfo | null>(null);
  const [cur, setCur] = useState<Curriculum | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setInfo(await invoke<AppInfo>("get_app_info"));
        setCur(await invoke<Curriculum>("load_curriculum"));
      } catch (e) {
        setError(
          `读取课表失败：${e}\n（不在 Athena 窗口里时没有 Tauri，请用 pnpm run tauri:dev 或 launcher open 启动，不要只开浏览器里的 Vite 页。）`,
        );
      }
    })();
  }, []);

  const topics = useMemo(() => (cur?.chapters ?? []).flatMap((c) => c.topics), [cur]);
  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    const map = new Map<string, Topic[]>();
    for (const t of topics) {
      if (q && !`${t.title} ${t.guide_line} ${t.id}`.toLowerCase().includes(q)) continue;
      const g = groupOf(t).group;
      map.set(g, [...(map.get(g) ?? []), t]);
    }
    return [...map.entries()];
  }, [topics, query]);

  const current = topics.find((t) => t.id === selected) ?? null;
  const chapter = cur?.chapters.find((c) => c.layer === "archive") ?? cur?.chapters[0];

  return (
    <div className="shell">
      <header className="topbar">
        <h1>{info?.title ?? "…"}</h1>
        <span className="muted">{cur?.tagline}</span>
        <span className="badge">历史归档 · 不计入进度</span>
      </header>
      {error && <pre className="error">{error}</pre>}
      <div className="body">
        <nav className="nav">
          <input
            className="search"
            placeholder={`在 ${topics.length} 个条目里搜索`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {groups.map(([g, ts]) => (
            <section key={g}>
              <h3>
                {g} <small>{ts.length}</small>
              </h3>
              {ts.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  className={t.id === selected ? "item on" : "item"}
                  onClick={() => setSelected(t.id)}
                >
                  {t.title}
                </button>
              ))}
            </section>
          ))}
          {!groups.length && !error && <p className="muted">没有匹配的条目。</p>}
        </nav>
        <main className="main">
          {current ? (
            <Lesson topic={current} />
          ) : (
            <div className="home">
              <h2>{chapter?.title ?? "历史归档"}</h2>
              <p>{chapter?.summary}</p>
              <p className="muted">从左侧选一个条目：原代码原样保留，点编号看批注，能运行的可以直接运行。</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
