import { useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";
import { Check, Flame, Lock, Sparkles, Star } from "lucide-react";
import {
  bestSentence,
  highSchoolUnits,
  initialTasks,
  sentenceOfTheDay as s,
  streakDays,
  weekMinutes,
  type Task,
} from "@/data/demo";
import { useNavigate } from "react-router";
import { Celebration } from "@/components/Celebration";
import { todaySet } from "@/content";
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

  return (
    <div className="mx-auto grid max-w-6xl grid-cols-12 gap-5">
      <Celebration show={celebrate} message="今天完成啦！" />

      <section className="col-span-12 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-4xl font-semibold leading-tight text-balance">
            {greeting(new Date().getHours())}，今天学一组
            <em className="text-accent [:root[data-style=night]_&]:gradient-text [:root[data-style=night]_&]:not-italic">
              好句子
            </em>
            吧
          </h1>
          <p className="mt-1 text-muted">读、写、听完今天的 6 个句子，再复习 12 个词，今天就完成了。</p>
        </div>
        <div className="flex items-center gap-2.5 rounded-full bg-surface-strong px-4 py-2.5 text-sm shadow-skin">
          <motion.span
            animate={{ scale: [1, 1.15, 1], rotate: [0, -4, 0] }}
            transition={{ duration: 1.6, repeat: Infinity }}
          >
            <Flame size={22} className="fill-accent text-accent" />
          </motion.span>
          连续学习 <b className="font-display text-2xl text-accent tabular-nums">{streakDays}</b> 天
        </div>
      </section>

      <SentenceCard />
      <PlanPanel tasks={tasks} progress={progress} doneCount={doneCount} total={required.length} onToggle={toggle} />
      <MapPanel />
      <WeekPanel />
      <BestPanel />

      <p className="col-span-12 text-xs text-muted">首页数字和“本周最佳”都是示例数据；今日一句是真实句子。</p>
    </div>
  );
}

