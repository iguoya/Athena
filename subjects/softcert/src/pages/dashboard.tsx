import { useEffect, useState } from "react";
import { Flame, CalendarCheck } from "lucide-react";
import { allKps } from "../content";
import { attemptsSummary, todayStats, type KpSummary, type TodayStats } from "../db";
import { ProgressRing, DifficultyDots, MasteryGoalBadge } from "../components/ui";

/** 战况页:一切数字由作答记录派生(ADR 0052)——没有记录就没有徽章。 */
export function DashboardPage() {
  const [summary, setSummary] = useState<KpSummary[]>([]);
  const [today, setToday] = useState<TodayStats | null>(null);
  useEffect(() => {
    attemptsSummary().then(setSummary).catch(() => {});
    todayStats().then(setToday).catch(() => {});
  }, []);

  const byKp = new Map(summary.map((s) => [s.kp_id, s]));
  const totalAnswered = summary.reduce((s, x) => s + x.total, 0);
  const totalCorrect = summary.reduce((s, x) => s + x.correct, 0);
  const bestStreak = Math.max(0, ...summary.map((s) => s.streak));
  const mastery = (kpId: string) => {
    const s = byKp.get(kpId);
    if (!s || s.total === 0) return 0;
    return Math.min(1, s.correct / s.total) * Math.min(1, s.total / 8);
  };

  return (
    <div className="space-y-7 pt-8">
      <header>
        <h1 className="text-[26px] font-bold tracking-tight">掌握度战况</h1>
        <p className="mt-1.5 text-[14px] text-ink/60">
          掌握度只由作答写入:下面每个数字都来自 progress/learning.db 的作答记录。
        </p>
      </header>

      <section className="grid gap-4 sm:grid-cols-3">
        <StatCard
          icon={<CalendarCheck size={20} />}
          label="今日作答"
          value={`${today?.answered ?? 0} 题`}
          sub={today ? `答对 ${today.correct} · ${today.date}` : "还没有作答"}
          from="from-brand-500"
          to="to-violet-600"
        />
        <StatCard
          icon={<Flame size={20} />}
          label="最高连对"
          value={`${bestStreak} 题`}
          sub="单个知识点最近连续答对"
          from="from-orange-500"
          to="to-rose-500"
        />
        <StatCard
          icon={<ProgressStat />}
          label="累计正确率"
          value={totalAnswered > 0 ? `${Math.round((totalCorrect / totalAnswered) * 100)}%` : "—"}
          sub={`累计作答 ${totalAnswered} 题`}
          from="from-emerald-500"
          to="to-teal-600"
        />
      </section>

      <section className="card overflow-hidden">
        <div className="border-b border-black/5 px-5 py-3.5 text-[14px] font-bold">知识点掌握一览</div>
        <div className="divide-y divide-black/5">
          {allKps().map(({ course, chapter, kp }) => {
            const s = byKp.get(kp.id);
            const m = mastery(kp.id);
            return (
              <div key={kp.id} className="flex items-center gap-4 px-5 py-3.5">
                <span className="h-8 w-1.5 shrink-0 rounded-full" style={{ background: course.accent }} />
                <div className="min-w-0 flex-1">
                  <div className="text-[14px] font-semibold">
                    {chapter.title}
                    <span className="ml-2 text-[11.5px] font-normal text-ink/40">{course.title}</span>
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-2.5 text-[12px] text-ink/50">
                    <DifficultyDots difficulty={kp.difficulty} />
                    <MasteryGoalBadge goal={kp.mastery_goal} />
                    {s ? (
                      <span className="font-mono">
                        {s.correct}/{s.total} 对 · 连对 {s.streak}
                      </span>
                    ) : (
                      <span>还没作答过——先去随堂考核</span>
                    )}
                  </div>
                </div>
                <ProgressRing value={m} color={course.accent} />
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  sub,
  from,
  to,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
  from: string;
  to: string;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-center gap-3">
        <span className={`flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br ${from} ${to} text-white shadow-md`}>
          {icon}
        </span>
        <span className="text-[13px] font-medium text-ink/55">{label}</span>
      </div>
      <div className="mt-3 text-[26px] font-bold tracking-tight">{value}</div>
      <div className="mt-0.5 text-[12px] text-ink/45">{sub}</div>
    </div>
  );
}

function ProgressStat() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
      <path d="M4 17 L10 11 L14 15 L20 7" />
      <path d="M15 7 L20 7 L20 12" />
    </svg>
  );
}
