// 节学习页 = 阅读器:与 softcert 的「大卡片包内容」刻意区分——内容块直接
// 铺在学习流上,列宽收窄,标题区紧凑,节末内联考核入口。块自身的视觉
// (表格卡/公式卡/callout)是内容元素,不是容器。
import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, Link2, BookOpen, PenLine } from "lucide-react";
import { course, findSection, lessonOf, pastExamQuestions, quizOf } from "../content";
import { textbookTextOf } from "../textbook-text";
import { saveSetting } from "../db";
import Blocks from "../components/Blocks";
import QuizRunner from "../components/QuizRunner";
import PaperRunner from "../components/PaperRunner";
import {
  GradeBadge,
  WeightStars,
  DifficultyDots,
  MasteryGoalBadge,
  KnowledgeTypeBadge,
} from "../components/ui";
import type { View } from "./types";

/** 全部节,按课程顺序平铺:上一节/下一节导航用。 */
const flat = course.chapters.flatMap((ch) =>
  ch.sections.map((s) => ({ sectionId: s.id, title: s.title })),
);

export default function TopicView({ sectionId, go }: { sectionId: string; go: (v: View) => void }) {
  const current = findSection(sectionId);
  const lesson = lessonOf(sectionId);

  const idx = flat.findIndex((s) => s.sectionId === sectionId);
  const prev = idx > 0 ? flat[idx - 1] : null;
  const next = idx < flat.length - 1 ? flat[idx + 1] : null;
  const requires = current.section.kp?.requires ?? [];
  const textbookText = textbookTextOf(sectionId);

  // 立即检索（P2）：讲解读完立刻作答，讲解与检索 1:1 绑定在同一页里。
  // 配置了 past_exam_knowledge 的节走真题精选整卷（延迟反馈），其余单题聚焦（即时反馈）。
  const [retrieval, setRetrieval] = useState(false);
  const pattern = current.section.past_exam_knowledge;
  const pastQuestions = useMemo(() => (pattern ? pastExamQuestions(pattern) : []), [pattern]);
  const localQuiz = pastQuestions.length === 0 ? quizOf(sectionId) : null;
  const questionCount = pastQuestions.length || localQuiz?.questions.length || 0;

  // 续读:每次进入章节就记下位置,首页行动卡据此放「接着学」。
  useEffect(() => {
    saveSetting(
      "last-read",
      JSON.stringify({
        sectionId,
        chapterTitle: current.chapter.title,
        sectionTitle: current.section.title,
      }),
    ).catch(() => {});
  }, [sectionId, current.chapter.title, current.section.title]);

  const kpId = current.section.kp?.id ?? current.section.id;

  return (
    <div className="mx-auto max-w-[820px]">
      {/* 面包屑行 */}
      <div className="flex items-center justify-between gap-3 pt-2">
        <button
          type="button"
          className="inline-flex items-center gap-1 text-[13px] transition-colors"
          style={{ color: "var(--tk-muted)" }}
          onClick={() => go({ kind: "course" })}
        >
          <ArrowLeft size={14} /> 学习路径
        </button>
        <span
          className="text-[12px]"
          style={{ color: "color-mix(in srgb, var(--tk-muted) 75%, transparent)" }}
        >
          第 {current.chapter.no} 章 · {current.chapter.title}
        </span>
      </div>

      {/* 标题区:紧凑 */}
      <header className="mt-6 space-y-3">
        <h1 className="tk-display text-[30px] font-bold leading-tight tracking-tight">
          {current.section.title}
        </h1>
        <div className="flex flex-wrap items-center gap-2.5">
          <GradeBadge value={current.section.grade} />
          <WeightStars weight={current.section.weight} />
          {current.section.kp && (
            <>
              <DifficultyDots difficulty={current.section.kp.difficulty} />
              <MasteryGoalBadge goal={current.section.kp.mastery_goal} />
              <KnowledgeTypeBadge type={current.section.kp.knowledge_type} />
            </>
          )}
        </div>
        {requires.length > 0 && (
          <p className="flex items-center gap-1.5 text-[12.5px]" style={{ color: "var(--tk-muted)" }}>
            <Link2 size={13} /> 先修:{requires.join("、")}——没学过的先回去过一遍
          </p>
        )}
        <p
          className="flex items-center gap-1.5 text-[12px]"
          style={{ color: "color-mix(in srgb, var(--tk-muted) 80%, transparent)" }}
        >
          <BookOpen size={13} />
          出处:{current.chapter.textbook_ref.locator},《{course.textbook.title}》
        </p>
      </header>

      {/* 内容块直接铺在学习流上(无容器卡) */}
      <article className="space-y-7 border-t py-8" style={{ borderColor: "var(--tk-line)" }}>
        {lesson.blocks.map((b, i) => (
          <Blocks key={i} block={b} />
        ))}
      </article>

      {textbookText && (
        <details className="tk-card px-6 py-4">
          <summary
            className="cursor-pointer select-none text-[13.5px] font-semibold"
            style={{ color: "var(--tk-muted)" }}
          >
            教材原文({current.chapter.textbook_ref.locator},《{course.textbook.title}》忠实转录,OCR
            可能有个别识别误差)
          </summary>
          <pre
            className="mt-4 max-h-[500px] overflow-y-auto whitespace-pre-wrap font-sans text-[13.5px] leading-7"
            style={{ color: "color-mix(in srgb, var(--tk-fg) 75%, transparent)" }}
          >
            {textbookText}
          </pre>
        </details>
      )}

      {/* 节末:内联考核入口 + 上下节导航 */}
      <div className="mt-8 space-y-4">
        {/* 立即检索（P2）：讲解读完立刻作答；展开后可收起回讲义 */}
        {retrieval && pastQuestions.length > 0 ? (
          <PaperRunner
            title={`${current.section.title} · 历年真题精选(${pastQuestions.length} 题)`}
            questions={pastQuestions}
            mode="chapter"
            course={course.id}
            chapterId={current.section.id}
            kpId={kpId}
            onExit={() => setRetrieval(false)}
          />
        ) : retrieval && localQuiz ? (
          <QuizRunner
            title={`${current.section.title} · 立即检索`}
            questions={localQuiz.questions}
            mode="chapter"
            course={course.id}
            chapterId={current.section.id}
            kpId={kpId}
            onExit={() => setRetrieval(false)}
          />
        ) : questionCount > 0 ? (
          <button
            type="button"
            className="accent-gradient flex w-full items-center justify-center gap-2 rounded-full py-3 text-[14.5px] font-semibold text-white shadow-md transition-transform hover:scale-[1.01] active:scale-[0.99]"
            onClick={() => setRetrieval(true)}
          >
            <PenLine size={16} /> 读完立即检索 · {current.section.title}（{questionCount} 题）
          </button>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2">
          {prev ? (
            <button
              type="button"
              className="tk-card tk-card-hover flex items-center gap-2.5 p-3.5 text-left"
              onClick={() => go({ kind: "topic", sectionId: prev.sectionId })}
            >
              <ArrowLeft size={15} className="shrink-0" style={{ color: "var(--tk-muted)" }} />
              <span className="min-w-0">
                <span className="block text-[11px]" style={{ color: "var(--tk-muted)" }}>
                  上一节
                </span>
                <span className="block truncate text-[13.5px] font-semibold">{prev.title}</span>
              </span>
            </button>
          ) : (
            <span />
          )}
          {next ? (
            <button
              type="button"
              className="tk-card tk-card-hover flex items-center justify-end gap-2.5 p-3.5 text-right"
              onClick={() => go({ kind: "topic", sectionId: next.sectionId })}
            >
              <span className="min-w-0">
                <span className="block text-[11px]" style={{ color: "var(--tk-muted)" }}>
                  下一节
                </span>
                <span className="block truncate text-[13.5px] font-semibold">{next.title}</span>
              </span>
              <ArrowRight size={15} className="accent-fg shrink-0" />
            </button>
          ) : (
            <span />
          )}
        </div>
      </div>
    </div>
  );
}
