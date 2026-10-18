import { useEffect, useMemo, useState, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Cooperate, type Cooperation } from "./cooperate";
import { VisualFigure, type Visual } from "./cubefig";

type Section = {
  role: "focus" | "advanced" | "experiment";
  heading: string;
  body: string;
  /** 这一节配的图：魔方步骤回放或条形图。 */
  figure?: Visual;
  /** experiment 专用：改之前先猜的那个问题。 */
  predict?: string;
  /** experiment 专用：实测到的结果，点开才看。 */
  observe?: string;
};

type Question = {
  id: string;
  kind: string;
  stem: string;
  /** 题干配图，做题前就显示。预测题在这里只给起点，不给转法。 */
  figure?: Visual;
  choices: string[];
  answer: number;
  explanation: string;
  /** 作答后才出现的回放，让读者对照自己的预测。 */
  reveal?: Visual;
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
  cooperation: Cooperation;
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
    "../exercise/**/*.{cc,hh,h,blp,css}",
    "../exercise/**/meson.build",
    "../exercise/**/app.gresource.xml",
    "!../exercise/**/build/**",
  ],
  { eager: true, query: "?raw", import: "default" },
) as Record<string, string>;

function sourceText(relative: string): string | undefined {
  return sources[`../${relative}`];
}

const SCALE_KEY = "cube-ui-scale";
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
  { id: "sand", label: "沙色" },
  { id: "celadon", label: "青瓷" },
] as const;

type ThemeId = (typeof THEMES)[number]["id"];
const THEME_KEY = "cube-ui-theme";

function readTheme(): ThemeId {
  const raw = localStorage.getItem(THEME_KEY);
  return THEMES.some((item) => item.id === raw) ? (raw as ThemeId) : "paper";
}

function applyTheme(theme: ThemeId) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(THEME_KEY, theme);
}

applyTheme(readTheme());

const HUES = ["hue-1", "hue-2", "hue-3", "hue-4", "hue-5", "hue-6", "hue-7"];

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
  const [workspaceOn, setWorkspaceOn] = useState(false);

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
    const exercise = chapter?.exercise;
    if (!exercise) {
      return;
    }
    invoke<boolean>("workspace_present", { chapter: exercise })
      .then(setWorkspaceOn)
      .catch(() => setWorkspaceOn(false));
  }, [chapter?.exercise]);

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
      setRunNote("浏览器里只能看讲解。要打开魔方窗口，请用启动器打开「二阶魔方」。");
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

  async function openInVisualStudio() {
    if (!chapter) {
      return;
    }
    if (!("__TAURI_INTERNALS__" in window)) {
      setRunNote("浏览器里只能看讲解。要在 VS 2022 中改这一章，请用启动器打开「二阶魔方」。");
      return;
    }
    setRunNote("正在准备这一章的工作副本…");
    try {
      const message = await invoke<string>("open_in_visual_studio", { chapter: chapter.exercise });
      setWorkspaceOn(true);
      setRunNote(message);
    } catch (error) {
      setRunNote(typeof error === "string" ? error : "没有在 VS 2022 中打开。");
    }
  }

  async function restoreWorkspace() {
    if (!chapter) {
      return;
    }
    if (!workspaceOn) {
      setRunNote("这一章还没有工作副本。");
      return;
    }
    if (!window.confirm("还原会丢掉这一章工作副本里的修改。课程原件不动。")) {
      return;
    }
    try {
      const message = await invoke<string>("restore_workspace", { chapter: chapter.exercise });
      setWorkspaceOn(false);
      setRunNote(message);
    } catch (error) {
      setRunNote(typeof error === "string" ? error : "还原没有完成。");
    }
  }

  return (
    <div className="app">
      <aside className="nav">
        <header>
          <h1>二阶魔方</h1>
          <p>从初学者的层先法，写出能解任意状态的程序。</p>
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
        <Cooperate data={chapter.cooperation} />

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
          <div className="row">
            <button type="button" className="run secondary" onClick={() => void openInVisualStudio()}>
              在 VS 2022 中打开
            </button>
            <button type="button" className="run quiet" onClick={() => void restoreWorkspace()}>
              还原
            </button>
          </div>
          <p className="note">
            {runNote ||
              (workspaceOn
                ? "运行按钮编译的是这一章的工作副本。window.blp 是文本，改完后重新打开窗口看效果。"
                : "先打开这一章的窗口玩一玩。要改代码，用 VS 2022 打开工作副本，课程原件不动。")}
          </p>
        </section>

        <div className="split">
          <div>
            {chapter.sections.map((section) => {
              const body = (
                <>
                  {section.body.split("\n\n").map((paragraph) => (
                    <p key={paragraph}>
                      <RichText text={paragraph} />
                    </p>
                  ))}
                  {section.figure ? <VisualFigure spec={section.figure} /> : null}
                </>
              );
              if (section.role === "advanced") {
                return (
                  <details className="panel step advanced" key={section.heading}>
                    <summary>进阶：{section.heading}</summary>
                    {body}
                  </details>
                );
              }
              if (section.role === "experiment") {
                return (
                  <section className="panel step experiment" key={section.heading}>
                    <h3>{section.heading}</h3>
                    {body}
                    {section.predict ? <p className="predict">{section.predict}</p> : null}
                    {section.observe ? (
                      <details className="observe">
                        <summary>看实测结果</summary>
                        <p>{section.observe}</p>
                      </details>
                    ) : null}
                  </section>
                );
              }
              return (
                <section className={`panel step ${section.role}`} key={section.heading}>
                  <h3>{section.heading}</h3>
                  {body}
                </section>
              );
            })}
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
                {question.figure ? <VisualFigure spec={question.figure} /> : null}
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
                {revealed && question.reveal ? <VisualFigure spec={question.reveal} /> : null}
              </article>
            );
            })}
          </section>
        </div>

        <section className="panel code-panel">
          <h3>这一章的文件</h3>
          <p className="note">先看 window.blp，再看 Session 怎样把它们接起来。</p>
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
