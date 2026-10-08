import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { ChevronRight, FileQuestion } from "lucide-react";
import { courseById } from "../content";
import { attemptsSummary, type KpSummary } from "../db";
import { GradeBadge, WeightStars, DifficultyDots, MasteryGoalBadge, KnowledgeTypeBadge, ProgressRing } from "../components/ui";
import type { View } from "../App";

export function CoursePage({ courseId, go }: { courseId: string; go: (v: View) => void }) {
  const course = courseById(courseId);
  const [summary, setSummary] = useState<KpSummary[]>([]);
  useEffect(() => {
    attemptsSummary().then(setSummary).catch(() => {});
  }, []);

  const mastery = (kpId: string) => {
    const s = summary.find((x) => x.kp_id === kpId);
    if (!s || s.total === 0) return 0;
    return Math.min(1, s.correct / s.total) * Math.min(1, s.total / 8);
  };

  return (
    <div className="space-y-6">
      <section className="hero-gradient -mx-5 px-5 pb-8 pt-10">
        <div className="flex items-center gap-2 text-[12.5px] text-ink/50">
          <GradeBadge grade={course.exam.grade} />
          <span>{course.exam.subject} · 分值 {course.exam.score_range}</span>
        </div>
        <h1 className="mt-2 text-[28px] font-bold" style={{ color: course.accent }}>
          {course.title}
        </h1>
        <p className="mt-1.5 max-w-3xl text-[14px] text-ink/60">{course.tagline}</p>
        <p className="mt-2 max-w-3xl text-[12px] text-ink/40">{course.exam.note}</p>
      </section>

      <section className="space-y-3">
        {course.chapters.map((ch, i) => {
          const m = mastery(ch.kp.id);
          return (
            <motion.div
              key={ch.id}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * i, duration: 0.4 }}
            >
              <div className="card card-hover flex items-center gap-5 p-5">
                <span
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-[17px] font-bold text-white shadow-md"
                  style={{ background: `linear-gradient(135deg, ${course.accent}, ${course.accent}cc)` }}
                >
                  {i + 1}
                </span>
                <button
                  type="button"
                  className="min-w-0 flex-1 text-left"
                  onClick={() => go({ kind: "topic", courseId, chapterId: ch.id })}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[16px] font-bold">{ch.title}</span>
                    <GradeBadge grade={ch.grade} />
                    <WeightStars weight={ch.weight} />
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2.5 text-[12.5px] text-ink/55">
                    <DifficultyDots difficulty={ch.kp.difficulty} />
                    <MasteryGoalBadge goal={ch.kp.mastery_goal} />
                    <KnowledgeTypeBadge type={ch.kp.knowledge_type} />
                    <span className="text-ink/40">{ch.kp.guide_line}</span>
                  </div>
                </button>
                <div className="flex shrink-0 items-center gap-3">
                  <button
                    type="button"
                    title="随堂考核"
                    onClick={() => go({ kind: "quiz", courseId, chapterId: ch.id })}
                    className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200 transition-colors hover:bg-emerald-100"
                  >
                    <FileQuestion size={17} />
                  </button>
                  <ProgressRing value={m} color={course.accent} />
                  <ChevronRight size={18} className="text-ink/30" />
                </div>
              </div>
            </motion.div>
          );
        })}
      </section>
    </div>
  );
}
