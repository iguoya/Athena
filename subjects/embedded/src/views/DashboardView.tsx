// 战况页:一切数字由作答记录派生(ADR 0052)——没有记录就没有徽章。
import { useEffect, useMemo, useState } from "react";
import { Flame, CalendarCheck, TrendingUp } from "lucide-react";
import { course, allSections, masteryOf } from "../content";
import { attemptsSummary, todayStats, type TodayStats } from "../db";
import type { KpSummary } from "../types";
import { DifficultyDots, MasteryGoalBadge } from "../components/ui";
import ProgressRing from "../components/ProgressRing";

export default function DashboardView() {
  const [summary, setSummary] = useState<KpSummary[]>([]);
  const [today, setToday] = useState<TodayStats | null>(null);
  useEffect(() => {
    attemptsSummary()
      .then(setSummary)
      .catch(() => {});
    todayStats()
      .then(setToday)
      .catch(() => {});
  }, []);

  const byKp = useMemo(() => new Map(summary.map((s) => [s.kp_id, s])), [summary]);
  const totalAnswered = summary.reduce((s, x) => s + x.total, 0);
  const totalCorrect = summary.reduce((s, x) => s + x.correct, 0);
  const bestStreak = Math.max(0, ...summary.map((s) => s.streak));

  return (
    <div className="space-y-7 pt-8">
      <header>
        <h1 className="tk-display text-[26px] font-bold tracking-tight">掌握度战况</h1>
        <p className="mt-1.5 text-[14px]" style={{ color: "var(--tk-muted)" }}>
          掌握度只由作答写入:下面每个数字都来自 progress/learning.db 的作答记录。
        </p>
      </header>

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="tk-card p-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md">
              <CalendarCheck size={20} />
            </span>
            <span className="text-[13px] font-medium" style={{ color: "var(--tk-muted)" }}>
              今日作答
            </span>
          </div>
          <div className="tk-display mt-3 text-[26px] font-bold tracking-tight">{today?.answered ?? 0} 题</div>
          <div className="mt-0.5 text-[12px]" style={{ color: "var(--tk-muted)" }}>
            {today ? `答对 ${today.correct} · ${today.date}` : "还没有作答"}
          </div>
        </div>
        <div className="tk-card p-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500 to-rose-500 text-white shadow-md">
              <Flame size={20} />
            </span>
            <span className="text-[13px] font-medium" style={{ color: "var(--tk-muted)" }}>
              最高连对
            </span>
          </div>
          <div className="tk-display mt-3 text-[26px] font-bold tracking-tight">{bestStreak} 题</div>
          <div className="mt-0.5 text-[12px]" style={{ color: "var(--tk-muted)" }}>
            单个知识点最近连续答对
          </div>
        </div>
        <div className="tk-card p-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-md">
              <TrendingUp size={20} />
            </span>
            <span className="text-[13px] font-medium" style={{ color: "var(--tk-muted)" }}>
              累计正确率
            </span>
          </div>
          <div className="tk-display mt-3 text-[26px] font-bold tracking-tight">
            {totalAnswered > 0 ? `${Math.round((totalCorrect / totalAnswered) * 100)}%` : "—"}
          </div>
          <div className="mt-0.5 text-[12px]" style={{ color: "var(--tk-muted)" }}>
            累计作答 {totalAnswered} 题
          </div>
        </div>
      </section>

      <section className="tk-card overflow-hidden">
        <div className="border-b px-5 py-3.5 text-[14px] font-bold" style={{ borderColor: "var(--tk-line)" }}>
          知识点掌握一览
        </div>
        <div className="divide-y" style={{ borderColor: "var(--tk-line)" }}>
          {allSections().map(({ chapter, section }) => {
            const stat = section.kp ? byKp.get(section.kp.id) : undefined;
            return (
              <div
                key={section.id}
                className="flex items-center gap-4 px-5 py-3.5"
                style={{ borderColor: "var(--tk-line)" }}
              >
                <span className="h-8 w-1.5 shrink-0 rounded-full" style={{ background: course.accent }} />
                <div className="min-w-0 flex-1">
                  <div className="text-[14px] font-semibold">
                    {section.title}
                    <span className="ml-2 text-[11.5px] font-normal" style={{ color: "var(--tk-muted)" }}>
                      第 {chapter.no} 章
                    </span>
                  </div>
                  <div
                    className="mt-1 flex flex-wrap items-center gap-2.5 text-[12px]"
                    style={{ color: "var(--tk-muted)" }}
                  >
                    {section.kp ? (
                      <>
                        <DifficultyDots difficulty={section.kp.difficulty} />
                        <MasteryGoalBadge goal={section.kp.mastery_goal} />
                        {stat ? (
                          <span className="font-mono">
                            {stat.correct}/{stat.total} 对 · 连对 {stat.streak}
                          </span>
                        ) : (
                          <span>还没作答过——先去随堂考核</span>
                        )}
                      </>
                    ) : (
                      <span>本章待建</span>
                    )}
                  </div>
                </div>
                <ProgressRing value={masteryOf(section.kp?.id, summary)} color={course.accent} />
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
