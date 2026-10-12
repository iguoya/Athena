import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: false,
  theme: "neutral",
  flowchart: { useMaxWidth: false },
  state: { useMaxWidth: false },
  themeVariables: { fontSize: "18px" },
});

type Section = {
  role: "focus" | "compare" | "diagram" | "code";
  heading: string;
  body?: string;
  diagram?: string;
  code?: string;
};

type Question = {
  id: string;
  kind: string;
  stem: string;
  choices: string[];
  answer: number;
  explanation: string;
};

type Run = {
  id: string;
  label: string;
  primary?: boolean;
};

type Chapter = {
  id: string;
  exercise: string;
  title: string;
  lead: string;
  sections: Section[];
  questions: Question[];
  runs: Run[];
  files: string[];
};

const chapters = Object.values(
  import.meta.glob("../content/chapters/*.json", {
    eager: true,
    import: "default",
  }) as Record<string, Chapter>,
).sort((a, b) => a.exercise.localeCompare(b.exercise));

const sources = import.meta.glob(
  [
    "../exercise/**/*.{cc,hh,h}",
    "../exercise/**/CMakeLists.txt",
    "!../exercise/**/build/**",
  ],
  { eager: true, query: "?raw", import: "default" },
) as Record<string, string>;

function sourceText(relative: string): string | undefined {
  return sources[`../${relative}`];
}

const SCALE_KEY = "snake-ui-scale";
const SCALE_MIN = 0.8;
const SCALE_MAX = 1.6;

function clampScale(value: number) {
  const stepped = Math.round(value * 10) / 10;
  return Math.min(SCALE_MAX, Math.max(SCALE_MIN, stepped));
}

function readScale() {
  const raw = localStorage.getItem(SCALE_KEY);
  const value = raw === null ? 1 : Number(raw);
  return Number.isFinite(value) ? clampScale(value) : 1;
}

function applyScale(scale: number) {
  document.documentElement.style.fontSize = `${20 * scale}pt`;
  localStorage.setItem(SCALE_KEY, String(scale));
}

const THEMES = [
  { id: "paper", label: "纸色" },
  { id: "wood", label: "木色" },
  { id: "celadon", label: "青瓷" },
] as const;

type ThemeId = (typeof THEMES)[number]["id"];
const THEME_KEY = "snake-ui-theme";

function readTheme(): ThemeId {
  const raw = localStorage.getItem(THEME_KEY);
  return THEMES.some((item) => item.id === raw) ? (raw as ThemeId) : "paper";
}

function applyTheme(theme: ThemeId) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(THEME_KEY, theme);
}

applyTheme(readTheme());

const HUES = ["hue-window", "hue-grid", "hue-snake", "hue-state", "hue-polish"];

function kindClass(kind: string) {
  if (kind === "重点" || kind === "要点") return "key";
  if (kind === "难点") return "hard";
  if (kind === "考点") return "exam";
  return "";
}

