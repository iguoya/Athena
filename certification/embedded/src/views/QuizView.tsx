// 随堂考核入口:配置了 past_exam_knowledge 的节直接用该知识点历年真题精选
// (verbatim 整卷形态),否则用本节考核题(单题聚焦式)。
import { useMemo } from "react";
import { course, findSection, pastExamQuestions, quizOf } from "../content";
import QuizRunner from "../components/QuizRunner";
import PaperRunner from "../components/PaperRunner";
import type { View } from "./types";

export default function QuizView({ sectionId, go }: { sectionId: string; go: (v: View) => void }) {
  const section = findSection(sectionId).section;
  const pattern = section.past_exam_knowledge;
  const pastQuestions = useMemo(() => (pattern ? pastExamQuestions(pattern) : []), [pattern]);
  const localQuiz = pastQuestions.length === 0 ? quizOf(sectionId) : null;
  const common = {
    mode: "chapter" as const,
    course: course.id,
    chapterId: section.id,
    kpId: section.kp?.id ?? section.id,
    onExit: () => go({ kind: "topic", sectionId: section.id }),
  };

  if (pastQuestions.length > 0) {
    return (
      <PaperRunner
        title={`${section.title} · 历年真题精选(${pastQuestions.length} 题)`}
        questions={pastQuestions}
        {...common}
      />
    );
  }
  if (localQuiz) {
    return <QuizRunner title={`${section.title} · 随堂考核`} questions={localQuiz.questions} {...common} />;
  }
  return null;
}
