// 真题卷整卷作答器:一页铺开全部题目(真实试卷形态),答题卡导航,
// 每题点选即判分写库(ADR 0052),交卷出成绩。随堂考核仍用单题聚焦式。
import { useMemo, useState } from "react";
import { motion } from "motion/react";
import { CheckCircle2, XCircle, ArrowLeft, Award } from "lucide-react";
import { recordAttempt } from "../db";
import { inline } from "../components/blocks";
import type { Question } from "../types";

const LETTERS = ["A", "B", "C", "D"];

interface Answered {
  qid: string;
  picked: number;
}

export function PaperRunner({
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
  const [answers, setAnswers] = useState<Record<string, Answered>>({});

  const pick = (q: Question, choice: number) => {
    if (answers[q.id]) return;
    setAnswers((m) => ({ ...m, [q.id]: { qid: q.id, picked: choice } }));
    recordAttempt({
      course,
      chapterId,
      kpId,
      questionId: q.id,
      correct: choice === q.answer,
      mode,
    }).catch(() => {});
  };

  const answeredCount = Object.keys(answers).length;
  const score = useMemo(
    () => Object.values(answers).filter((a) => a.picked === questions.find((q) => q.id === a.qid)!.answer).length,
    [answers, questions],
  );
  const allDone = answeredCount === questions.length;

  const jump = (qid: string) => {
    document.getElementById(`pq-${qid}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="pt-6">
      {/* 顶部 sticky 工具条 */}
      <div className="glass-nav sticky top-14 z-10 -mx-5 mb-6 border-b border-black/5 px-5 py-3">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3">
          <h1 className="text-[16px] font-bold">{title}</h1>
          <span className="text-[13px] text-ink/50">
            已答 {answeredCount} / {questions.length}
          </span>
          <div className="ml-auto flex items-center gap-3">
            {answeredCount > 0 && (
              <span className="text-[13px] font-semibold text-emerald-600">
                答对 {score}
              </span>
            )}
            <button
              type="button"
              onClick={onExit}
              className="inline-flex items-center gap-1 rounded-full border border-black/10 px-3.5 py-1.5 text-[13px] text-ink/60 hover:border-brand-300 hover:text-brand-600"
            >
              <ArrowLeft size={13} /> 退出
            </button>
          </div>
        </div>
      </div>

      <div className="flex gap-6">
        {/* 题目区:整卷铺开 */}
        <div className="min-w-0 flex-1 space-y-5">
          {questions.map((q, qi) => {
            const a = answers[q.id];
            const judged = !!a;
            const correct = judged && a.picked === q.answer;
            return (
              <div key={q.id} id={`pq-${q.id}`} className="card scroll-mt-28 p-5">
                <div className="flex items-start justify-between gap-3">
                  <p className="prose-lesson text-[15px] font-medium leading-relaxed">
                    <span className="mr-2 font-bold text-brand-700">{qi + 1}.</span>
                    {inline(q.stem)}
                  </p>
                  {judged &&
                    (correct ? (
                      <CheckCircle2 size={18} className="mt-1 shrink-0 text-emerald-500" />
                    ) : (
                      <XCircle size={18} className="mt-1 shrink-0 text-rose-400" />
                    ))}
                </div>
                <div className="mt-3.5 grid gap-2 md:grid-cols-2">
                  {q.options.map((opt, i) => {
                    const isAnswer = i === q.answer;
                    const isPicked = judged && a.picked === i;
                    let cls = "border-black/10 hover:border-brand-400 hover:bg-brand-50/60";
                    if (judged) {
                      if (isAnswer) cls = "border-emerald-400 bg-emerald-50";
                      else if (isPicked) cls = "border-rose-300 bg-rose-50 animate-shake";
                      else cls = "border-black/5 opacity-50";
                    }
                    return (
                      <button
                        key={i}
                        type="button"
                        disabled={judged}
                        onClick={() => pick(q, i)}
                        className={`flex items-center gap-2.5 rounded-xl border px-3.5 py-2.5 text-left text-[13.5px] transition-all ${cls}`}
                      >
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-black/5 text-[11.5px] font-bold">
                          {LETTERS[i]}
                        </span>
                        <span className="prose-lesson">{inline(opt)}</span>
                      </button>
                    );
                  })}
                </div>
                {judged && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className={`mt-3 overflow-hidden rounded-xl px-4 py-3 text-[13px] leading-relaxed ${
                      correct ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-800"
                    }`}
                  >
                    <b>正确答案:{LETTERS[q.answer]}。</b> {q.explanation}
                  </motion.div>
                )}
              </div>
            );
          })}
        </div>

        {/* 答题卡 */}
        <aside className="hidden w-44 shrink-0 lg:block">
          <div className="card sticky top-32 p-4">
            <div className="mb-3 text-[13px] font-bold">答题卡</div>
            <div className="grid grid-cols-6 gap-1.5">
              {questions.map((q, i) => {
                const a = answers[q.id];
                const cls = !a
                  ? "bg-black/5 text-ink/45"
                  : a.picked === q.answer
                    ? "bg-emerald-500 text-white"
                    : "bg-rose-400 text-white";
                return (
                  <button
                    key={q.id}
                    type="button"
                    onClick={() => jump(q.id)}
                    className={`h-7 rounded-md text-[11px] font-bold transition-colors ${cls}`}
                  >
                    {i + 1}
                  </button>
                );
              })}
            </div>
            {allDone ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="mt-4 rounded-xl bg-emerald-50 p-3 text-center"
              >
                <Award size={20} className="mx-auto text-emerald-500" />
                <div className="mt-1 text-[13px] font-bold text-emerald-700">整卷完成</div>
                <div className="text-[12px] text-emerald-600/80">
                  {score} / {questions.length} · {Math.round((score / questions.length) * 100)} 分
                </div>
              </motion.div>
            ) : (
              <p className="mt-3 text-[11.5px] leading-relaxed text-ink/40">
                白 = 未答,绿 = 答对,红 = 答错;点题号跳转。
              </p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
