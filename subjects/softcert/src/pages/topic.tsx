import { useEffect } from "react";
import { ArrowLeft, ArrowRight, Link2, BookOpen } from "lucide-react";
import { findSection, lessonOf, courses } from "../content";
import { saveSetting } from "../db";
import { LessonBlocks } from "../components/blocks";
import { GradeBadge, WeightStars, DifficultyDots, MasteryGoalBadge, KnowledgeTypeBadge } from "../components/ui";
import type { View } from "../App";

/** 全部有内容的节,按课程顺序平铺:上一节/下一节导航用。 */
function flatSections() {
  return courses.flatMap((c) =>
    c.chapters.flatMap((ch) => ch.sections.map((s) => ({ courseId: c.id, sectionId: s.id, title: s.title }))),
  );
}

export function TopicPage({
  courseId,
  sectionId,
  go,
}: {
  courseId: string;
  sectionId: string;
  go: (v: View) => void;
}) {
  const { course, chapter, section } = findSection(courseId, sectionId);
  const lesson = lessonOf(sectionId);
  const flat = flatSections();
  const idx = flat.findIndex((s) => s.courseId === courseId && s.sectionId === sectionId);
  const prev = idx > 0 ? flat[idx - 1] : null;
  const next = idx < flat.length - 1 ? flat[idx + 1] : null;
  const requires = section.kp?.requires ?? [];

  // 续读:每次进入章节就记下位置,首页据此放「接着学」入口。
  useEffect(() => {
    saveSetting(
      "last-read",
      JSON.stringify({ courseId, sectionId, courseTitle: course.title, chapterTitle: section.title }),
    ).catch(() => {});
  }, [courseId, sectionId, course.title, section.title]);

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
        <p className="text-[13px] font-medium text-ink/45">
          第 {chapter.no} 章 · {chapter.title}
        </p>
        <h1 className="text-[26px] font-bold tracking-tight">{section.title}</h1>
        <div className="flex flex-wrap items-center gap-2.5">
          <GradeBadge grade={section.grade} />
          <WeightStars weight={section.weight} />
          {section.kp && (
            <>
              <DifficultyDots difficulty={section.kp.difficulty} />
              <MasteryGoalBadge goal={section.kp.mastery_goal} />
              <KnowledgeTypeBadge type={section.kp.knowledge_type} />
            </>
          )}
        </div>
        {requires.length > 0 && (
          <p className="flex items-center gap-1.5 text-[12.5px] text-ink/45">
            <Link2 size={13} /> 先修:{requires.join("、")}——没学过的先回去过一遍
          </p>
        )}
        <p className="flex items-center gap-1.5 text-[12px] text-ink/40">
          <BookOpen size={13} /> 出处:{chapter.textbook_ref.locator},《{course.textbook.title}》
        </p>
      </header>

      <article className="card mx-auto max-w-[980px] px-6 py-7 md:px-9 md:py-9">
        <LessonBlocks blocks={lesson.blocks} />
      </article>

      <div className="mx-auto flex max-w-[980px] items-center justify-between gap-3">
        {prev ? (
          <button
            type="button"
            onClick={() => go({ kind: "topic", courseId: prev.courseId, sectionId: prev.sectionId })}
            className="inline-flex items-center gap-1.5 rounded-full border border-black/10 px-4 py-2 text-[13px] text-ink/60 hover:border-brand-300 hover:text-brand-600"
          >
            <ArrowLeft size={14} /> {prev.title}
          </button>
        ) : <span />}
        {next ? (
          <button
            type="button"
            onClick={() => go({ kind: "topic", courseId: next.courseId, sectionId: next.sectionId })}
            className="inline-flex items-center gap-1.5 rounded-full border border-black/10 px-4 py-2 text-[13px] text-ink/60 hover:border-brand-300 hover:text-brand-600"
          >
            {next.title} <ArrowRight size={14} />
          </button>
        ) : <span />}
      </div>

      <button
        type="button"
        onClick={() => go({ kind: "quiz", courseId, sectionId })}
        className="mx-auto max-w-[980px] w-full rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 py-4 text-[16px] font-bold text-white shadow-lg shadow-emerald-500/25 transition-transform hover:scale-[1.01] active:scale-[0.99]"
      >
        开始随堂考核({section.title})
      </button>
    </div>
  );
}
