import { invoke } from "@tauri-apps/api/core";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Inline } from "./Inline";
import { Rich, TaskCard } from "./Tasks";
import { KID_PREFIX, type AttemptRow, type Beat, type Lesson, type PlayerStatus, type Task } from "./types";

const mmss = (sec: number | null | undefined) =>
  sec === null || sec === undefined || sec < 0 ? "待标" : `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, "0")}`;

const store = {
  get(k: string): string | null { try { return localStorage.getItem(k); } catch { return null; } },
  set(k: string, v: string) { try { localStorage.setItem(k, v); } catch { /* 隐私模式等：记不住就算了 */ } },
};

/** 「边看边标」记录：节拍起止与暂停点的秒数，先存本机，确认后再写进内容文件。 */
type Marks = { beats: Record<string, { start?: number; end?: number }>; tasks: Record<string, number> };

export default function Workbench({ lesson, attempts, onAttempt }: {
  lesson: Lesson; attempts: AttemptRow[]; onAttempt: (itemId: string, correct: boolean) => void;
}) {
  const [status, setStatus] = useState<PlayerStatus | null>(null);
  const [ready, setReady] = useState(false);
  const [active, setActive] = useState<Task | null>(null);
  const [doneIds, setDoneIds] = useState<Set<string>>(() => new Set(JSON.parse(store.get(`advvideo.done.${lesson.id}`) ?? "[]")));
  const [notes, setNotes] = useState<Record<string, string>>(() => JSON.parse(store.get(`advvideo.notes.${lesson.id}`) ?? "{}"));
  const [marks, setMarks] = useState<Marks>({ beats: {}, tasks: {} });
  const [marking, setMarking] = useState(false);
  const [loginMode, setLoginMode] = useState(false);
  const [playerOn, setPlayerOn] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const statusRef = useRef<PlayerStatus | null>(null);
  const t = status?.t ?? 0;

  const atOf = useCallback((task: Task) => (task.at !== undefined && task.at !== null ? task.at : marks.tasks[task.id]), [marks]);
  const allTasks = useMemo(() => lesson.beats.flatMap((b) => b.tasks), [lesson]);

  // 载入课节：让播放窗格加载这一集，并读回「边看边标」的记录。
  useEffect(() => {
    setReady(false);
    setActive(null);
    invoke("player_load", { bvid: lesson.video.bvid, p: lesson.video.p }).catch((e) => setErr(String(e)));
    invoke<Marks | null>("load_marks", { lessonId: lesson.id }).then((m) => m && setMarks(m)).catch(() => undefined);
  }, [lesson.id, lesson.video.bvid, lesson.video.p]);

  // 下一个暂停点：播放位置之后、还没做的、已有时间戳的任务里最早的一个。
  const nextPausePoint = useCallback((from: number) => {
    const cands = allTasks.filter((k) => !doneIds.has(k.id)).map(atOf).filter((x): x is number => typeof x === "number" && x > from);
    return cands.length ? Math.min(...cands) : -1;
  }, [allTasks, doneIds, atOf]);

  const armPausePoint = useCallback((from: number) => {
    void invoke("player_set_pause_point", { t: nextPausePoint(from) });
  }, [nextPausePoint]);

  // 播放桥上报的处理函数每次渲染都换新（闭包里要用最新的 doneIds、marks）；轮询本身只建一次。
  const onStatus = useRef<(s: PlayerStatus, discrete: boolean) => void>(() => undefined);
  onStatus.current = (s: PlayerStatus, discrete: boolean) => {
    statusRef.current = s;
    setReady(true); // 任何一条上报都说明播放窗格在线
    if (discrete) {
      if (s.ev === "ready") { const from = lesson.video.start ?? 0; armPausePoint(from); if (from > 0) void invoke("player_seek", { t: from }); }
      if (s.ev === "pausepoint") {
        const hit = allTasks.find((k) => !doneIds.has(k.id) && atOf(k) !== undefined && Math.abs((atOf(k) as number) - Number(s.note)) < 0.01);
        if (hit) setActive(hit);
      }
    }
    setStatus(s);
  };
  // 不用前端事件 API（ui webview 里被 ACL 拒绝）：每 250ms 向 Rust 取一次最近状态与离散事件。
  useEffect(() => {
    let alive = true;
    const timer = setInterval(() => {
      invoke<{ last: PlayerStatus | null; events: PlayerStatus[] } | null>("player_poll")
        .then((r) => {
          if (!alive || !r) return;
          r.events.forEach((ev) => onStatus.current(ev, true));
          if (r.last && r.events.length === 0) onStatus.current(r.last, false);
        })
        .catch(() => undefined);
    }, 250);
    void invoke("player_ping").catch(() => undefined);
    return () => { alive = false; clearInterval(timer); };
  }, []);

  useEffect(() => { store.set(`advvideo.done.${lesson.id}`, JSON.stringify([...doneIds])); }, [doneIds, lesson.id]);
  useEffect(() => { store.set(`advvideo.notes.${lesson.id}`, JSON.stringify(notes)); }, [notes, lesson.id]);

  const currentBeat: Beat | undefined = useMemo(() => {
    const timed = lesson.beats.filter((b) => b.start !== null && (b.start as number) <= t);
    return timed.length ? timed[timed.length - 1] : undefined;
  }, [lesson.beats, t]);

  const finishTask = (task: Task) => {
    setDoneIds((d) => new Set(d).add(task.id));
    setActive(null);
  };

  const resume = (task?: Task) => {
    if (task) finishTask(task);
    // 完成后的下一个暂停点要排除刚做完的这个：doneIds 的更新在下一次渲染才生效，所以这里自己算
    const left = allTasks.filter((k) => !doneIds.has(k.id) && k.id !== task?.id).map(atOf).filter((x): x is number => typeof x === "number" && x > (statusRef.current?.t ?? 0));
    void invoke("player_set_pause_point", { t: left.length ? Math.min(...left) : -1 });
    void invoke("player_play");
  };

  const mark = (kind: "start" | "end" | "task", id: string) => {
    const now = statusRef.current?.t;
    if (now === undefined || now < 0) return;
    setMarks((m) => {
      const next: Marks = JSON.parse(JSON.stringify(m));
      if (kind === "task") next.tasks[id] = Math.round(now * 10) / 10;
      else { next.beats[id] = { ...next.beats[id], [kind]: Math.round(now * 10) / 10 }; }
      void invoke("save_marks", { lessonId: lesson.id, marks: next });
      return next;
    });
  };

  const gradedDone = allTasks.filter((k) => (k.kind === "quick" || k.kind === "workout") && doneIds.has(k.id)).length;
  const gradedAll = allTasks.filter((k) => k.kind === "quick" || k.kind === "workout").length;
  const doneAll = allTasks.filter((k) => doneIds.has(k.id)).length;
  const recorded = (k: Task) => attempts.some((a) => a.knowledge_id === KID_PREFIX + lesson.id && a.item_id === `${lesson.id}.${k.id}`);

  return (
    <div className="bench">
      <header className="bench-head">
        <div>
          <h1>{lesson.title}</h1>
          <p className="muted">第 {lesson.video.p} 集 · {lesson.video.outline} · {mmss(lesson.video.duration)}{lesson.video.start !== undefined && ` · 本课 ${mmss(lesson.video.start)}–${mmss(lesson.video.end)}`}</p>
        </div>
        <div className="bench-actions">
          {loginMode ? (
            <button className="on" onClick={() => { setLoginMode(false); setReady(false); void invoke("player_load", { bvid: lesson.video.bvid, p: lesson.video.p }).catch((e) => setErr(String(e))); }}>登录完成，回到视频</button>
          ) : (
            <button onClick={() => { setLoginMode(true); void invoke("player_open_login").catch((e) => setErr(String(e))); }} title="右侧窗格会换成 B 站官方登录页；登录与清晰度由你自己处理">登录 B 站</button>
          )}
          <button onClick={() => { const v = !playerOn; setPlayerOn(v); void invoke("player_set_visible", { visible: v }); }}>{playerOn ? "收起视频" : "展开视频"}</button>
          <button className={marking ? "on" : ""} onClick={() => setMarking((v) => !v)}>边看边标</button>
        </div>
      </header>
      {err && <p className="verdict bad">出错了：{err}</p>}

      {loginMode && <p className="stage-note">右侧已换成 B 站官方登录页：请在那里扫码或输入账号登录。登录后可在播放器里选清晰度；弄好了点上方「登录完成，回到视频」。</p>}
      <div className="statusbar">
        <span className={ready ? "dot on" : "dot"} />
        <span>{ready ? (status?.paused ? "已暂停" : "播放中") : "播放窗格载入中…"} · {mmss(t)} / {mmss(status?.duration || lesson.video.duration)}</span>
        <span className="spacer" />
        <span>任务 {doneAll}/{allTasks.length} · 进掌握度的 {gradedDone}/{gradedAll}</span>
        {ready && status?.paused && !active && <button className="link" onClick={() => resume()}>继续播放</button>}
      </div>

      {active ? (
        <section className="stage">
          <div className="stage-note">视频已暂停，先做这一题</div>
          <TaskCard
            key={active.id}
            task={active}
            onAnswer={(ok) => onAttempt(`${lesson.id}.${active.id}`, ok)}
            onContinue={() => resume(active)}
            onSkip={() => resume(active)}
          />
        </section>
      ) : (
        <>
          <section className="card opening">
            <h2>本节目标</h2>
            <Rich text={lesson.opening.goal} />
            {lesson.opening.predict && (
              <TaskCard
                task={lesson.opening.predict}
                onAnswer={(ok) => onAttempt(`${lesson.id}.${lesson.opening.predict!.id}`, ok)}
                onContinue={() => { void invoke("player_seek", { t: lesson.video.start ?? 0 }); void invoke("player_play"); }}
              />
            )}
          </section>

          <section className="beats">
            <h2>节拍</h2>
            {lesson.beats.map((b, i) => {
              const m = marks.beats[b.id] ?? {};
              const start = b.start ?? m.start ?? null;
              const isNow = currentBeat?.id === b.id;
              return (
                <article key={b.id} className={`beat${isNow ? " now" : ""}`}>
                  <header>
                    <button className="link" disabled={start === null} onClick={() => start !== null && void invoke("player_seek", { t: start })}>
                      {i + 1}. {b.title}
                    </button>
                    <span className="muted">{mmss(start)}</span>
                    {marking && (
                      <span className="marks">
                        <button onClick={() => mark("start", b.id)}>标起点</button>
                        <button onClick={() => mark("end", b.id)}>标终点</button>
                      </span>
                    )}
                  </header>
                  <ul className="beat-tasks">
                    {b.tasks.map((k) => {
                      const at = atOf(k);
                      return (
                        <li key={k.id} className={doneIds.has(k.id) ? "done" : ""}>
                          <button className="link" onClick={() => { void invoke("player_pause"); setActive(k); }}>
                            {k.kind === "predict" ? "预测" : k.kind === "selfexplain" ? "自我解释" : k.kind === "quick" ? "速答" : "先自己算"}
                          </button>
                          <span className="muted"> {doneIds.has(k.id) ? (recorded(k) ? "已作答" : "已完成") : "暂停点 " + mmss(at)}</span>
                          {marking && <button onClick={() => mark("task", k.id)}>标暂停点</button>}
                        </li>
                      );
                    })}
                  </ul>
                  <div className="takeaway"><span className="tag">要点</span> <Inline text={b.takeaway} /></div>
                </article>
              );
            })}
          </section>

          <section className="card closing">
            <h2>收尾</h2>
            <p className="muted">不看视频，做完出口题，再用自己的话改写本节要点。</p>
            {lesson.closing.exit.map((k) => (
              <button key={k.id} className="link" onClick={() => { void invoke("player_pause"); setActive(k); }}>
                {doneIds.has(k.id) ? "✓ " : ""}出口题：{k.kind === "quick" ? "速答" : "先自己算"} {k.id}
              </button>
            ))}
            <label>
              <Inline text={lesson.closing.note_prompt} />
              <textarea rows={4} value={notes.closing ?? ""} onChange={(e) => setNotes({ ...notes, closing: e.target.value })} placeholder="用自己的话写，写完就留在这里，下次复习时会看到" />
            </label>
          </section>
        </>
      )}
    </div>
  );
}
