import { invoke } from "@tauri-apps/api/core";
import { useCallback, useEffect, useMemo, useState } from "react";
import { SectionView } from "./Reader";
import type { AttemptRow, Curriculum, CurriculumItem, Exercise, SectionData } from "./types";

const store = {
  get(k: string): string | null {
    try { return localStorage.getItem(k); } catch { return null; }
  },
  set(k: string, v: string) {
    try { localStorage.setItem(k, v); } catch { /* 隐私模式等：记不住就算了 */ }
  },
};

export default function App() {
  const [cur, setCur] = useState<Curriculum | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [sel, setSel] = useState<string>(() => location.hash.slice(1) || (store.get("axler.sel") ?? ""));
  const [advanced, setAdvanced] = useState<boolean>(() => store.get("axler.adv") === "1");
  const [data, setData] = useState<SectionData | null>(null);
  const [exercises, setExercises] = useState<Exercise[] | null>(null);
  const [attempts, setAttempts] = useState<AttemptRow[]>([]);

  useEffect(() => {
    invoke<Curriculum>("get_curriculum").then(setCur).catch((e) => setErr(String(e)));
    invoke<AttemptRow[]>("get_attempts").then(setAttempts).catch(() => setAttempts([]));
  }, []);

  const pages = useMemo(() => (cur ? cur.chapters.flatMap((c) => c.items.filter((i) => i.page)) : []), [cur]);

  useEffect(() => {
    if (!cur) return;
    if (!sel || !pages.some((p) => p.id === sel)) setSel(pages[0]?.id ?? "");
  }, [cur, pages, sel]);

  useEffect(() => {
    if (!sel) return;
    store.set("axler.sel", sel);
    setData(null);
    invoke<SectionData>("get_section", { sectionId: sel }).then((d) => { setData(d); document.getElementById("main")?.scrollTo(0, 0); }).catch((e) => setErr(String(e)));
    invoke<Exercise[] | null>("get_exercises", { sectionId: sel }).then(setExercises).catch(() => setExercises(null));
  }, [sel]);

  useEffect(() => store.set("axler.adv", advanced ? "1" : "0"), [advanced]);

  const onAttempt = useCallback((itemId: string, correct: boolean) => {
    const sectionId = itemId.split(".")[0];
    const row: AttemptRow = { knowledge_id: sectionId, item_id: itemId, correct, answered_at: Math.floor(Date.now() / 1000) };
    setAttempts((a) => [...a, row]);
    void invoke("record_attempt", { knowledgeId: sectionId, itemId, correct });
  }, []);

  const idx = pages.findIndex((p) => p.id === sel);
  const go = (d: number) => { const t = pages[idx + d]; if (t) setSel(t.id); };

  if (err) return <div className="boot-error">出错了：{err}</div>;
  if (!cur) return <div className="boot">载入中…</div>;

  const doneCount = (it: CurriculumItem) => {
    const last = new Map<string, boolean>();
    for (const a of attempts) if (a.knowledge_id === it.id) last.set(a.item_id, a.correct);
    return [...last.values()].filter(Boolean).length;
  };

  return (
    <div className="app">
      <nav className="side">
        <div className="brand">
          <h1>Axler 线性代数</h1>
          <p>精读 · 原书习题 · {pages.length} 章</p>
          <div className="modes" role="group" aria-label="内容深度">
            {([[false, "基础"], [true, "进阶"]] as const).map(([v, label]) => (
              <button key={String(v)} className={advanced === v ? "on" : ""} onClick={() => setAdvanced(v)}>{label}</button>
            ))}
          </div>
        </div>
        {cur.chapters.map((ch) => (
          <div key={ch.id} className="chapter">
            <h2>{ch.title}</h2>
            {ch.items.map((it) =>
              it.page ? (
                <button key={it.id} className={`item l${it.level}${sel === it.id ? " active" : ""}`} onClick={() => setSel(it.id)}>
                  <span>{it.title}</span>
                  <span className="meta">
                    {it.exercises ? `题目 ${doneCount(it)}/${it.exercises}` : ""}
                  </span>
                </button>
              ) : (
                <div key={it.id} className={`group-title l${it.level}`}>{it.title}</div>
              ),
            )}
          </div>
        ))}
      </nav>
      <main id="main" className="main">
        {data ? (
          <>
            <SectionView data={data} exercises={exercises} advanced={advanced} onAdvanced={setAdvanced} attempts={attempts} onAttempt={onAttempt} />
            <div className="pager">
              <button disabled={idx <= 0} onClick={() => go(-1)}>← 上一章</button>
              <button disabled={idx >= pages.length - 1} onClick={() => go(1)}>下一章 →</button>
            </div>
          </>
        ) : (
          <div className="boot">载入中…</div>
        )}
      </main>
    </div>
  );
}
