import { invoke } from "@tauri-apps/api/core";
import { useCallback, useEffect, useState } from "react";
import { KID_PREFIX, type AttemptRow, type Curriculum, type Lesson } from "./types";
import Workbench from "./Workbench";

const store = {
  get(k: string): string | null { try { return localStorage.getItem(k); } catch { return null; } },
  set(k: string, v: string) { try { localStorage.setItem(k, v); } catch { /* 隐私模式等：记不住就算了 */ } },
};

export default function App() {
  const [cur, setCur] = useState<Curriculum | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [sel, setSel] = useState<string>(() => store.get("wengc.sel") ?? "");
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [attempts, setAttempts] = useState<AttemptRow[]>([]);

  useEffect(() => {
    invoke<Curriculum>("get_curriculum").then(setCur).catch((e) => setErr(String(e)));
    invoke<AttemptRow[]>("get_attempts").then(setAttempts).catch(() => setAttempts([]));
  }, []);

  const items = cur ? cur.chapters.flatMap((c) => c.items) : [];
  useEffect(() => {
    if (!cur) return;
    if (!sel || !items.some((i) => i.id === sel)) setSel(items[0]?.id ?? "");
  }, [cur]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!sel) return;
    store.set("wengc.sel", sel);
    setLesson(null);
    invoke<Lesson>("get_lesson", { lessonId: sel }).then(setLesson).catch((e) => setErr(String(e)));
  }, [sel]);

  const onAttempt = useCallback((itemId: string, correct: boolean) => {
    const knowledgeId = KID_PREFIX + itemId.split(".")[0];
    const row: AttemptRow = { knowledge_id: knowledgeId, item_id: itemId, correct, answered_at: Math.floor(Date.now() / 1000) };
    setAttempts((a) => [...a, row]);
    void invoke("record_attempt", { knowledgeId, itemId, correct });
  }, []);

  if (err) return <div className="boot-error">出错了：{err}</div>;
  if (!cur) return <div className="boot">载入中…</div>;
  if (items.length === 0) return <div className="boot">还没有课节。</div>;

  return (
    <div className="app">
      <nav className="side">
        <div className="brand">
          <h1>翁恺 C 语言</h1>
          <p>课堂工作台 · {items.length} 节</p>
        </div>
        {cur.chapters.map((ch) => (
          <div key={ch.id} className="chapter">
            <h2>{ch.title}</h2>
            {ch.items.map((it) => (
              <button key={it.id} className={`item${sel === it.id ? " active" : ""}`} onClick={() => setSel(it.id)}>
                <span>{it.title}</span>
              </button>
            ))}
          </div>
        ))}
      </nav>
      <main id="main" className="main">
        {lesson ? <Workbench key={lesson.id} lesson={lesson} attempts={attempts} onAttempt={onAttempt} /> : <div className="boot">载入中…</div>}
      </main>
    </div>
  );
}
