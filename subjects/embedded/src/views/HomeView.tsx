// 首页 = 行动面板:打开就是「现在学什么」——接着学(或开始学习)是主卡,
// 真题/战况其次,课程时间线入口垫底。与 softcert 的「大标语 hero + 介绍」
// 刻意区分(ADR 0090:两种体验,好做对比)。
import { useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";
import { ArrowRight, ScrollText, Gauge, Target, CalendarClock, BookOpen, Play } from "lucide-react";
import { course, allSections, masteryOf } from "../content";
import { attemptsSummary, loadSetting } from "../db";
import type { KpSummary } from "../types";
import ProgressRing from "../components/ProgressRing";
import type { View } from "./types";

interface LastRead {
  sectionId: string;
  chapterTitle: string;
  sectionTitle: string;
}

const sections = course.chapters.flatMap((ch) => ch.sections);
const graded = sections.filter((s) => s.kp);
const firstSection = sections.find((s) => s.kp) ?? sections[0];

const chipStyle = {
  background: "var(--tk-surface)",
  color: "var(--tk-muted)",
  borderColor: "var(--tk-line)",
};

export default function HomeView({ go }: { go: (v: View) => void }) {
  const [summary, setSummary] = useState<KpSummary[]>([]);
  const [last, setLast] = useState<LastRead | null>(null);

  useEffect(() => {
    attemptsSummary()
      .then(setSummary)
      .catch(() => {});
    loadSetting("last-read")
      .then((v) => {
        if (v) {
          const parsed = JSON.parse(v) as LastRead;
          // 只在节还存在时展示续读(内容重组后旧位置自然失效)
          if (allSections().some((s) => s.section.id === parsed.sectionId)) setLast(parsed);
        }
      })
      .catch(() => {});
  }, []);

  const avg = useMemo(
    () =>
      graded.length
        ? graded.reduce((acc, s) => acc + masteryOf(s.kp!.id, summary), 0) / graded.length
        : 0,
    [summary],
  );
  const done = useMemo(
    () => graded.filter((s) => masteryOf(s.kp!.id, summary) >= 0.6).length,
    [summary],
  );

  // 行动卡目标:续读优先,否则第一个有内容的节
  const action = useMemo(() => {
    if (last) {
      const meta = allSections().find((s) => s.section.id === last.sectionId);
      return {
        sectionId: last.sectionId,
        kicker: "接着学",
        title: last.sectionTitle,
        sub: last.chapterTitle,
        guide: meta?.section.kp?.guide_line ?? "",
      };
    }
    return {
      sectionId: firstSection.id,
      kicker: "开始学习",
      title: firstSection.title,
      sub: `第 ${course.chapters.find((ch) => ch.sections.some((s) => s.id === firstSection.id))?.no ?? ""} 章`,
      guide: firstSection.kp?.guide_line ?? "",
    };
  }, [last]);

  return (
    <div className="space-y-6">
      {/* 紧凑事实行 */}
      <div className="flex flex-wrap items-center gap-2 pt-2">
        <span className="accent-gradient rounded-full px-3 py-1 text-[12px] font-bold text-white shadow">
          {course.exam.subject}
        </span>
        <span
          className="inline-flex items-center gap-1 rounded-full px-3 py-1 text-[12px] font-medium ring-1"
          style={chipStyle}
        >
          <Target size={12} /> {course.exam.score_range}
        </span>
        <span
          className="inline-flex items-center gap-1 rounded-full px-3 py-1 text-[12px] font-medium ring-1"
          style={chipStyle}
        >
          <CalendarClock size={12} /> 一年一考,2024 年起为 5 月底
        </span>
      </div>

      {/* 行动卡:现在学什么 */}
      <motion.button
        type="button"
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        className="tk-card tk-card-hover relative w-full overflow-hidden p-6 text-left"
        style={{
          border: "2px solid transparent",
          background: `linear-gradient(var(--tk-surface), var(--tk-surface)) padding-box,
            linear-gradient(135deg, var(--tk-accent-from), var(--tk-accent-to)) border-box`,
        }}
        onClick={() => go({ kind: "topic", sectionId: action.sectionId })}
      >
        <div
          className="absolute -right-12 -top-12 h-40 w-40 rounded-full opacity-[0.10]"
          style={{ background: course.accent }}
        />
        <div className="flex items-center gap-5">
          <span className="accent-gradient flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl text-white shadow-lg">
            <Play size={24} />
          </span>
          <span className="min-w-0 flex-1">
            <span className="accent-fg text-[12px] font-bold uppercase tracking-widest">{action.kicker}</span>
            <span className="tk-display mt-0.5 block truncate text-[24px] font-bold">{action.title}</span>
            <span className="mt-0.5 block text-[13px]" style={{ color: "var(--tk-muted)" }}>
              {action.sub}
              {action.guide ? ` · ${action.guide}` : ""}
            </span>
          </span>
          <span className="accent-gradient flex shrink-0 items-center gap-1 rounded-full px-4 py-2 text-[13.5px] font-semibold text-white shadow">
            进入 <ArrowRight size={15} />
          </span>
        </div>
      </motion.button>

      <p
        className="text-[12.5px] leading-relaxed"
        style={{ color: "color-mix(in srgb, var(--tk-muted) 85%, transparent)" }}
      >
        考纲对齐、分值驱动:菜单目录对齐官方教材,每章带分值权重与出处可查的练习题;{course.exam.note}
      </p>

      {/* 真题与战况 */}
      <section className="grid gap-4 sm:grid-cols-2">
        <button
          type="button"
          className="tk-card tk-card-hover flex items-center gap-4 p-5 text-left"
          onClick={() => go({ kind: "past" })}
        >
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-lg">
            <ScrollText size={20} />
          </span>
          <span>
            <span className="block font-bold">历年真题演练</span>
            <span className="block text-[13px]" style={{ color: "var(--tk-muted)" }}>
              2010–2020 十一卷整卷练习
            </span>
          </span>
        </button>
        <button
          type="button"
          className="tk-card tk-card-hover flex items-center gap-4 p-5 text-left"
          onClick={() => go({ kind: "dashboard" })}
        >
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg">
            <Gauge size={20} />
          </span>
          <span>
            <span className="block font-bold">掌握度战况</span>
            <span className="block text-[13px]" style={{ color: "var(--tk-muted)" }}>
              共 {allSections().length} 节 · {done} 节已拿下
            </span>
          </span>
        </button>
      </section>

      {/* 课程时间线入口 */}
      <section>
        <motion.button
          type="button"
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08, duration: 0.4 }}
          className="tk-card tk-card-hover group relative w-full overflow-hidden p-5 text-left"
          onClick={() => go({ kind: "course" })}
        >
          <div className="flex items-center gap-4">
            <span className="accent-soft accent-fg flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl">
              <BookOpen size={20} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-[16px] font-bold">{course.title} · 学习路径</span>
              <span className="mt-0.5 block text-[13px]" style={{ color: "var(--tk-muted)" }}>
                依据《{course.textbook.title}》· {course.textbook.chapters_total} 章 {sections.length} 节
              </span>
            </span>
            <ProgressRing value={avg} size={52} stroke={6} color={course.accent}>
              <span className="text-[11.5px] font-bold" style={{ color: course.accent }}>
                {Math.round(avg * 100)}%
              </span>
            </ProgressRing>
          </div>
        </motion.button>
      </section>
    </div>
  );
}
