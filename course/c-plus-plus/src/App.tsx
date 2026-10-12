import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import course from "../content/curriculum.json";

type Block =
  | { type: "lead" | "prose"; text: string }
  | { type: "callout"; tone: string; text: string }
  | { type: "compare"; caption?: string; headers: string[]; rows: string[][] }
  | { type: "code"; caption?: string; text: string }
  | { type: "predict"; prompt: string; reveal: string };

type QuizItem = {
  prompt: string;
  choices: string[];
  answer: number;
  explanation: string;
};

type Lab = { case: string; prompt: string; goal: string; hint: string };

type Topic = {
  id: string;
  title: string;
  description: string;
  difficulty: number;
  masteryGoal: string;
  knowledgeType: string;
  requires: string[];
  blocks: Block[];
  quiz: QuizItem[];
  labs: Lab[];
};

type Chapter = {
  id: string;
  title: string;
  description: string;
  topics: Topic[];
};

type ProgressRow = {
  function_id: string;
  mastery: number;
  last_correct: number;
  last_total: number;
};

const chapters = course.chapters as Chapter[];

const GOAL: Record<string, string> = {
  master: "熟练",
  required: "要会",
  familiar: "了解",
};

const KIND: Record<string, string> = {
  concept: "概念",
  skill: "技能",
  strategy: "策略",
};

function inTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

async function openLegacy(setNote: (note: string) => void) {
  if (!inTauri()) {
    setNote("请在应用窗口里打开。浏览器预览调不起旧版程序。");
    return;
  }
  setNote("正在打开…");
  try {
    setNote(await invoke<string>("open_legacy_window"));
  } catch (error) {
    setNote(typeof error === "string" ? error : "打不开旧版窗口");
  }
}