function RichText({ text }: { text: string }) {
  const nodes: ReactNode[] = [];
  const pattern = /〔(重点|要点|难点|考点)〕([\s\S]*?)〔〕/g;
  let last = 0;
  let index = 0;
  for (const match of text.matchAll(pattern)) {
    const at = match.index ?? 0;
    if (at > last) nodes.push(text.slice(last, at));
    nodes.push(
      <mark key={index} className={`mark ${kindClass(match[1])}`}>
        {match[2]}
      </mark>,
    );
    index += 1;
    last = at + match[0].length;
  }
  if (last === 0) return text;
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

let diagramSeq = 0;

// 图按自然尺寸渲染（不缩进容器宽），点击进全屏：遮罩里用 <img> 隔离 svg 的 id 空间，
// 同一份源码两处展示互不串线。svg 是矢量，放大不失真。
function Diagram({ code }: { code: string }) {
  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");
  const [zoom, setZoom] = useState(false);
  const id = useRef(`diagram-${++diagramSeq}`);
  useEffect(() => {
    let alive = true;
    mermaid
      .render(id.current, code)
      .then(({ svg }) => {
        if (alive) {
          setSvg(svg);
          setError("");
        }
      })
      .catch((e) => {
        if (alive) setError(String(e));
      });
    return () => {
      alive = false;
    };
  }, [code]);
  if (error) {
    return (
      <div className="diagram-error">
        <p>这张图画不出来，源码如下：</p>
        <pre>{code}</pre>
      </div>
    );
  }
  const dataUrl = `data:image/svg+xml,${encodeURIComponent(svg)}`;
  return (
    <>
      <div className="diagram" title="点击放大">
        <div onClick={() => setZoom(true)} dangerouslySetInnerHTML={{ __html: svg }} />
      </div>
      {zoom ? (
        <div className="diagram-fullscreen" onClick={() => setZoom(false)}>
          <img src={dataUrl} alt="放大查看" />
          <p className="diagram-hint">点击任意处关闭</p>
        </div>
      ) : null}
    </>
  );
}

export default function App() {
  const [currentId, setCurrentId] = useState(chapters[0]?.id ?? "");
  const chapter = useMemo(
    () => chapters.find((item) => item.id === currentId) ?? chapters[0],
    [currentId],
  );
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [passed, setPassed] = useState<Set<string>>(() => new Set());
  const [file, setFile] = useState<string | null>(null);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [runNote, setRunNote] = useState("");
  const [scale, setScale] = useState(readScale);
  const [theme, setTheme] = useState(readTheme);

  useEffect(() => {
    applyScale(scale);
  }, [scale]);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (!(event.ctrlKey || event.metaKey) || event.altKey) {
        return;
      }
      if (event.key === "+" || event.key === "=") {
        event.preventDefault();
        setScale((current) => clampScale(current + 0.1));
      } else if (event.key === "-" || event.key === "_") {
        event.preventDefault();
        setScale((current) => clampScale(current - 0.1));
      } else if (event.key === "0") {
        event.preventDefault();
        setScale(1);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    invoke<string[]>("passed_questions")
      .then((ids) => setPassed(new Set(ids)))
      .catch(() => {
        // 浏览器里预览时没有进度库，标绿只跟着这一页的作答走。
      });
  }, []);

  if (!chapter) {
    return <p>还没有章节。</p>;
  }

  const shown = file ?? chapter.files[0];

  // 图与接口代码块全宽横幅渲染（图占一行、说明在图下方），文字讲解留在分栏里。
  const fullSections = chapter.sections.filter(
    (item) => item.role === "diagram" || item.role === "code",
  );
  const flowSections = chapter.sections.filter(
    (item) => item.role !== "diagram" && item.role !== "code",
  );

  function chapterDone(item: Chapter) {
    return item.questions.length > 0 && item.questions.every((question) => passed.has(question.id));
  }

  function openChapter(id: string) {
    setCurrentId(id);
    setAnswers({});
    setFile(null);
    setRunNote("");
  }

  async function choose(question: Question, index: number) {
    if (answers[question.id] !== undefined) {
      return;
    }
    setAnswers((prev) => ({ ...prev, [question.id]: index }));
    setPassed((prev) => {
      const next = new Set(prev);
      if (index === question.answer) {
        next.add(question.id);
      } else {
        next.delete(question.id);
      }
      return next;
    });
    try {
      await invoke("record_attempt", {
        functionId: question.id,
        correct: index === question.answer,
      });
    } catch {
      // 浏览器里预览时没有壳，作答仍留在这一页上。
    }
  }

  async function run(target: Run) {
    if (!("__TAURI_INTERNALS__" in window)) {
      setRunNote("浏览器里只能看讲解。要打开贪吃蛇窗口，请用启动器打开「贪吃蛇」。");
      return;
    }
    setRunningId(target.id);
    setRunNote(`正在编译并打开${target.label}…`);
    try {
      const message = await invoke<string>("run_chapter", { id: target.id });
      setRunNote(message);
    } catch (error) {
      setRunNote(typeof error === "string" ? error : "这一章没有启动起来。");
    } finally {
      setRunningId(null);
    }
  }

  return (
    <div className="app">
      <aside className="nav">
        <header>
          <h1>贪吃蛇</h1>
          <p>每章一个程序，盯住游戏循环。</p>
        </header>
        <nav>
          {chapters.map((item, index) => {
            const done = chapterDone(item);
            const className = [
              "chapter",
              HUES[index] ?? "",
              item.id === chapter.id ? "active" : "",
              done ? "done" : "",
            ]
              .filter(Boolean)
              .join(" ");
            return (
              <button key={item.id} className={className} onClick={() => openChapter(item.id)}>
                <i>{index + 1}</i>
                <span>
                  <strong>{item.title}</strong>
                  {done ? <em>已完成</em> : null}
                </span>
              </button>
            );
          })}
        </nav>
        <div className="themes" role="group" aria-label="主题">
          {THEMES.map((item) => (
            <button
              key={item.id}
              type="button"
              className={item.id === theme ? "active" : ""}
              onClick={() => setTheme(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="scale">
          <button type="button" onClick={() => setScale((current) => clampScale(current - 0.1))}>
            缩小
          </button>
          <span>{Math.round(20 * scale)}pt</span>
          <button type="button" onClick={() => setScale((current) => clampScale(current + 0.1))}>
            放大
          </button>
        </div>
      </aside>
      <main className="main">
        <p className="kicker">{chapter.exercise}</p>
        <h2>{chapter.title}</h2>
        <p className="lead">{chapter.lead}</p>

        <section className="panel">
          <div className="row">
            {chapter.runs.map((target) => (
              <button
                key={target.id}
                className={target.primary ? "run" : "run secondary"}
                disabled={runningId !== null}
                onClick={() => run(target)}
              >
                {target.label}
              </button>
            ))}
          </div>
          <p className="note">
            {runNote || "程序只有一个主文件。先读讲解，再点运行，回来对照源码。"}
          </p>
        </section>

        {fullSections.map((section) => (
          <section className={`panel step ${section.role}`} key={section.heading}>
            <h3>{section.heading}</h3>
            {section.role === "diagram" && section.diagram ? (
              <Diagram code={section.diagram} />
            ) : null}
            {section.role === "code" && section.code ? (
              <pre className="code-sample">{section.code}</pre>
            ) : null}
            {section.body
              ? section.body.split("\n\n").map((paragraph) => (
                  <p key={paragraph}>
                    <RichText text={paragraph} />
                  </p>
                ))
              : null}
          </section>
        ))}

        <div className="split">
          <div>
            {flowSections.map((section) => (
              <section className={`panel step ${section.role}`} key={section.heading}>
                <h3>{section.heading}</h3>
                {section.body
                  ? section.body.split("\n\n").map((paragraph) => (
                      <p key={paragraph}>
                        <RichText text={paragraph} />
                      </p>
                    ))
                  : null}
              </section>
            ))}
          </div>

          <section className="panel">
            <h3>从这一章里抽出来的题</h3>
          {chapter.questions.map((question) => {
            const picked = answers[question.id];
            const revealed = picked !== undefined;
            return (
              <article className="question" key={question.id}>
                <p className={`kind ${kindClass(question.kind)}`}>{question.kind}</p>
                <p>{question.stem}</p>
                <div className="choices">
                  {question.choices.map((choice, index) => {
                    let mark = "";
                    if (revealed && index === question.answer) {
                      mark = "right";
                    } else if (revealed && index === picked) {
                      mark = "wrong";
                    }
                    return (
                      <button
                        key={choice}
                        className={mark}
                        onClick={() => choose(question, index)}
                      >
                        {choice}
                      </button>
                    );
                  })}
                </div>
                {revealed ? <p className="explain">{question.explanation}</p> : null}
              </article>
            );
            })}
          </section>
        </div>

        <section className="panel code-panel">
          <h3>这一章的文件</h3>
          <p className="note">主程序是这一章要读的写法。CMakeLists 只负责找到 raylib 并链接。</p>
          <div className="files">
            {chapter.files.map((path) => (
              <button
                key={path}
                className={path === shown ? "active" : ""}
                onClick={() => setFile(path)}
              >
                {path.replace(`exercise/${chapter.exercise}/`, "")}
              </button>
            ))}
          </div>
          <pre>{sourceText(shown) ?? "找不到这份源文件。"}</pre>
        </section>
      </main>
    </div>
  );
}
