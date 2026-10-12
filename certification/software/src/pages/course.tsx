import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { ChevronRight, FileQuestion, BookOpen, Hammer } from "lucide-react";
import { courseById } from "../content";
import { textbookTextOfChapter } from "../textbook-text";
import { attemptsSummary, type KpSummary } from "../db";
import { GradeBadge, WeightStars, DifficultyDots, MasteryGoalBadge, KnowledgeTypeBadge, ProgressRing } from "../components/ui";
import type { View } from "../App";

export function CoursePage({ courseId, go }: { courseId: string; go: (v: View) => void }) {
  const course = courseById(courseId);
  const [summary, setSummary] = useState<KpSummary[]>([]);
  useEffect(() => {
    attemptsSummary().then(setSummary).catch(() => {});
  }, []);

  const mastery = (kpId?: string) => {
    if (!kpId) return 0;
    const s = summary.find((x) => x.kp_id === kpId);
    if (!s || s.total === 0) return 0;
    return Math.min(1, s.correct / s.total) * Math.min(1, s.total / 8);
  };

  return (
    <div className="space-y-6">
      <section className="hero-gradient -mx-5 px-5 pb-8 pt-10">
        <div className="flex items-center gap-2 text-[12.5px] text-ink/50">
          <GradeBadge grade={course.exam.grade} />
          <span>{course.exam.subject} · {course.exam.score_range}</span>
        </div>
        <h1 className="mt-2 text-[28px] font-bold" style={{ color: course.accent }}>
          {course.title}
        </h1>
        <p className="mt-1.5 max-w-3xl text-[14px] text-ink/60">{course.tagline}</p>
        <p className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-white/70 px-3 py-1 text-[12px] font-medium text-ink/60 ring-1 ring-black/5">
          <BookOpen size={13} />
          依据《{course.textbook.title}》({course.textbook.publisher} {course.textbook.year})· 全 {course.textbook.chapters_total} 章
        </p>
        <p className="mt-2 max-w-3xl text-[12px] text-ink/40">{course.exam.note}</p>
      </section>

      <section className="space-y-8">
        {course.chapters.map((ch, ci) => {
          const built = ch.sections.length > 0;
          return (
            <motion.div
              key={ch.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.04 * ci, duration: 0.35 }}
            >
              <div className="mb-3 flex flex-wrap items-baseline gap-2 px-1">
                <span
                  className="rounded-lg px-2 py-0.5 text-[13px] font-bold text-white"
                  style={{ background: course.accent }}
                >
                  第 {ch.no} 章
                </span>
                <h2 className="text-[17px] font-bold">{ch.title}</h2>
                <span className="text-[11.5px] text-ink/40">{ch.textbook_ref.locator} · {course.textbook.title}</span>
                {!built && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-[11.5px] font-medium text-amber-600 ring-1 ring-amber-200">
                    <Hammer size={11} /> 本章待建
                  </span>
                )}
              </div>
              {ch.note && <p className="mb-3 px-1 text-[12.5px] leading-relaxed text-ink/45">{ch.note}</p>}

              {built ? (
                <div className="space-y-2.5">
                  {ch.sections.map((sec) => {
                    const m = mastery(sec.kp?.id);
                    return (
                      <div key={sec.id} className="card card-hover flex items-center gap-4 p-4">
                        <button
                          type="button"
                          className="min-w-0 flex-1 text-left"
                          onClick={() => go({ kind: "topic", courseId, sectionId: sec.id })}
                        >
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-[15px] font-bold">{sec.title}</span>
                            <GradeBadge grade={sec.grade} />
                            <WeightStars weight={sec.weight} />
                          </div>
                          {sec.kp && (
                            <div className="mt-1.5 flex flex-wrap items-center gap-2.5 text-[12.5px] text-ink/55">
                              <DifficultyDots difficulty={sec.kp.difficulty} />
                              <MasteryGoalBadge goal={sec.kp.mastery_goal} />
                              <KnowledgeTypeBadge type={sec.kp.knowledge_type} />
                              <span className="text-ink/40">{sec.kp.guide_line}</span>
                            </div>
                          )}
                        </button>
                        <div className="flex shrink-0 items-center gap-3">
                          <button
                            type="button"
                            title="随堂考核"
                            onClick={() => go({ kind: "quiz", courseId, sectionId: sec.id })}
                            className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200 transition-colors hover:bg-emerald-100"
                          >
                            <FileQuestion size={17} />
                          </button>
                          <ProgressRing value={m} color={course.accent} />
                          <ChevronRight size={18} className="text-ink/30" />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="rounded-2xl border border-dashed border-black/10 px-4 py-4 text-center text-[13px] text-ink/40">
                    教学内容建设中——以下可直接阅读本章教材原文
                  </div>
                  {textbookTextOfChapter(ch.id) && (
                    <details className="card px-4 py-3">
                      <summary className="cursor-pointer select-none text-[13px] font-semibold text-ink/60">
                        教材原文({ch.textbook_ref.locator},《{course.textbook.title}》忠实转录)
                      </summary>
                      <pre className="mt-3 max-h-[480px] overflow-y-auto whitespace-pre-wrap font-sans text-[13px] leading-7 text-ink/75">{textbookTextOfChapter(ch.id)}</pre>
                    </details>
                  )}
                </div>
              )}
            </motion.div>
          );
        })}
      </section>
    </div>
  );
}
