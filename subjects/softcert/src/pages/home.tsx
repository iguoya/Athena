import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { ArrowRight, ScrollText, Gauge, CalendarClock, Target, BookOpen } from "lucide-react";
import { courses, registry, allSections } from "../content";
import { attemptsSummary, loadSetting, type KpSummary } from "../db";
import { ProgressRing, GradeBadge } from "../components/ui";
import type { View } from "../App";

interface LastRead {
  courseId: string;
  sectionId: string;
  courseTitle: string;
  chapterTitle: string;
}

export function HomePage({ go }: { go: (v: View) => void }) {
  const [summary, setSummary] = useState<KpSummary[]>([]);
  const [last, setLast] = useState<LastRead | null>(null);
  useEffect(() => {
    attemptsSummary().then(setSummary).catch(() => {});
    loadSetting("last-read")
      .then((v) => {
        if (v) setLast(JSON.parse(v) as LastRead);
      })
      .catch(() => {});
  }, []);

  const mastery = (kpId?: string) => {
    if (!kpId) return 0;
    const s = summary.find((x) => x.kp_id === kpId);
    if (!s || s.total === 0) return 0;
    return Math.min(1, s.correct / s.total) * Math.min(1, s.total / 8);
  };

  return (
    <div className="space-y-8">
      {/* hero */}
      <section className="hero-gradient -mx-5 -mt-0 px-5 pb-10 pt-12">
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-brand-500 px-3 py-1 text-[12px] font-bold text-white shadow">
              {registry.exam.name}
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-white/70 px-3 py-1 text-[12px] font-medium text-ink/70 ring-1 ring-black/5">
              <Target size={12} /> 两科同时 ≥{registry.exam.passing_score} 分通过
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-white/70 px-3 py-1 text-[12px] font-medium text-ink/70 ring-1 ring-black/5">
              <CalendarClock size={12} /> 嵌入式一年一考,2024 年起为 5 月底
            </span>
          </div>
          <h1 className="mt-4 text-[32px] font-bold leading-snug tracking-tight">
            考纲对齐、分值驱动的
            <span className="bg-gradient-to-r from-brand-600 to-fuchsia-600 bg-clip-text text-transparent"> 软考备考</span>
          </h1>
          <p className="mt-2 max-w-3xl text-[15px] leading-relaxed text-ink/65">
            {registry.exam.facts[3]}。先从这里两门共用课程学起:上午卷的核心拿分区,
            也是下午大题的地基;每章带分值权重、课后考核与出处可查的练习题。
          </p>
        </motion.div>
      </section>

      {/* 续读 */}
      {last && (
        <motion.button
          type="button"
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={() => go({ kind: "topic", courseId: last.courseId, sectionId: last.sectionId })}
          className="card card-hover flex w-full items-center gap-3 border-brand-200/70 bg-gradient-to-r from-brand-50/80 to-white px-5 py-3.5 text-left"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500 text-white shadow">
            <BookOpen size={17} />
          </span>
          <span className="flex-1 text-[14px]">
            <span className="font-semibold">接着学</span>
            <span className="ml-2 text-ink/60">{last.courseTitle} · {last.chapterTitle}</span>
          </span>
          <ArrowRight size={16} className="text-brand-500" />
        </motion.button>
      )}

      {/* 课程卡 */}
      <section className="grid gap-5 md:grid-cols-2">
        {courses.map((c, i) => {
          const sections = c.chapters.flatMap((ch) => ch.sections);
          const graded = sections.filter((s) => s.kp);
          const avg = graded.length
            ? graded.reduce((acc, s) => acc + mastery(s.kp!.id), 0) / graded.length
            : 0;
          const done = graded.filter((s) => mastery(s.kp!.id) >= 0.6).length;
          return (
            <motion.button
              key={c.id}
              type="button"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08 * (i + 1), duration: 0.45 }}
              onClick={() => go({ kind: "course", courseId: c.id })}
              className="card card-hover group relative overflow-hidden p-6 text-left"
            >
              <div
                className="absolute -right-10 -top-10 h-36 w-36 rounded-full opacity-[0.07] transition-transform duration-500 group-hover:scale-150"
                style={{ background: c.accent }}
              />
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <GradeBadge grade={c.exam.grade} />
                    <span className="text-[12px] font-medium text-ink/45">{c.exam.subject}</span>
                  </div>
                  <h2 className="mt-2 text-[22px] font-bold" style={{ color: c.accent }}>
                    {c.title}
                  </h2>
                  <p className="mt-1.5 text-[13.5px] leading-relaxed text-ink/60">{c.tagline}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12.5px] text-ink/50">
                    <span>依据《{c.textbook.title}》</span>
                    <span>· {c.textbook.chapters_total} 章 {sections.length} 节 · 已拿下 {done} 节</span>
                  </div>
                </div>
                <ProgressRing value={avg} size={64} stroke={7} color={c.accent}>
                  <span className="text-[13px] font-bold" style={{ color: c.accent }}>
                    {Math.round(avg * 100)}%
                  </span>
                </ProgressRing>
              </div>
              <div className="mt-4 flex items-center gap-1 text-[13px] font-semibold" style={{ color: c.accent }}>
                进入学习 <ArrowRight size={15} className="transition-transform group-hover:translate-x-1" />
              </div>
            </motion.button>
          );
        })}
      </section>

      {/* 真题与战况入口 */}
      <section className="grid gap-5 sm:grid-cols-2">
        <button type="button" onClick={() => go({ kind: "past" })} className="card card-hover flex items-center gap-4 p-5 text-left">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-fuchsia-500 to-purple-600 text-white shadow-lg">
            <ScrollText size={22} />
          </span>
          <span>
            <span className="block font-bold">历年真题演练</span>
            <span className="block text-[13px] text-ink/55">按年份成卷;真题整卷待授权导入,格式已就绪</span>
          </span>
        </button>
        <button type="button" onClick={() => go({ kind: "dashboard" })} className="card card-hover flex items-center gap-4 p-5 text-left">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg">
            <Gauge size={22} />
          </span>
          <span>
            <span className="block font-bold">掌握度战况</span>
            <span className="block text-[13px] text-ink/55">
              共 {allSections().length} 节 · 全部由作答记录派生
            </span>
          </span>
        </button>
      </section>
    </div>
  );
}
