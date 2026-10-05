import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { BlockView } from "./blocks";
import type { Curriculum, DemoEvent, Manifest } from "./types";

const MASTERY_LABEL: Record<string, string> = {
  master: "需精通",
  required: "须掌握",
  familiar: "了解即可",
  "": "未评定",
};

export default function App() {
  const [curriculum, setCurriculum] = useState<Curriculum | null>(null);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [sectionId, setSectionId] = useState<string | null>(null);
  const [kpId, setKpId] = useState<string | null>(null);
  const [events, setEvents] = useState<DemoEvent[]>([]);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    invoke<Curriculum>("get_curriculum").then(setCurriculum);
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

  const section = curriculum?.sections.find((s) => s.id === sectionId) ?? null;
  const kp = section?.knowledge_points.find((k) => k.id === kpId) ?? null;

  const launch = (demoId: string) => {
    invoke<{ ok: boolean; message: string }>("launch_demo", { demoId }).then((result) => {
      setNotice(result.message);
    });
  };

  const answer = (itemId: string, correct: boolean) => {
    invoke("record_attempt", { knowledgeId: kp?.id ?? sectionId ?? "", itemId, correct });
  };

  if (!curriculum) {
    return <div className="p-8 text-stone-500">正在读取课程……</div>;
  }

  return (
    <div className="flex h-screen bg-stone-100 text-stone-900">
      {/* 左侧：课表树 */}
      <nav className="w-72 shrink-0 overflow-y-auto border-r border-stone-200 bg-white">
        <header className="border-b border-stone-200 px-4 py-4">
          <h1 className="text-lg font-semibold">{curriculum.title}</h1>
          <p className="mt-1 text-xs text-stone-500">
            编排基准：{curriculum.book.title}（GFDL）
          </p>
        </header>
        <ul className="p-2">
          {curriculum.sections.map((s) => (
            <li key={s.id}>
              <button
                onClick={() => {
                  setSectionId(s.id);
                  setKpId(s.knowledge_points[0]?.id ?? null);
                }}
                className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm ${
                  s.id === sectionId ? "bg-blue-50 text-blue-800" : "hover:bg-stone-100"
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
              {s.id === sectionId && (
                <ul className="ml-6 border-l border-stone-200 pl-2">
                  {s.knowledge_points.map((k) => (
                    <li key={k.id}>
                      <button
                        onClick={() => setKpId(k.id)}
                        className={`w-full rounded px-2 py-1.5 text-left text-xs ${
                          k.id === kpId
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
      </nav>

      {/* 右侧：知识点详情 */}
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-8 py-8">
          {!section && <p className="text-stone-500">从左侧选择一个章节开始。</p>}
          {section && !kp && (
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
          {section && kp && (
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