function SentenceCard() {
  const [flipped, setFlipped] = useState(false);
  const [before, after] = s.en.split(s.focus);
  return (
    <section className="relative col-span-12 [perspective:1400px] lg:col-span-7 [:root[data-style=journal]_&]:rotate-[var(--tilt)]">
      <div
        aria-hidden
        className="absolute -top-3 left-[40%] z-10 hidden h-6 w-28 rotate-3 bg-accent/45 [:root[data-style=journal]_&]:block"
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
        className="relative h-full min-h-[300px] cursor-pointer rounded-skin [transform-style:preserve-3d]"
      >
        <div className="absolute inset-0 flex flex-col rounded-skin border border-line bg-surface-strong p-7 shadow-skin [backface-visibility:hidden] [:root[data-style=night]_&]:bg-[linear-gradient(150deg,rgba(255,95,174,.28),rgba(108,91,255,.22))]">
          <Tags items={["今日一句", s.grammar]} />
          <p className="en my-auto font-sentence text-[30px] leading-snug text-pretty [:root[data-style=journal]_&]:text-[32px]">
            {before}
            <mark className="bg-transparent font-word font-bold text-accent [:root[data-style=night]_&]:[text-shadow:0_0_18px_rgba(255,95,174,.6)]">
              {s.focus}
            </mark>
            {after}
          </p>
          <div className="flex flex-wrap justify-between gap-2 text-[13px] text-muted">
            <span>先读句子，猜猜 {s.focus} 的意思</span>
            <span>点击翻面 ↻</span>
          </div>
        </div>

        <div className="absolute inset-0 flex flex-col gap-2 rounded-skin border border-line bg-surface-strong p-7 shadow-skin [backface-visibility:hidden] [transform:rotateY(180deg)]">
          <div className="flex items-baseline gap-3">
            <span className="font-word text-4xl font-semibold text-word">{s.word.text}</span>
            <span className="text-muted">
              {s.word.ipa} · {s.word.pos}
            </span>
          </div>
          <p className="en font-sentence text-lg italic [:root[data-style=night]_&]:not-italic [:root[data-style=journal]_&]:text-2xl [:root[data-style=journal]_&]:not-italic">
            {s.word.simpleEn}
          </p>
          <p className="text-xl font-medium">{s.word.cn}</p>
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
  const C = 2 * Math.PI * 42;
  return (
    <section className="glass col-span-12 flex flex-col p-5 lg:col-span-5">
      <p className="mb-3 text-xs tracking-widest text-muted">今日计划</p>
      <div className="mb-4 flex items-center gap-4">
        <svg viewBox="0 0 100 100" className="h-24 w-24 flex-none" aria-hidden>
          <defs>
            <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="var(--accent)" />
              <stop offset="1" stopColor="var(--accent-2)" />
            </linearGradient>
          </defs>
          <circle cx="50" cy="50" r="42" fill="none" strokeWidth="10" stroke="var(--line)" />
          <motion.circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            strokeWidth="10"
            stroke="url(#ring)"
            strokeLinecap="round"
            strokeDasharray={C}
            transform="rotate(-90 50 50)"
            initial={{ strokeDashoffset: C }}
            animate={{ strokeDashoffset: C * (1 - progress) }}
            transition={{ duration: 1.1, ease: "easeOut" }}
          />
          <text x="50" y="57" textAnchor="middle" className="fill-fg font-display text-[20px] font-bold">
            {Math.round(progress * 100)}%
          </text>
        </svg>
        <p className="text-sm text-muted">
          <b className="block text-base text-fg">
            {doneCount} / {total} 项必做完成
          </b>
          点一项标记完成，全部做完有惊喜
        </p>
      </div>
      <ul className="grid gap-2">
        {tasks.map((t) => (
          <li key={t.id}>
            <button
              type="button"
              onClick={() => onToggle(t.id)}
              className={cn(
                "flex w-full items-center gap-3 rounded-2xl border border-line bg-surface-strong px-3 py-2.5 text-left text-sm transition-transform hover:-translate-y-0.5",
                t.done && "opacity-75",
              )}
            >
              <span className="grid h-8 w-8 flex-none place-items-center rounded-xl bg-bg-2 text-[13px] font-bold text-accent">
                {STEP_LABEL[t.step]}
              </span>
              <span className="min-w-0 flex-1">
                {t.title}
                <small className="block text-xs text-muted">{t.detail}</small>
              </span>
              {t.done ? (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="grid h-6 w-6 place-items-center rounded-full bg-accent text-on-accent"
                >
                  <Check size={14} strokeWidth={3} />
                </motion.span>
              ) : (
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-xs",
                    t.optional ? "bg-accent-2/20" : "border border-line text-muted",
                  )}
                >
                  {t.optional ? "鼓励项" : "待完成"}
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
  const lit = highSchoolUnits.filter((u) => u.state === "lit").length;
  return (
    <section className="glass col-span-12 p-5 md:col-span-6 lg:col-span-4">
      <p className="mb-2 text-xs tracking-widest text-muted">高中英语知识地图</p>
      <p className="font-display text-4xl font-semibold tabular-nums">
        {lit}
        <small className="ml-1 font-body text-sm text-muted">/ {highSchoolUnits.length} 个单元已点亮</small>
      </p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {highSchoolUnits.map((u) => (
          <span
            key={u.id}
            className={cn(
              "flex items-center gap-1 rounded-full px-2.5 py-1 text-xs",
              u.state === "lit" && "bg-accent text-on-accent shadow-skin",
              u.state === "learning" && "border border-accent text-accent",
              u.state === "locked" && "border border-line text-muted",
            )}
          >
            {u.state === "lit" && <Sparkles size={12} />}
            {u.state === "locked" && <Lock size={11} />}
            {u.name}
          </span>
        ))}
      </div>
    </section>
  );
}

function WeekPanel() {
  const max = useMemo(() => Math.max(...weekMinutes.map((d) => d.minutes)), []);
  const total = weekMinutes.reduce((sum, d) => sum + d.minutes, 0);
  return (
    <section className="glass col-span-12 p-5 md:col-span-6 lg:col-span-4">
      <p className="mb-2 text-xs tracking-widest text-muted">这 7 天的学习</p>
      <p className="font-display text-4xl font-semibold tabular-nums">
        {total}
        <small className="ml-1 font-body text-sm text-muted">分钟</small>
      </p>
      <div className="mt-3 flex h-16 items-end gap-1.5">
        {weekMinutes.map((d, i) => (
          <motion.i
            key={d.day}
            title={`${d.day}：${d.minutes} 分钟`}
            className={cn(
              "flex-1 rounded-t-md rounded-b-sm bg-[linear-gradient(var(--accent),var(--accent-2))] opacity-80",
              d.day === "今" && "opacity-100 shadow-[0_0_14px_var(--accent)]",
            )}
            initial={{ height: 0 }}
            animate={{ height: `${(d.minutes / max) * 100}%` }}
            transition={{ delay: 0.05 * i, duration: 0.6, ease: "easeOut" }}
          />
        ))}
      </div>
      <div className="mt-1 flex gap-1.5 text-[11px] text-muted">
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
    <section className="glass relative col-span-12 p-5 lg:col-span-4">
      <p className="mb-2 flex items-center gap-1.5 text-xs tracking-widest text-muted">
        <Star size={13} className="fill-accent text-accent" />
        本周最佳 · 你写的句子
      </p>
      <p className="en font-sentence text-xl leading-snug [:root[data-style=journal]_&]:text-2xl">{bestSentence.en}</p>
      <p className="mt-3 border-l-[3px] border-accent-2 pl-2.5 text-[13px] text-muted">{bestSentence.note}</p>
      <div
        aria-hidden
        className="absolute bottom-4 right-4 hidden h-[70px] w-[70px] rotate-12 place-items-center rounded-full bg-[#f7d06b] text-center font-[Caveat] text-[15px] font-bold leading-tight text-[#6b4a12] shadow-[2px_3px_0_rgba(90,70,40,.18)] [:root[data-style=journal]_&]:grid"
      >
        Keep
        <br />
        going!
      </div>
    </section>
  );
}
