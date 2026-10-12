import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Link2, BookOpen } from "lucide-react";
import { findSection, lessonOf, courses, quizOf, pastExamQuestions } from "../content";
import { textbookTextOf } from "../textbook-text";
import { saveSetting } from "../db";
import { LessonBlocks } from "../components/blocks";
import { QuizRunner } from "./quiz";
import { PaperRunner } from "./paper-quiz";
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
  const textbookText = textbookTextOf(sectionId);

  // 立即检索（P2）：讲解读完立刻作答，讲解与检索 1:1 绑定在同一个页面里。
  // 真题精选配置的节走整卷模式（延迟反馈），其余走单题聚焦式（即时反馈）。
  const pattern = section.past_exam_knowledge;
  const examQuestions = pattern ? pastExamQuestions(pattern) : [];
  const sectionQuestions = examQuestions.length > 0 ? examQuestions : quizOf(sectionId).questions;
  const [retrieval, setRetrieval] = useState(false);

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

      {textbookText && (
        <details className="card px-6 py-4">
          <summary className="cursor-pointer select-none text-[13.5px] font-semibold text-ink/60">
            教材原文({chapter.textbook_ref.locator},《{course.textbook.title}》忠实转录,OCR 可能有个别识别误差)
          </summary>
          <pre className="mt-4 max-h-[500px] overflow-y-auto whitespace-pre-wrap font-sans text-[13.5px] leading-7 text-ink/75">{textbookText}</pre>
        </details>
      )}

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

      {sectionQuestions.length > 0 && !retrieval && (
        <button
          type="button"
          onClick={() => setRetrieval(true)}
          className="mx-auto max-w-[980px] w-full rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 py-4 text-[16px] font-bold text-white shadow-lg shadow-emerald-500/25 transition-transform hover:scale-[1.01] active:scale-[0.99]"
        >
          读完立即检索 · {section.title}({sectionQuestions.length} 题)
        </button>
      )}
      {retrieval && sectionQuestions.length > 0 && (
        examQuestions.length > 0 ? (
          <PaperRunner
            title={`${section.title} · 历年真题精选(${examQuestions.length} 题)`}
            questions={examQuestions}
            mode="chapter"
            course={course.id}
            chapterId={section.id}
            kpId={section.kp?.id ?? section.id}
            onExit={() => setRetrieval(false)}
          />
        ) : (
          <QuizRunner
            title={`${section.title} · 立即检索`}
            questions={sectionQuestions}
            mode="chapter"
            course={course.id}
            chapterId={section.id}
            kpId={section.kp?.id ?? section.id}
            onExit={() => setRetrieval(false)}
          />
        )
      )}
    </div>
  );
}
