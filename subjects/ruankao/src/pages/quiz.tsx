// 章节随堂考核:每答一题即写进度库(ADR 0052:作答先入库)。
import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { CheckCircle2, XCircle, ArrowRight, RotateCcw, Award } from "lucide-react";
import { courseById, quizOf } from "../content";
import { recordAttempt } from "../db";
import { inline } from "../components/blocks";
import type { Question } from "../types";
import type { View } from "../App";

const LETTERS = ["A", "B", "C", "D"];

interface Answered {
  question: Question;
  picked: number;
}

export function QuizRunner({
  title,
  questions,
  mode,
  course,
  chapterId,
  kpId,
  onExit,
}: {
  title: string;
  questions: Question[];
  mode: "chapter" | "past-exam";
  course: string;
  chapterId: string;
  kpId: string;
  onExit: () => void;
}) {
  const [idx, setIdx] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [answers, setAnswers] = useState<Answered[]>([]);
  const question = questions[idx];
  const judged = picked !== null;
  const correct = judged && picked === question.answer;
  const finished = answers.length === questions.length;

  const submit = (choice: number) => {
    if (judged) return;
    setPicked(choice);
    setAnswers((a) => [...a, { question, picked: choice }]);
    recordAttempt({
      course,
      chapterId,
      kpId,
      questionId: question.id,
      correct: choice === question.answer,
      mode,
    }).catch(() => {});
  };

  const score = useMemo(() => answers.filter((a) => a.picked === a.question.answer).length, [answers]);

  if (finished) {
    const ratio = score / questions.length;
    return (
      <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} className="mx-auto max-w-2xl space-y-5 pt-8">
        <div className="card p-8 text-center">
          <Award size={44} className={ratio >= 0.6 ? "mx-auto text-emerald-500" : "mx-auto text-amber-500"} />
          <h2 className="mt-3 text-[22px] font-bold">
            {ratio >= 0.8 ? "稳了" : ratio >= 0.6 ? "过线水平" : "回炉再战"}
          </h2>
          <p className="mt-1 text-[14px] text-ink/60">
            {score} / {questions.length} 正确(及格线 60%:{ratio >= 0.6 ? "已过" : "未过"})
          </p>
          <div className="mx-auto mt-4 h-2.5 w-64 overflow-hidden rounded-full bg-black/5">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${ratio * 100}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className={`h-full rounded-full ${ratio >= 0.6 ? "bg-gradient-to-r from-emerald-400 to-teal-500" : "bg-gradient-to-r from-amber-400 to-orange-500"}`}
            />
          </div>
          <p className="mt-4 text-[12.5px] text-ink/40">作答已写入进度库,战况页可见派生的掌握度。</p>
          <button
            type="button"
            onClick={onExit}
            className="mt-5 inline-flex items-center gap-1.5 rounded-full bg-brand-500 px-5 py-2.5 text-[14px] font-semibold text-white shadow-md hover:bg-brand-600"
          >
            <ArrowRight size={15} /> 返回
          </button>
        </div>
        <div className="space-y-3">
          {answers.map((a, i) => (
            <AnswerReview key={i} answered={a} index={i} />
          ))}
        </div>
      </motion.div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-5 pt-6">
      <div className="flex items-center justify-between">
        <h1 className="text-[18px] font-bold">{title}</h1>
        <span className="text-[13px] text-ink/50">
          第 {idx + 1} / {questions.length} 题
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-black/5">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-brand-400 to-fuchsia-500"
          animate={{ width: `${((idx + (judged ? 1 : 0)) / questions.length) * 100}%` }}
        />
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={question.id}
          initial={{ opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -24 }}
          transition={{ duration: 0.25 }}
          className="card p-6"
        >
          <p className="prose-lesson text-[15.5px] font-medium leading-relaxed">{inline(question.stem)}</p>
          <div className="mt-5 space-y-2.5">
            {question.options.map((opt, i) => {
              const isAnswer = i === question.answer;
              const isPicked = picked === i;
              let cls = "border-black/10 hover:border-brand-400 hover:bg-brand-50/60";
              if (judged) {
                if (isAnswer) cls = "border-emerald-400 bg-emerald-50 animate-pop";
                else if (isPicked) cls = "border-rose-300 bg-rose-50 animate-shake";
                else cls = "border-black/8 opacity-55";
              }
              return (
                <button
                  key={i}
                  type="button"
                  disabled={judged}
                  onClick={() => submit(i)}
                  className={`flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-[14px] transition-all ${cls}`}
                >
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-black/5 text-[12.5px] font-bold">
                    {LETTERS[i]}
                  </span>
                  <span className="prose-lesson">{inline(opt)}</span>
                  {judged && isAnswer && <CheckCircle2 size={18} className="ml-auto shrink-0 text-emerald-500" />}
                  {judged && isPicked && !isAnswer && <XCircle size={18} className="ml-auto shrink-0 text-rose-400" />}
                </button>
              );
            })}
          </div>

          {judged && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-5">
              <div className={`rounded-xl px-4 py-3.5 text-[13.5px] leading-relaxed ${correct ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-800"}`}>
                <b>{correct ? "答对了。" : "答错了。"}</b> {question.explanation}
              </div>
              <div className="mt-2.5 flex items-center justify-between">
                <span className="text-[11.5px] text-ink/40">
                  出处:{question.source.relation === "authored" ? "自造考点题" : "真题"}
                  {question.source.locator ? ` · ${question.source.locator}` : ""}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    if (idx + 1 < questions.length) {
                      setIdx(idx + 1);
                      setPicked(null);
                    } else {
                      setIdx(questions.length); // 触发 finished
                    }
                  }}
                  className="inline-flex items-center gap-1 rounded-full bg-brand-500 px-4 py-2 text-[13px] font-semibold text-white shadow hover:bg-brand-600"
                >
                  {idx + 1 < questions.length ? "下一题" : "看结果"} <ArrowRight size={14} />
                </button>
              </div>
            </motion.div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

function AnswerReview({ answered, index }: { answered: Answered; index: number }) {
  const ok = answered.picked === answered.question.answer;
  return (
    <div className="card p-4">
      <div className="flex items-start gap-2.5">
        {ok ? <CheckCircle2 size={17} className="mt-0.5 shrink-0 text-emerald-500" /> : <XCircle size={17} className="mt-0.5 shrink-0 text-rose-400" />}
        <div className="min-w-0">
          <p className="prose-lesson text-[13.5px] font-medium">
            {index + 1}. {inline(answered.question.stem)}
          </p>
          <p className="mt-1 text-[12.5px] text-ink/55">
            你的答案:{LETTERS[answered.picked]}
            {!ok && <> · 正确:{LETTERS[answered.question.answer]}</>}
          </p>
          {!ok && <p className="prose-lesson mt-1 text-[12.5px] text-ink/60">{inline(answered.question.explanation)}</p>}
        </div>
      </div>
    </div>
  );
}

export function QuizPage({ courseId, chapterId, go }: { courseId: string; chapterId: string; go: (v: View) => void }) {
  const course = courseById(courseId);
  const chapter = course.chapters.find((c) => c.id === chapterId)!;
  const quiz = quizOf(chapterId);
  return (
    <QuizRunner
      title={`${chapter.title} · 随堂考核`}
      questions={quiz.questions}
      mode="chapter"
      course={course.id}
      chapterId={chapter.id}
      kpId={chapter.kp.id}
      onExit={() => go({ kind: "topic", courseId, chapterId })}
    />
  );
}

export function RestartIcon() {
  return <RotateCcw size={14} />;
}
