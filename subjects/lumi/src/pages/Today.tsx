import { useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";
import { Check, Flame, Lock, Sparkles, Star } from "lucide-react";
import {
  bestSentence,
  initialTasks,
  sentenceOfTheDay as s,
  streakDays,
  unitStates,
  weekMinutes,
  type Task,
} from "@/data/demo";
import { useNavigate } from "react-router";
import { Celebration } from "@/components/Celebration";
import { grammarUnits, todaySet } from "@/content";
import { dateKey, useProgress } from "@/store/progress";
import { cn } from "@/lib/utils";

function greeting(hour: number) {
  if (hour < 5) return "夜深了";
  if (hour < 11) return "早上好";
  if (hour < 14) return "中午好";
  if (hour < 18) return "下午好";
  return "晚上好";
}

const STEP_LABEL: Record<Task["step"], string> = { read: "读", write: "写", listen: "听", speak: "说", review: "复" };

export function Today() {
  const navigate = useNavigate();
  const [demoTasks, setTasks] = useState(initialTasks);
  const [celebrate, setCelebrate] = useState(false);
  const readDone = useProgress((p) => (p.readSets[dateKey()] ?? []).includes(todaySet().id));
  // The read step follows real progress; the other steps stay demo state until their pages exist.
  const tasks = demoTasks.map((t) => (t.id === "read" ? { ...t, done: readDone } : t));
  const required = tasks.filter((t) => !t.optional);
  const doneCount = required.filter((t) => t.done).length;
  const progress = doneCount / required.length;

  function toggle(id: string) {
    if (id === "read") return navigate("/sentences");
    const next = tasks.map((t) => (t.id === id ? { ...t, done: !t.done } : t));
    const allDone = (ts: Task[]) => ts.filter((t) => !t.optional).every((t) => t.done);
    if (allDone(next) && !allDone(tasks)) setCelebrate(true);
    setTasks(next);
  }

  useEffect(() => {
    if (!celebrate) return;
    const timer = setTimeout(() => setCelebrate(false), 2600);
    return () => clearTimeout(timer);
  }, [celebrate]);

  // Fill the viewport and shrink rows instead of overflowing (critical at 200% DPI ≈ 960 logical px).
  return (
    <>
      <Celebration show={celebrate} message="今天完成啦！" />
      <div className="mx-auto grid h-full max-w-6xl grid-cols-12 grid-rows-[auto_minmax(0,1.15fr)_minmax(0,0.85fr)] gap-x-3 gap-y-2 content-stretch">
        <section className="col-span-12 flex flex-wrap items-end justify-between gap-2">
          <div className="min-w-0">
            <h1 className="font-display text-[1.55rem] font-semibold leading-tight text-balance sm:text-[1.75rem] xl:text-3xl">
              {greeting(new Date().getHours())}，今天学一组
              <em className="text-accent [:root[data-style=night]_&]:gradient-text [:root[data-style=night]_&]:not-italic">
                好句子
              </em>
              吧
            </h1>
            <p className="mt-0.5 text-xs text-muted sm:text-sm">读、写、听完今天的 6 个句子，再复习 12 个词，今天就完成了。</p>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-surface-strong px-3 py-1.5 text-sm shadow-skin">
            <motion.span
              animate={{ scale: [1, 1.12, 1], rotate: [0, -4, 0] }}
              transition={{ duration: 1.6, repeat: Infinity }}
            >
              <Flame size={18} className="fill-accent text-accent" />
            </motion.span>
            连续学习 <b className="font-display text-lg text-accent tabular-nums">{streakDays}</b> 天
          </div>
        </section>

        <SentenceCard />
        <PlanPanel tasks={tasks} progress={progress} doneCount={doneCount} total={required.length} onToggle={toggle} />
        <MapPanel />
        <WeekPanel />
        <BestPanel />
      </div>
    </>
  );
}

function SentenceCard() {
  const [flipped, setFlipped] = useState(false);
  const [before, after] = s.en.split(s.focus);
  return (
    <section className="relative col-span-12 min-h-0 [perspective:1400px] lg:col-span-7 [:root[data-style=journal]_&]:rotate-[var(--tilt)]">
      <div
        aria-hidden
        className="absolute -top-2 left-[40%] z-10 hidden h-5 w-24 rotate-3 bg-accent/45 [:root[data-style=journal]_&]:block"
      />
      <motion.div
        role="button"
        tabIndex={0}
        aria-label="今日一句，点击翻面"
        onClick={() => setFlipped((f) => !f)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setFlipped((f) => !f);
          }
        }}
        animate={{ rotateY: flipped ? 180 : 0 }}
        transition={{ duration: 0.8, ease: [0.2, 0.8, 0.2, 1] }}
        className="relative h-full min-h-0 cursor-pointer rounded-skin [transform-style:preserve-3d]"
      >
        <div className="absolute inset-0 flex flex-col rounded-skin border border-line bg-surface-strong p-4 shadow-skin [backface-visibility:hidden] xl:p-5 [:root[data-style=night]_&]:bg-[linear-gradient(150deg,rgba(255,95,174,.28),rgba(108,91,255,.22))]">
          <Tags items={["今日一句", s.grammar]} />
          <p className="en my-auto font-sentence text-[20px] leading-snug text-pretty sm:text-[22px] xl:text-[26px] [:root[data-style=journal]_&]:text-[24px]">
            {before}
            <mark className="bg-transparent font-word font-bold text-accent [:root[data-style=night]_&]:[text-shadow:0_0_18px_rgba(255,95,174,.6)]">
              {s.focus}
            </mark>
            {after}
          </p>
          <div className="flex flex-wrap justify-between gap-2 text-[11px] text-muted">
            <span>先读句子，猜猜 {s.focus} 的意思</span>
            <span>点击翻面 ↻</span>
          </div>
        </div>

        <div className="absolute inset-0 flex flex-col gap-1 overflow-hidden rounded-skin border border-line bg-surface-strong p-4 shadow-skin [backface-visibility:hidden] [transform:rotateY(180deg)] xl:p-5">
          <div className="flex items-baseline gap-3">
            <span className="font-word text-3xl font-semibold text-word">{s.word.text}</span>
            <span className="text-sm text-muted">
              {s.word.ipa} · {s.word.pos}
            </span>
          </div>
          <p className="en font-sentence text-base italic [:root[data-style=night]_&]:not-italic [:root[data-style=journal]_&]:text-lg [:root[data-style=journal]_&]:not-italic">
            {s.word.simpleEn}
          </p>
          <p className="text-lg font-medium">{s.word.cn}</p>
          <p className="text-sm text-muted">{s.cn}</p>
          <p className="mt-auto text-xs text-muted">出处：{s.source}</p>
        </div>
      </motion.div>
    </section>
  );
}

