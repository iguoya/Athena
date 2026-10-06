import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { BlockView } from "./blocks";
import type {
  Curriculum,
  DemoEvent,
  ExperimentEntity,
  Manifest,
} from "./types";

const MASTERY_LABEL: Record<string, string> = {
  master: "需精通",
  required: "须掌握",
  familiar: "了解即可",
  "": "未评定",
};

type View =
  | { kind: "kp"; sectionId: string; kpId: string | null }
  | { kind: "lab"; expId: string }
  | { kind: "ref"; refId: string };

export default function App() {
  const [curriculum, setCurriculum] = useState<Curriculum | null>(null);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [view, setView] = useState<View | null>(null);
  const [events, setEvents] = useState<DemoEvent[]>([]);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    invoke<Curriculum>("get_curriculum").then((c) => {
      setCurriculum(c);
      const first = c.sections.find((s) => s.knowledge_points.length > 0);
      if (first) setView({ kind: "kp", sectionId: first.id, kpId: first.knowledge_points[0].id });
    });
    invoke<Manifest>("get_manifest").then(setManifest);
    const unlisten = listen<DemoEvent>("demo-event", (event) => {
      setEvents((prev) => [event.payload, ...prev].slice(0, 20));
    });
    return () => {
      unlisten.then((fn) => fn());
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

  const section = curriculum?.sections.find((s) => s.id === (view?.kind === "kp" ? view.sectionId : null)) ?? null;
  const kp = section?.knowledge_points.find((k) => k.id === (view?.kind === "kp" ? view.kpId : null)) ?? null;
  const labExp = view?.kind === "lab" ? experiments.get(view.expId) : undefined;
  const refEntry = view?.kind === "ref"
    ? curriculum?.reference.find((r) => r.id === view.refId)
    : undefined;

  const launch = (demoId: string) => {
    invoke<{ ok: boolean; message: string }>("launch_demo", { demoId }).then((result) => {
      setNotice(result.message);
    });
  };

  const answer = (itemId: string, correct: boolean) => {
    invoke("record_attempt", { knowledgeId: kp?.id ?? "", itemId, correct });
  };

  if (!curriculum) {
    return <div className="p-8 text-stone-500">正在读取课程……</div>;
  }

  return (
    <div className="flex h-screen bg-stone-100 text-stone-900">
      {/* 左侧：三区课表树 */}
      <nav className="w-72 shrink-0 overflow-y-auto border-r border-stone-200 bg-white">
        <header className="border-b border-stone-200 px-4 py-4">
          <h1 className="text-lg font-semibold">{curriculum.title}</h1>
          <p className="mt-1 text-xs text-stone-500">
            编排基准：{curriculum.book.title}（GFDL）
          </p>
        </header>

        {/* 一、教程章节（原文） */}
        <p className="px-4 pt-3 pb-1 text-xs font-semibold tracking-wide text-stone-400">
          教程章节
        </p>
        <ul className="px-2">
          {curriculum.sections.map((s) => (
            <li key={s.id}>
              <button
                onClick={() =>
                  setView({ kind: "kp", sectionId: s.id, kpId: s.knowledge_points[0]?.id ?? null })
                }
                className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm ${
                  view?.kind === "kp" && view.sectionId === s.id
                    ? "bg-blue-50 text-blue-800"
                    : "hover:bg-stone-100"
                }`}
              >
                <span
                  className={`size-2 shrink-0 rounded-full ${
                    s.status === "translated" ? "bg-green-500" : "bg-stone-300"
                  }`}
                />
                <span className="flex-1">
                  {s.order}. {s.title}
                </span>
              </button>
              {view?.kind === "kp" && view.sectionId === s.id && (
                <ul className="ml-6 border-l border-stone-200 pl-2">
                  {s.knowledge_points.map((k) => (
                    <li key={k.id}>
                      <button
                        onClick={() => setView({ kind: "kp", sectionId: s.id, kpId: k.id })}
                        className={`w-full rounded px-2 py-1.5 text-left text-xs ${
                          view.kpId === k.id
                            ? "bg-blue-100 font-medium text-blue-900"
                            : "text-stone-600 hover:bg-stone-100"
                        }`}
                      >
                        {k.title}
                      </button>
                    </li>
                  ))}
                  {s.checkpoint.length > 0 && (
                    <li className="px-2 py-1.5 text-xs font-medium text-stone-500">
                      章末考核（{s.checkpoint.length} 题）
                    </li>
                  )}
                </ul>
              )}
            </li>
          ))}
        </ul>

        {/* 二、实验区（与教程章节区分的独立入口） */}
        <p className="px-4 pt-4 pb-1 text-xs font-semibold tracking-wide text-orange-500">
          实验
        </p>
        <ul className="px-2 pb-2">
          {curriculum.labs?.groups.map((g) => (
            <li key={g.id}>
              <p className="px-3 py-1 text-xs text-stone-500">{g.title}</p>
              <ul className="ml-3 border-l border-orange-200 pl-2">
                {g.experiments.map((expId) => (
                  <li key={expId}>
                    <button
                      onClick={() => setView({ kind: "lab", expId })}
                      className={`w-full rounded px-2 py-1.5 text-left text-xs ${
                        view?.kind === "lab" && view.expId === expId
                          ? "bg-orange-100 font-medium text-orange-900"
                          : "text-stone-600 hover:bg-orange-50"
                      }`}
                    >
                      {experiments.get(expId)?.title ?? expId}
                    </button>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>

        {/* 三、参考层（完整呈现但不进学习主线） */}
        <p className="px-4 pt-4 pb-1 text-xs font-semibold tracking-wide text-stone-400">
          参考
        </p>
        <ul className="px-2 pb-4">
          {curriculum.reference.map((r) => (
            <li key={r.id}>
              <button
                onClick={() => setView({ kind: "ref", refId: r.id })}
                className={`flex w-full items-center gap-2 rounded px-3 py-1.5 text-left text-xs ${
                  view?.kind === "ref" && view.refId === r.id
                    ? "bg-stone-200 font-medium text-stone-800"
                    : "text-stone-500 hover:bg-stone-100"
                }`}
              >
                <span
                  className={`size-1.5 shrink-0 rounded-full ${
                    r.status === "translated" ? "bg-green-400" : "bg-stone-300"
                  }`}
                />
                <span className="flex-1">{r.title}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* 右侧：内容视图 */}
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-8 py-8">
          {!view && <p className="text-stone-500">从左侧选择一个章节开始。</p>}

          {view?.kind === "kp" && section && !kp && (
            <>
              <h2 className="text-2xl font-semibold">{section.title}</h2>
              <p className="mt-1 text-sm text-stone-500">
                教程第 {section.translation_ref.chapter} 章 ·{" "}
                <a
                  className="text-blue-600 hover:underline"
                  href={curriculum.book.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  回到原文
                </a>
              </p>
              {section.checkpoint.map((item, index) => (
                <BlockView
                  key={index}
                  block={{ type: "quiz", ...item }}
                  demos={demos}
                  experiments={experiments}
                  onLaunch={launch}
                  onAnswer={answer}
                  scopeId={`${section.id}:checkpoint`}
                />
              ))}
            </>
          )}

          {view?.kind === "kp" && section && kp && (
            <>
              <p className="text-sm text-stone-500">
                {section.order}. {section.title}
              </p>
              <h2 className="mt-1 text-2xl font-semibold">{kp.title}</h2>
              <div className="mt-2 flex gap-2 text-xs">
                <span className="rounded-full bg-stone-200 px-2 py-0.5">
                  难度 {kp.difficulty}/5
                </span>
                <span className="rounded-full bg-blue-100 px-2 py-0.5 text-blue-800">
                  {MASTERY_LABEL[kp.mastery_goal]}
                </span>
                <span className="rounded-full bg-stone-200 px-2 py-0.5">{kp.type}</span>
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

          {view?.kind === "lab" && labExp && <LabView entity={labExp} />}

          {view?.kind === "ref" && refEntry && (
            <>
              <h2 className="text-2xl font-semibold">{refEntry.title}</h2>
              <p className="mt-1 text-sm text-stone-500">
                {refEntry.kind === "migration"
                  ? "版本迁移 · 参考层"
                  : refEntry.kind === "contributing"
                    ? "贡献指南 · 参考层"
                    : "附录 · 参考层"}
                {" · "}
                {refEntry.status === "translated" ? "已译" : "待译"}
              </p>
              {refEntry.note && (
                <p className="mt-3 rounded-lg bg-stone-50 p-3 text-sm text-stone-600">
                  {refEntry.note}
                </p>
              )}
              <p className="mt-3 text-sm text-stone-500">
                教程定位：{refEntry.translation_ref.chapter
                  ? `第 ${refEntry.translation_ref.chapter} 章`
                  : `附录 ${refEntry.translation_ref.appendix}`}{" "}
                · {refEntry.translation_ref.title}
              </p>
            </>
          )}
        </div>
      </main>

      {/* 演示事件面板 */}
      <aside className="w-64 shrink-0 overflow-y-auto border-l border-stone-200 bg-white p-3">
        <h3 className="text-sm font-semibold text-stone-700">演示事件</h3>
        {notice && <p className="mt-2 rounded bg-amber-50 p-2 text-xs text-amber-800">{notice}</p>}
        <ul className="mt-2 space-y-1">
          {events.map((event, index) => (
            <li key={index} className="rounded bg-stone-50 p-2 font-mono text-xs text-stone-600">
              {event.demo_id}: {event.method}{" "}
              {Object.keys(event.params).length > 0 && JSON.stringify(event.params)}
            </li>
          ))}
          {events.length === 0 && (
            <li className="text-xs text-stone-400">
              启动真机演示后，signal 事件会显示在这里。
            </li>
          )}
        </ul>
      </aside>
    </div>
  );
}

function LabView({ entity }: { entity: ExperimentEntity }) {
  return (
    <>
      <p className="text-sm text-orange-600">实验 · {entity.id}</p>
      <h2 className="mt-1 text-2xl font-semibold">{entity.title}</h2>
      <p className="mt-3 leading-relaxed text-stone-800">{entity.purpose}</p>
      <div className="mt-4 rounded-lg border border-orange-300 bg-orange-50 p-4">
        <p className="text-sm font-medium text-orange-900">跑通标准</p>
        <p className="mt-1 text-sm text-stone-700">{entity.acceptance}</p>
      </div>
      <div className="mt-4 rounded-lg border border-stone-300 bg-white p-4 text-sm">
        <p className="font-medium text-stone-700">骨架位置</p>
        <p className="mt-1 font-mono text-xs text-stone-600">
          {entity.skeleton_dir}（只读；复制到工作区后修改，可一键重置）
        </p>
        <p className="mt-3 font-medium text-stone-700">编译运行</p>
        <pre className="mt-1 overflow-x-auto rounded bg-stone-900 p-3 text-xs text-stone-100">
          <code>{`cmake -S demos -B build-native && cmake --build build-native --target ${entity.build_target}`}</code>
        </pre>
        <p className="mt-3 font-medium text-stone-700">对应理论点</p>
        <ul className="mt-1 list-disc pl-5 text-xs text-stone-600">
          {entity.theory_refs.map((ref) => (
            <li key={ref} className="font-mono">
              {ref}
            </li>
          ))}
        </ul>
      </div>
      <p className="mt-4 text-xs text-stone-500">
        对照的教程章节：{entity.translation_ref.chapter
          ? `第 ${entity.translation_ref.chapter} 章`
          : `附录 ${entity.translation_ref.appendix}`}{" "}
        · {entity.translation_ref.title}
      </p>
    </>
  );
}
