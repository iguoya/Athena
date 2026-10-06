import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { AnimatePresence, motion } from "motion/react";
import {
  BookMarked,
  BookOpenText,
  FlaskConical,
  Sparkles,
  Terminal,
} from "lucide-react";
import { BlockView } from "./blocks";
import { PageView } from "./page-view";
import type {
  Block,
  Curriculum,
  DemoEvent,
  ExperimentEntity,
  Manifest,
  ManifestEntity,
  QuizItem,
} from "./types";

const MASTERY_LABEL: Record<string, string> = {
  master: "需精通",
  required: "须掌握",
  familiar: "了解即可",
  "": "未评定",
};

type View =
  | { kind: "kp"; sectionId: string; kpId: string | null }
  | { kind: "page"; sectionId: string; pageId: string }
  | { kind: "checkpoint"; sectionId: string }
  | { kind: "lab"; expId: string }
  | { kind: "ref"; refId: string };

/** Tauri 环境走 invoke；纯浏览器（vite dev）回退到直接读内容文件。 */
async function loadContent<T>(cmd: string, path: string): Promise<T> {
  try {
    return await invoke<T>(cmd);
  } catch {
    const response = await fetch(path);
    return (await response.json()) as T;
  }
}

export default function App() {
  const [curriculum, setCurriculum] = useState<Curriculum | null>(null);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [view, setView] = useState<View | null>(null);
  const [events, setEvents] = useState<DemoEvent[]>([]);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    loadContent<Curriculum>("get_curriculum", "/content/curriculum.json").then((c) => {
      setCurriculum(c);
      const first = c.sections.find((s) => s.knowledge_points.length > 0);
      if (first) setView({ kind: "kp", sectionId: first.id, kpId: first.knowledge_points[0].id });
    });
    loadContent<Manifest>("get_manifest", "/content/demos.json").then(setManifest);
    const unlisten = listen<DemoEvent>("demo-event", (event) => {
      setEvents((prev) => [event.payload, ...prev].slice(0, 20));
    });
    return () => {
      unlisten.then((fn) => fn()).catch(() => {});
    };
  }, []);

  const demos = useMemo(
    () => new Map((manifest?.demos ?? []).map((d) => [d.id, d])),
    [manifest],
  );
  const experiments = useMemo(
    () => new Map((manifest?.experiments ?? []).map((e) => [e.id as string, e])),
    [manifest],
  );

  const section = curriculum?.sections.find((s) => s.id === (view?.kind === "kp" || view?.kind === "page" ? view.sectionId : null)) ?? null;
  const kp = section?.knowledge_points.find((k) => k.id === (view?.kind === "kp" ? view.kpId : null)) ?? null;
  const page = section?.pages.find((p) => p.id === (view?.kind === "page" ? view.pageId : null)) ?? null;
  const labExp = view?.kind === "lab" ? experiments.get(view.expId) : undefined;
  const refEntry = view?.kind === "ref"
    ? curriculum?.reference.find((r) => r.id === view.refId)
    : undefined;

  const launch = (demoId: string) => {
    invoke<{ ok: boolean; message: string }>("launch_demo", { demoId })
      .then((result) => setNotice(result.message))
      .catch(() => setNotice("浏览器预览下不能启动演示，请在应用内运行。"));
  };

  const answer = (itemId: string, correct: boolean) => {
    invoke("record_attempt", { knowledgeId: kp?.id ?? "", itemId, correct }).catch(() => {});
  };

  // 在类型收窄之前提取，供侧栏展开块比较（那里 view 已被收窄为 kp）
  const activePageId = view?.kind === "page" ? view.pageId : null;
  const activeKpId = view?.kind === "kp" ? view.kpId : null;
  const activeSectionId =
    view?.kind === "kp" || view?.kind === "page" || view?.kind === "checkpoint"
      ? view.sectionId
      : null;
  const activeIsCheckpoint = view?.kind === "checkpoint";

  const viewKey =
    view?.kind === "kp" ? `${view.sectionId}:${view.kpId}`
    : view?.kind === "page" ? `${view.sectionId}:${view.pageId}`
    : view?.kind === "checkpoint" ? `${view.sectionId}::checkpoint`
    : view?.kind === "lab" ? view.expId
    : view?.kind === "ref" ? view.refId
    : "empty";

  if (!curriculum) {
    return <div className="p-8 text-muted">正在读取课程……</div>;
  }

  return (
    <div className="relative flex h-screen text-fg">
      <div className="deco-blobs" />

      {/* 左侧：三区课表树 */}
      <nav className="relative z-10 flex w-[360px] shrink-0 flex-col overflow-y-auto border-r border-line bg-surface/80 backdrop-blur-sm">
        <header className="flex items-center gap-3 border-b border-line px-4 py-4">
          <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-accent to-accent-deep font-display text-[30px] font-semibold text-on-accent shadow-card">
            G
          </div>
          <div>
            <h1 className="font-display text-[26px] font-semibold leading-tight">
              {curriculum.title}
            </h1>
            <p className="text-[20px] text-muted">Programming with gtkmm 4</p>
          </div>
        </header>

        <div className="flex-1 px-2 pb-4">
          {/* 一、教程章节（原文） */}
          <p className="flex items-center gap-1.5 px-3 pt-4 pb-1 text-[20px] font-semibold tracking-wide text-muted">
            <BookOpenText className="size-5" /> 教程章节
          </p>
          <ul>
            {curriculum.sections.map((s) => {
              const active =
                activeSectionId === s.id &&
                (activePageId != null || activeKpId != null || activeIsCheckpoint);
              return (
                <li key={s.id}>
                  <button
                    onClick={() =>
                      // 官网行为：点章直接进入章页正文（章导语并入第一节）
                      setView({ kind: "page", sectionId: s.id, pageId: s.pages[0]?.id ?? "" })
                    }
                    className={`group relative flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[22px] transition-colors ${
                      active ? "bg-accent-soft font-medium text-accent" : "hover:bg-surface-2"
                    }`}
                  >
                    {active && (
                      <motion.span
                        layoutId="nav-indicator"
                        className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-full bg-accent"
                      />
                    )}
                    <span
                      className={`size-3 shrink-0 rounded-full transition-colors ${
                        s.pages.some((p) => p.status === "translated")
                          ? "bg-accent-deep"
                          : "bg-line group-hover:bg-muted"
                      }`}
                    />
                    <span className="flex-1 truncate">
                      {s.order}. {s.title}
                    </span>
                  </button>
                  {active && (
                    <ul className="ml-6 border-l border-line pl-2">
                      {/* 官方节页：严格跟随上游分页（应用 ADR 0002），直接跟在章名下 */}
                      {s.pages.map((p) => {
                        const pageActive = activeSectionId === s.id && activePageId === p.id;
                        return (
                          <li key={p.id}>
                            <button
                              onClick={() => setView({ kind: "page", sectionId: s.id, pageId: p.id })}
                              className={`flex w-full items-center gap-1.5 rounded px-2 py-1.5 text-left text-[22px] transition-colors ${
                                pageActive
                                  ? "bg-accent-soft font-medium text-accent"
                                  : "text-muted hover:bg-surface-2 hover:text-fg"
                              }`}
                            >
                              <span
                                className={`size-1 shrink-0 rounded-full ${
                                  p.status === "translated" ? "bg-accent-deep" : "bg-line"
                                }`}
                              />
                              <span className="flex-1 truncate">{p.title}</span>
                            </button>
                          </li>
                        );
                      })}

                      {s.checkpoint.length > 0 && (
                        <li>
                          <button
                            onClick={() => setView({ kind: "checkpoint", sectionId: s.id })}
                            className={`w-full rounded px-2 py-1.5 text-left text-[20px] transition-colors ${
                              activeIsCheckpoint && activeSectionId === s.id
                                ? "bg-accent-soft font-medium text-accent"
                                : "text-muted hover:bg-surface-2 hover:text-fg"
                            }`}
                          >
                            章末考核（{s.checkpoint.length} 题）
                          </button>
                        </li>
                      )}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>

          {/* 二、实验区（与教程章节区分的独立入口） */}
          <p className="flex items-center gap-1.5 px-3 pt-5 pb-1 text-[20px] font-semibold tracking-wide text-accent-deep">
            <FlaskConical className="size-5" /> 实验
          </p>
          <ul className="pb-2">
            {curriculum.labs?.groups.map((g) => (
              <li key={g.id}>
                <p className="px-3 py-1 text-[20px] text-muted">{g.title}</p>
                <ul className="ml-3 border-l border-accent/40 pl-2">
                  {g.experiments.map((expId) => {
                    const active = view?.kind === "lab" && view.expId === expId;
                    return (
                      <li key={expId}>
                        <button
                          onClick={() => setView({ kind: "lab", expId })}
                          className={`w-full rounded px-2 py-1.5 text-left text-[20px] transition-colors ${
                            active
                              ? "bg-accent-soft font-medium text-accent"
                              : "text-muted hover:bg-surface-2 hover:text-fg"
                          }`}
                        >
                          {experiments.get(expId)?.title ?? expId}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </li>
            ))}
          </ul>

          {/* 三、参考层（完整呈现但不进学习主线） */}
          <p className="flex items-center gap-1.5 px-3 pt-4 pb-1 text-[20px] font-semibold tracking-wide text-muted">
            <BookMarked className="size-5" /> 参考
          </p>
          <ul>
            {curriculum.reference.map((r) => {
              const active = view?.kind === "ref" && view.refId === r.id;
              return (
                <li key={r.id}>
                  <button
                    onClick={() => setView({ kind: "ref", refId: r.id })}
                    className={`flex w-full items-center gap-2 rounded px-3 py-1.5 text-left text-[20px] transition-colors ${
                      active
                        ? "bg-surface-2 font-medium text-fg"
                        : "text-muted hover:bg-surface-2 hover:text-fg"
                    }`}
                  >
                    <span
                      className={`size-5 shrink-0 rounded-full ${
                        r.status === "translated" ? "bg-accent-deep/70" : "bg-line"
                      }`}
                    />
                    <span className="flex-1 truncate">{r.title}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      </nav>

      {/* 右侧：内容视图（切换时淡入上浮） */}
      <main className="relative z-10 flex-1 overflow-y-auto">
        {notice && (
          <motion.p
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="sticky top-0 z-20 mx-auto w-fit rounded-full bg-accent-soft px-5 py-2 text-[22px] text-accent-deep shadow-card ring-1 ring-accent/25"
          >
            {notice}
          </motion.p>
        )}
        <AnimatePresence mode="wait">
          <motion.div
            key={viewKey}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="mx-auto w-full px-14 py-12"
          >
            {!view && <p className="text-muted">从左侧选择一个章节开始。</p>}

            {view?.kind === "kp" && section && kp && (
              <>
                <p className="text-[22px] text-muted">
                  {section.order}. {section.title}
                </p>
                <h2 className="mt-1 font-display text-[42px] font-semibold">{kp.title}</h2>
                <div className="mt-3 flex gap-2 text-[20px]">
                  <span className="rounded-full bg-surface-2 px-2.5 py-1 text-muted ring-1 ring-line">
                    难度 {kp.difficulty}/5
                  </span>
                  <span className="rounded-full bg-accent-soft px-2.5 py-1 font-medium text-accent ring-1 ring-accent/20">
                    {MASTERY_LABEL[kp.mastery_goal]}
                  </span>
                  <span className="rounded-full bg-surface-2 px-2.5 py-1 text-muted ring-1 ring-line">
                    {kp.type}
                  </span>
                </div>
                {kp.blocks.map((block, index) => (
                  <BlockView
                    key={index}
                    block={block}
                    demos={demos}
                    experiments={experiments}
                    onLaunch={launch}
                    onAnswer={answer}
                    scopeId={kp.id}
                  />
                ))}
              </>
            )}

            {view?.kind === "page" && section && page && (() => {
              const pageIndex = section.pages.findIndex((x) => x.id === page.id);
              const prevPage = pageIndex > 0 ? section.pages[pageIndex - 1] : null;
              const nextPage = pageIndex < section.pages.length - 1 ? section.pages[pageIndex + 1] : null;
              const navButton = (target: { id: string; title: string } | null, label: string, align: "left" | "right") =>
                target ? (
                  <button
                    onClick={() => setView({ kind: "page", sectionId: section.id, pageId: target.id })}
                    className={`max-w-[45%] rounded px-3 py-1.5 text-left text-[20px] text-white/90 transition-colors hover:bg-white/15 ${align === "right" ? "text-right" : ""}`}
                  >
                    <span className="block text-[20px] uppercase tracking-wide text-white/60">{label}</span>
                    <span className="block truncate font-medium">{target.title}</span>
                  </button>
                ) : <span className="w-24" />;
              return (
              <>
                {/* 官方 navheader 风格的节间导航（深红底，来源：上游 style.css） */}
                <div className="mb-6 flex items-center justify-between gap-2 rounded-card bg-accent-deep px-4 py-3">
                  {navButton(prevPage, "← 上一节", "left")}
                  <span className="shrink-0 text-[20px] font-medium text-white/70">
                    {section.order}. {section.title}
                  </span>
                  {navButton(nextPage, "下一节 →", "right")}
                </div>
                <p className="text-[22px] text-muted">
                  教程第 {section.translation_ref.chapter} 章 ·{" "}
                  <a
                    className="text-accent hover:underline"
                    href={curriculum.book.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    回到原文
                  </a>
                </p>
                <h2 className="mt-1 font-display text-[42px] font-semibold">{page.title}</h2>
                <button
                  onClick={() => setView({ kind: "kp", sectionId: section.id, kpId: null })}
                  className="mt-2 text-[20px] text-accent hover:underline"
                >
                  ← 本章节页
                </button>
                <PageView chapterId={section.id} pageId={page.id} />
                <PageAssessments
                  section={section}
                  pageId={page.id}
                  demos={demos}
                  experiments={experiments}
                  onLaunch={launch}
                  onAnswer={answer}
                />
                <div className="mt-10 flex items-center justify-between gap-2 rounded-card bg-accent-deep px-4 py-3">
                  {navButton(prevPage, "← 上一节", "left")}
                  <span className="shrink-0 text-[20px] font-medium text-white/70">
                    {section.translation_ref.chapter}.{pageIndex + 1}
                  </span>
                  {navButton(nextPage, "下一节 →", "right")}
                </div>
              </>
              );
            })()}

            {view?.kind === "checkpoint" && section && (
              <CheckpointPage
                section={section}
                demos={demos}
                experiments={experiments}
                onLaunch={launch}
                onAnswer={answer}
              />
            )}

            {view?.kind === "lab" && labExp && <LabView entity={labExp} />}

            {view?.kind === "ref" && refEntry && (
              <>
                <h2 className="font-display text-[42px] font-semibold">{refEntry.title}</h2>
                <p className="mt-2 text-[22px] text-muted">
                  {refEntry.kind === "migration"
                    ? "版本迁移 · 参考层"
                    : refEntry.kind === "contributing"
                      ? "贡献指南 · 参考层"
                      : "附录 · 参考层"}
                  {" · "}
                  {refEntry.status === "translated" ? "已译" : "待译"}
                </p>
                {refEntry.note && (
                  <p className="mt-4 rounded-card bg-surface p-4 text-[22px] text-fg/80 shadow-card ring-1 ring-line">
                    {refEntry.note}
                  </p>
                )}
                <p className="mt-4 text-[22px] text-muted">
                  教程定位：{refEntry.translation_ref.chapter
                    ? `第 ${refEntry.translation_ref.chapter} 章`
                    : `附录 ${refEntry.translation_ref.appendix}`}{" "}
                  · {refEntry.translation_ref.title}
                </p>
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* 演示事件面板：只在实验页出现（它是实验工作流的上下文） */}
      {view?.kind === "lab" && (
      <aside className="relative z-10 flex w-[360px] shrink-0 flex-col border-l border-line bg-surface p-4 text-fg">
        <h3 className="flex items-center gap-2 text-[22px] font-semibold text-accent">
          <Terminal className="size-6" /> 演示事件
        </h3>
        {notice && (
          <motion.p
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-2 rounded-lg bg-accent-soft p-2 text-[20px] text-accent-deep"
          >
            {notice}
          </motion.p>
        )}
        <ul className="mt-3 flex-1 space-y-1.5 overflow-y-auto">
          <AnimatePresence initial={false}>
            {events.map((event, index) => (
              <motion.li
                key={`${index}-${event.demo_id}-${event.method}`}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                className="rounded-lg bg-surface-2 p-2 font-mono text-[20px] leading-relaxed text-muted ring-1 ring-line"
              >
                <span className="text-accent">{event.demo_id}</span>
                <span className="text-muted"> · </span>
                <span className="text-fg">{event.method}</span>
                {Object.keys(event.params).length > 0 && (
                  <span className="block break-all text-muted">
                    {JSON.stringify(event.params)}
                  </span>
                )}
              </motion.li>
            ))}
          </AnimatePresence>
          {events.length === 0 && (
            <li className="flex items-start gap-2 text-[20px] text-muted">
              <Sparkles className="mt-0.5 size-5 shrink-0" />
              启动真机演示后，signal 事件会显示在这里。
            </li>
          )}
        </ul>
      </aside>
      )}
    </div>
  );
}


function PageAssessments({
  section,
  pageId,
  demos,
  experiments,
  onLaunch,
  onAnswer,
}: {
  section: { id: string; pages: { id: string }[]; knowledge_points: { blocks: Block[] }[]; checkpoint: QuizItem[] };
  pageId: string;
  demos: Map<string, ManifestEntity>;
  experiments: Map<string, ExperimentEntity>;
  onLaunch: (demoId: string) => void;
  onAnswer: (itemId: string, correct: boolean) => void;
}) {
  // 本节的随堂测验：读完本节即时测（题面按 page_ref 归属各节）
  const quizzes = section.knowledge_points
    .flatMap((kp) => kp.blocks)
    .filter(
      (b) =>
        (b.type === "quiz" || b.type === "observation_quiz") &&
        "page_ref" in b &&
        b.page_ref === pageId,
    );
  if (quizzes.length === 0) return null;
  return (
    <section className="mt-16">
      <h3 className="font-display text-[26px] font-semibold text-accent">
        本节测验 · {quizzes.length} 题
      </h3>
      {quizzes.map((block, index) => (
        <BlockView
          key={index}
          block={block}
          demos={demos}
          experiments={experiments}
          onLaunch={onLaunch}
          onAnswer={onAnswer}
          scopeId={`${section.id}:${pageId}`}
        />
      ))}
    </section>
  );
}

function CheckpointPage({
  section,
  demos,
  experiments,
  onLaunch,
  onAnswer,
}: {
  section: { id: string; title: string; translation_ref: { chapter?: number }; checkpoint: QuizItem[] };
  demos: Map<string, ManifestEntity>;
  experiments: Map<string, ExperimentEntity>;
  onLaunch: (demoId: string) => void;
  onAnswer: (itemId: string, correct: boolean) => void;
}) {
  return (
    <>
      <p className="text-sm text-muted">
        {section.title} · 教程第 {section.translation_ref.chapter} 章
      </p>
      <h2 className="mt-1 font-display text-[42px] font-semibold">章末考核</h2>
      <p className="mt-3 text-[22px] leading-relaxed text-fg/80">
        本考核覆盖本章全部官方节页的内容。答错没有惩罚——错题会进入复习回路。
      </p>
      <section className="mt-8 rounded-card bg-surface p-6 shadow-card ring-1 ring-accent/30">
        {section.checkpoint.map((item, index) => (
          <BlockView
            key={index}
            block={{ type: "quiz", ...item }}
            demos={demos}
            experiments={experiments}
            onLaunch={onLaunch}
            onAnswer={onAnswer}
            scopeId={`${section.id}:checkpoint`}
          />
        ))}
      </section>
    </>
  );
}

function LabView({ entity }: { entity: ExperimentEntity }) {
  return (
    <>
      <p className="flex items-center gap-2 text-[22px] font-medium text-accent-deep">
        <FlaskConical className="size-6" /> 实验 · {entity.id}
      </p>
      <h2 className="mt-1 font-display text-[42px] font-semibold">{entity.title}</h2>
      <p className="mt-4 leading-relaxed text-fg/90">{entity.purpose}</p>
      <div className="mt-5 rounded-card border border-accent-deep/30 bg-accent-deep/5 p-5">
        <p className="text-[22px] font-semibold text-accent-deep">跑通标准</p>
        <p className="mt-1 text-[22px] text-fg/85">{entity.acceptance}</p>
      </div>
      <div className="mt-4 rounded-card bg-surface p-5 text-[22px] shadow-card ring-1 ring-line">
        <p className="font-semibold text-fg">骨架位置</p>
        <p className="mt-1 font-mono text-[20px] text-muted">{entity.skeleton_dir}</p>
        <p className="mt-1 text-[20px] text-muted">只读；复制到工作区后修改，可一键重置。</p>
        <p className="mt-4 font-semibold text-fg">编译运行</p>
        <pre className="mt-2 overflow-x-auto rounded-xl bg-[#F6F6F6] p-4 font-mono text-[20px] leading-relaxed text-[#555555] ring-1 ring-line">
          <code>{`cmake -S demos -B build-native && cmake --build build-native --target ${entity.build_target}`}</code>
        </pre>
        <p className="mt-4 font-semibold text-fg">对应理论点</p>
        <ul className="mt-1 space-y-0.5 text-[20px] text-muted">
          {entity.theory_refs.map((ref) => (
            <li key={ref} className="font-mono">
              {ref}
            </li>
          ))}
        </ul>
      </div>
      <p className="mt-4 text-[20px] text-muted">
        对照的教程章节：{entity.translation_ref.chapter
          ? `第 ${entity.translation_ref.chapter} 章`
          : `附录 ${entity.translation_ref.appendix}`}{" "}
        · {entity.translation_ref.title}
      </p>
    </>
  );
}