export default function App() {
  const topics = useMemo(() => chapters.flatMap((chapter) => chapter.topics), []);
  const [currentId, setCurrentId] = useState(topics[0]?.id ?? "");
  const [progress, setProgress] = useState<Record<string, ProgressRow>>({});
  const [legacyNote, setLegacyNote] = useState<string | null>(null);
  const current = topics.find((topic) => topic.id === currentId) ?? topics[0];

  useEffect(() => {
    if (!inTauri()) return;
    invoke<ProgressRow[]>("load_progress")
      .then((rows) => {
        const next: Record<string, ProgressRow> = {};
        for (const row of rows) next[row.function_id] = row;
        setProgress(next);
      })
      .catch(() => undefined);
  }, []);

  if (!current) return null;

  return (
    <div className="grid h-screen grid-cols-[280px_1fr]">
      <aside className="overflow-y-auto border-r border-[var(--line)] bg-white">
        <header className="sticky top-0 border-b border-[var(--line)] bg-white px-4 py-3">
          <div className="text-lg font-semibold text-[var(--accent)]">C++ 教程</div>
          <p className="mt-1 text-sm text-[var(--muted)]">{course.tagline}</p>
          <button
            type="button"
            onClick={() => void openLegacy(setLegacyNote)}
            className="mt-3 w-full rounded border border-[var(--line)] px-2 py-1.5 text-left text-sm hover:bg-[var(--paper)]"
          >
            运行旧版窗口
          </button>
          {legacyNote ? (
            <p className="mt-2 whitespace-pre-wrap text-xs text-[var(--muted)]">{legacyNote}</p>
          ) : null}
        </header>
        <nav className="px-2 py-2">
          {chapters.map((chapter) => (
            <section key={chapter.id} className="mb-3">
              <h2 className="px-2 py-1 text-xs font-semibold tracking-wide text-[var(--muted)]">
                {chapter.title}
              </h2>
              <ul>
                {chapter.topics.map((topic) => {
                  const row = progress[topic.id];
                  const active = topic.id === current.id;
                  return (
                    <li key={topic.id}>
                      <button
                        type="button"
                        onClick={() => setCurrentId(topic.id)}
                        className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm ${
                          active
                            ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                            : "hover:bg-[var(--paper)]"
                        }`}
                      >
                        <span>{topic.title}</span>
                        {row ? (
                          <span className="text-xs text-[var(--muted)]">{row.mastery}/5</span>
                        ) : null}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </nav>
      </aside>
      <main className="overflow-y-auto px-8 py-6">
        <TopicView
          key={current.id}
          topic={current}
          saved={progress[current.id]}
          onSaved={(row) => setProgress((prev) => ({ ...prev, [row.function_id]: row }))}
        />
      </main>
    </div>
  );
}

function TopicView({
  topic,
  saved,
  onSaved,
}: {
  topic: Topic;
  saved?: ProgressRow;
  onSaved: (row: ProgressRow) => void;
}) {
  return (
    <article className="mx-auto max-w-3xl">
      <p className="text-sm text-[var(--muted)]">{topic.id}</p>
      <h1 className="mt-1 text-2xl font-semibold">{topic.title}</h1>
      <p className="mt-2 text-sm text-[var(--muted)]">
        难度 {topic.difficulty} · {GOAL[topic.masteryGoal] ?? topic.masteryGoal}
        {topic.knowledgeType ? ` · ${KIND[topic.knowledgeType] ?? topic.knowledgeType}` : ""}
        {saved ? ` · 最近掌握度 ${saved.mastery}/5（${saved.last_correct}/${saved.last_total}）` : ""}
      </p>
      <div className="mt-6 space-y-4">
        {topic.blocks.map((block, index) => (
          <BlockView key={index} block={block} />
        ))}
      </div>
      <Quiz topic={topic} onSaved={onSaved} />
      {topic.labs.map((lab) => (
        <LabView key={lab.case} lab={lab} />
      ))}
    </article>
  );
}

function BlockView({ block }: { block: Block }) {
  if (block.type === "lead") {
    return <p className="text-lg leading-relaxed">{block.text}</p>;
  }
  if (block.type === "prose") {
    return <p className="leading-relaxed">{block.text}</p>;
  }
  if (block.type === "callout") {
    const warn = block.tone === "warn";
    return (
      <p
        className={`rounded border px-3 py-2 text-sm leading-relaxed ${
          warn
            ? "border-amber-300 bg-amber-50"
            : "border-[var(--line)] bg-white"
        }`}
      >
        {block.text}
      </p>
    );
  }
  if (block.type === "code") {
    return (
      <figure>
        {block.caption ? (
          <figcaption className="mb-1 text-sm text-[var(--muted)]">{block.caption}</figcaption>
        ) : null}
        <pre className="overflow-x-auto rounded bg-[#102033] p-4 text-sm leading-relaxed text-[#e7eef6]">
          {block.text}
        </pre>
      </figure>
    );
  }
  if (block.type === "compare") {
    return (
      <figure>
        {block.caption ? (
          <figcaption className="mb-1 text-sm text-[var(--muted)]">{block.caption}</figcaption>
        ) : null}
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              {block.headers.map((header) => (
                <th
                  key={header}
                  className="border border-[var(--line)] bg-white px-2 py-1.5 text-left font-medium"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, index) => (
              <tr key={index}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className="border border-[var(--line)] bg-white px-2 py-1.5">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </figure>
    );
  }
  if (block.type === "predict") {
    return <Predict prompt={block.prompt} reveal={block.reveal} />;
  }
  return null;
}

function Predict({ prompt, reveal }: { prompt: string; reveal: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded border border-[var(--line)] bg-white p-3">
      <p className="text-sm font-medium text-[var(--accent)]">先想一下</p>
      <p className="mt-1 leading-relaxed">{prompt}</p>
      {open ? (
        <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">{reveal}</p>
      ) : (
        <button
          type="button"
          className="mt-2 text-sm text-[var(--accent)] underline"
          onClick={() => setOpen(true)}
        >
          揭示
        </button>
      )}
    </div>
  );
}

function Quiz({ topic, onSaved }: { topic: Topic; onSaved: (row: ProgressRow) => void }) {
  const [picks, setPicks] = useState<Record<number, number>>({});
  const [note, setNote] = useState("");
  useEffect(() => {
    setPicks({});
    setNote("");
  }, [topic.id]);

  if (topic.quiz.length === 0) {
    return (
      <p className="mt-8 text-sm text-[var(--muted)]">
        这一节还没有随堂题。原来的掌握度记录还在，不会被清掉。
      </p>
    );
  }

  const done = topic.quiz.every((_, index) => picks[index] !== undefined);

  async function submit() {
    const correct = topic.quiz.filter((item, index) => picks[index] === item.answer).length;
    if (!inTauri()) {
      setNote(`浏览器预览不写进度。这一卷 ${correct}/${topic.quiz.length}。`);
      return;
    }
    try {
      const row = await invoke<ProgressRow>("record_attempt", {
        functionId: topic.id,
        correct,
        total: topic.quiz.length,
      });
      onSaved(row);
      setNote(`已写入掌握度 ${row.mastery}/5。`);
    } catch (error) {
      setNote(String(error));
    }
  }

  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold">随堂题</h2>
      <ol className="mt-3 space-y-4">
        {topic.quiz.map((item, index) => {
          const picked = picks[index];
          return (
            <li key={item.prompt} className="rounded border border-[var(--line)] bg-white p-3">
              <p>{item.prompt}</p>
              <div className="mt-2 space-y-1">
                {item.choices.map((choice, choiceIndex) => {
                  const selected = picked === choiceIndex;
                  const show = picked !== undefined;
                  const right = choiceIndex === item.answer;
                  return (
                    <button
                      key={choice}
                      type="button"
                      disabled={picked !== undefined}
                      onClick={() => setPicks((prev) => ({ ...prev, [index]: choiceIndex }))}
                      className={`block w-full rounded px-2 py-1.5 text-left text-sm ${
                        show && right
                          ? "bg-emerald-50"
                          : show && selected
                            ? "bg-rose-50"
                            : "hover:bg-[var(--paper)]"
                      }`}
                    >
                      {choice}
                    </button>
                  );
                })}
              </div>
              {picked !== undefined ? (
                <p className="mt-2 text-sm text-[var(--muted)]">{item.explanation}</p>
              ) : null}
            </li>
          );
        })}
      </ol>
      <button
        type="button"
        disabled={!done}
        onClick={() => void submit()}
        className="mt-3 rounded bg-[var(--accent)] px-3 py-1.5 text-sm text-white disabled:opacity-40"
      >
        写入掌握度
      </button>
      {note ? <p className="mt-2 text-sm text-[var(--muted)]">{note}</p> : null}
    </section>
  );
}

function LabView({ lab }: { lab: Lab }) {
  const [source, setSource] = useState("");
  const [output, setOutput] = useState("");
  const [running, setRunning] = useState(false);

  useEffect(() => {
    setOutput("");
    if (!inTauri()) {
      setSource("案例在应用窗口里打开。浏览器预览读不到本机文件。");
      return;
    }
    invoke<string>("read_case", { caseId: lab.case })
      .then(setSource)
      .catch((error) => setSource(String(error)));
  }, [lab.case]);

  async function run() {
    setRunning(true);
    try {
      const result = await invoke<{ ok: boolean; compiler: string; output: string }>(
        "compile_and_run",
        { source },
      );
      setOutput(`${result.compiler}\n${result.ok ? "通过" : "未通过"}\n${result.output}`);
    } catch (error) {
      setOutput(String(error));
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold">实验 · {lab.case}</h2>
      <p className="mt-2 leading-relaxed">{lab.prompt}</p>
      <p className="mt-2 text-sm text-[var(--muted)]">{lab.goal}</p>
      {lab.hint ? <p className="mt-1 text-sm text-[var(--muted)]">{lab.hint}</p> : null}
      <textarea
        value={source}
        onChange={(event) => setSource(event.target.value)}
        spellCheck={false}
        className="mt-3 h-80 w-full rounded border border-[var(--line)] bg-[#102033] p-3 font-mono text-sm text-[#e7eef6]"
      />
      <button
        type="button"
        disabled={!inTauri() || running}
        onClick={() => void run()}
        className="mt-2 rounded bg-[var(--accent)] px-3 py-1.5 text-sm text-white disabled:opacity-40"
      >
        {running ? "编译运行中" : "编译运行"}
      </button>
      {output ? (
        <pre className="mt-3 overflow-x-auto rounded bg-white p-3 text-sm whitespace-pre-wrap">
          {output}
        </pre>
      ) : null}
    </section>
  );
}
