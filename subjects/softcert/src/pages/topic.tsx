import { useEffect } from "react";
import { ArrowLeft, ArrowRight, Link2 } from "lucide-react";
import { courseById, lessonOf } from "../content";
import { saveSetting } from "../db";
import { LessonBlocks } from "../components/blocks";
import { GradeBadge, WeightStars, DifficultyDots, MasteryGoalBadge, KnowledgeTypeBadge } from "../components/ui";
import type { View } from "../App";

export function TopicPage({
  courseId,
  chapterId,
  go,
}: {
  courseId: string;
  chapterId: string;
  go: (v: View) => void;
}) {
  const course = courseById(courseId);
  const idx = course.chapters.findIndex((c) => c.id === chapterId);
  const chapter = course.chapters[idx];
  const lesson = lessonOf(chapterId);
  const prev = idx > 0 ? course.chapters[idx - 1] : null;
  const next = idx < course.chapters.length - 1 ? course.chapters[idx + 1] : null;
  const requires = chapter.kp.requires;

  // 续读:每次进入章节就记下位置,首页据此放「接着学」入口。
  useEffect(() => {
    saveSetting(
      "last-read",
      JSON.stringify({ courseId, chapterId, courseTitle: course.title, chapterTitle: chapter.title }),
    ).catch(() => {});
  }, [courseId, chapterId, course.title, chapter.title]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 pt-4">
        <button
          type="button"
          onClick={() => go({ kind: "course", courseId })}
          className="inline-flex items-center gap-1 text-[13px] text-ink/50 hover:text-brand-600"
        >
          <ArrowLeft size={15} /> {course.title}
        </button>
      </div>

      <header className="space-y-3">
        <h1 className="text-[26px] font-bold tracking-tight">{chapter.title}</h1>
        <div className="flex flex-wrap items-center gap-2.5">
          <GradeBadge grade={chapter.grade} />
          <WeightStars weight={chapter.weight} />
          <DifficultyDots difficulty={chapter.kp.difficulty} />
          <MasteryGoalBadge goal={chapter.kp.mastery_goal} />
          <KnowledgeTypeBadge type={chapter.kp.knowledge_type} />
        </div>
        {requires.length > 0 && (
          <p className="flex items-center gap-1.5 text-[12.5px] text-ink/45">
            <Link2 size={13} /> 先修:{requires.join("、")}——没学过的先回去过一遍
          </p>
        )}
      </header>

      <article className="card px-6 py-7 md:px-9 md:py-9">
        <LessonBlocks blocks={lesson.blocks} />
      </article>

      <div className="flex items-center justify-between gap-3">
        {prev ? (
          <button
            type="button"
            onClick={() => go({ kind: "topic", courseId, chapterId: prev.id })}
            className="inline-flex items-center gap-1.5 rounded-full border border-black/10 px-4 py-2 text-[13px] text-ink/60 hover:border-brand-300 hover:text-brand-600"
          >
            <ArrowLeft size={14} /> {prev.title}
          </button>
        ) : <span />}
        {next ? (
          <button
            type="button"
            onClick={() => go({ kind: "topic", courseId, chapterId: next.id })}
            className="inline-flex items-center gap-1.5 rounded-full border border-black/10 px-4 py-2 text-[13px] text-ink/60 hover:border-brand-300 hover:text-brand-600"
          >
            {next.title} <ArrowRight size={14} />
          </button>
        ) : <span />}
      </div>

      <button
        type="button"
        onClick={() => go({ kind: "quiz", courseId, chapterId })}
        className="w-full rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 py-4 text-[16px] font-bold text-white shadow-lg shadow-emerald-500/25 transition-transform hover:scale-[1.01] active:scale-[0.99]"
      >
        开始随堂考核({chapter.title})
      </button>
    </div>
  );
}