function Tags({ items }: { items: string[] }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((t, i) => (
        <span
          key={t}
          className={cn(
            "rounded-full border border-line bg-bg-2 px-2.5 py-0.5 text-xs text-muted",
            i === 0 && "text-accent",
          )}
        >
          {t}
        </span>
      ))}
    </div>
  );
}

type PlanProps = { tasks: Task[]; progress: number; doneCount: number; total: number; onToggle: (id: string) => void };

function PlanPanel({ tasks, progress, doneCount, total, onToggle }: PlanProps) {
  const C = 2 * Math.PI * 30;
  return (
    <section className="glass col-span-12 flex min-h-0 flex-col overflow-hidden p-3 lg:col-span-5 xl:p-4">
      <div className="mb-2 flex items-center gap-3">
        <svg viewBox="0 0 100 100" className="h-14 w-14 flex-none" aria-hidden>
          <defs>
            <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="var(--accent)" />
              <stop offset="1" stopColor="var(--accent-2)" />
            </linearGradient>
          </defs>
          <circle cx="50" cy="50" r="30" fill="none" strokeWidth="8" stroke="var(--line)" />
          <motion.circle
            cx="50"
            cy="50"
            r="30"
            fill="none"
            strokeWidth="8"
            stroke="url(#ring)"
            strokeLinecap="round"
            strokeDasharray={C}
            transform="rotate(-90 50 50)"
            initial={{ strokeDashoffset: C }}
            animate={{ strokeDashoffset: C * (1 - progress) }}
            transition={{ duration: 1.1, ease: "easeOut" }}
          />
          <text x="50" y="55" textAnchor="middle" className="fill-fg font-display text-[16px] font-bold">
            {Math.round(progress * 100)}%
          </text>
        </svg>
        <div className="min-w-0">
          <p className="text-xs tracking-widest text-muted">今日计划</p>
          <p className="text-sm text-fg">
            {doneCount} / {total} 项必做完成
          </p>
        </div>
      </div>
      <ul className="grid min-h-0 flex-1 content-start gap-1 overflow-hidden">
        {tasks.map((t) => (
          <li key={t.id} className="min-h-0">
            <button
              type="button"
              onClick={() => onToggle(t.id)}
              className={cn(
                "flex w-full items-center gap-2 rounded-xl border border-line bg-surface-strong px-2 py-1.5 text-left text-[13px]",
                t.done && "opacity-75",
              )}
            >
              <span className="grid h-6 w-6 flex-none place-items-center rounded-md bg-bg-2 text-[11px] font-bold text-accent">
                {STEP_LABEL[t.step]}
              </span>
              <span className="min-w-0 flex-1 truncate leading-snug">
                {t.title}
                <small className="mt-0.5 block truncate text-[10px] text-muted">{t.detail}</small>
              </span>
              {t.done ? (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="grid h-5 w-5 place-items-center rounded-full bg-accent text-on-accent"
                >
                  <Check size={11} strokeWidth={3} />
                </motion.span>
              ) : (
                <span
                  className={cn(
                    "rounded-full px-1.5 py-0.5 text-[10px]",
                    t.optional ? "bg-accent-2/20" : "border border-line text-muted",
                  )}
                >
                  {t.optional ? "鼓励" : "待做"}
                </span>
              )}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

function MapPanel() {
  const navigate = useNavigate();
  const lit = grammarUnits.filter((u) => unitStates[u.id] === "lit").length;
  return (
    <button
      type="button"
      onClick={() => navigate("/map")}
      className="glass col-span-12 flex min-h-0 flex-col overflow-hidden p-3 text-left md:col-span-6 lg:col-span-4 xl:p-4"
    >
      <p className="text-xs tracking-widest text-muted">高中英语知识地图</p>
      <p className="font-display text-2xl font-semibold tabular-nums xl:text-3xl">
        {lit}
        <small className="ml-1 font-body text-xs text-muted">/ {grammarUnits.length} 已点亮</small>
      </p>
      <div className="mt-1.5 flex min-h-0 flex-1 flex-wrap content-start gap-1 overflow-hidden">
        {grammarUnits.map((u) => {
          const state = unitStates[u.id] ?? "locked";
          return (
            <span
              key={u.id}
              className={cn(
                "flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[10px]",
                state === "lit" && "bg-accent text-on-accent shadow-skin",
                state === "learning" && "border border-accent text-accent",
                state === "locked" && "border border-line text-muted",
              )}
            >
              {state === "lit" && <Sparkles size={10} />}
              {state === "locked" && <Lock size={9} />}
              {u.name}
            </span>
          );
        })}
      </div>
      <p className="mt-1 text-[11px] text-accent">打开完整路线图 →</p>
    </button>
  );
}

function WeekPanel() {
  const max = useMemo(() => Math.max(...weekMinutes.map((d) => d.minutes), 1), []);
  const total = weekMinutes.reduce((sum, d) => sum + d.minutes, 0);
  return (
    <section className="glass col-span-12 flex min-h-0 flex-col overflow-hidden p-3 md:col-span-6 lg:col-span-4 xl:p-4">
      <p className="text-xs tracking-widest text-muted">这 7 天的学习</p>
      <p className="font-display text-2xl font-semibold tabular-nums xl:text-3xl">
        {total}
        <small className="ml-1 font-body text-xs text-muted">分钟</small>
      </p>
      <div className="mt-1.5 flex min-h-0 flex-1 items-end gap-1">
        {weekMinutes.map((d, i) => (
          <div key={d.day} className="flex h-full min-h-[2.5rem] flex-1 items-end" title={`${d.day}：${d.minutes} 分钟`}>
            <motion.span
              className={cn(
                "block w-full origin-bottom rounded-t-md rounded-b-sm bg-[linear-gradient(var(--accent),var(--accent-2))] opacity-80",
                d.day === "今" && "opacity-100 shadow-[0_0_14px_var(--accent)]",
              )}
              style={{ height: "100%" }}
              initial={{ scaleY: 0 }}
              animate={{ scaleY: d.minutes / max }}
              transition={{ delay: 0.04 * i, duration: 0.55, ease: "easeOut" }}
            />
          </div>
        ))}
      </div>
      <div className="mt-1 flex gap-1 text-[10px] text-muted">
        {weekMinutes.map((d) => (
          <span key={d.day} className="flex-1 text-center">
            {d.day}
          </span>
        ))}
      </div>
    </section>
  );
}

function BestPanel() {
  return (
    <section className="glass relative col-span-12 flex min-h-0 flex-col overflow-hidden p-3 lg:col-span-4 xl:p-4">
      <p className="mb-1 flex items-center gap-1.5 text-xs tracking-widest text-muted">
        <Star size={12} className="fill-accent text-accent" />
        本周最佳 · 你写的句子
      </p>
      <p className="en min-h-0 flex-1 overflow-hidden font-sentence text-base leading-snug xl:text-lg [:root[data-style=journal]_&]:text-lg">
        {bestSentence.en}
      </p>
      <p className="mt-1.5 line-clamp-2 border-l-[3px] border-accent-2 pl-2 text-[11px] text-muted">{bestSentence.note}</p>
    </section>
  );
}
