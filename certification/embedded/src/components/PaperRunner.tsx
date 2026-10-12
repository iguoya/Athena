// 整卷作答器:一页铺开全部题目(真实试卷形态),答题卡导航,
// 每题点选即判分写库(ADR 0052),交卷出成绩。随堂考核用单题聚焦式。
import { useState } from "react";
import { CheckCircle2, XCircle, ArrowLeft, Award } from "lucide-react";
import { recordAttempt } from "../db";
import { InlineText } from "./InlineText";
import type { Question } from "../types";
import { cn } from "@/lib/utils";

const LETTERS = ["A", "B", "C", "D"];

interface Props {
  title: string;
  questions: Question[];
  mode: "chapter" | "past-exam";
  course: string;
  chapterId: string;
  kpId: string;
  onExit: () => void;
}

export default function PaperRunner({ title, questions, mode, course, chapterId, kpId, onExit }: Props) {
  const [answers, setAnswers] = useState<Record<string, { qid: string; picked: number }>>({});

  function pick(q: Question, choice: number) {
    if (answers[q.id]) return;
    setAnswers((prev) => ({ ...prev, [q.id]: { qid: q.id, picked: choice } }));
    recordAttempt({
      course,
      chapterId,
      kpId,
      questionId: q.id,
      correct: choice === q.answer,
      mode,
    }).catch(() => {});
  }

  const answeredCount = Object.keys(answers).length;
  const score = Object.values(answers).filter(
    (a) => a.picked === questions.find((q) => q.id === a.qid)?.answer,
  ).length;
  const allDone = answeredCount === questions.length;

  function jump(qid: string) {
    document.getElementById(`pq-${qid}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="pt-6">
      {/* 顶部 sticky 工具条(顶栏 h-14 之下) */}
      <div
        className="sticky top-14 z-10 -mx-6 mb-6 border-b px-6 py-3 backdrop-blur"
        style={{
          borderColor: "var(--tk-line)",
          background: "color-mix(in srgb, var(--tk-bg) 82%, transparent)",
        }}
      >
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3">
          <h1 className="tk-display text-[16px] font-bold">{title}</h1>
          <span className="text-[13px]" style={{ color: "var(--tk-muted)" }}>
            已答 {answeredCount} / {questions.length}
          </span>
          <div className="ml-auto flex items-center gap-3">
            {answeredCount > 0 && (
              <span className="text-[13px] font-semibold text-emerald-600">答对 {score}</span>
            )}
            <button
              type="button"
              className="inline-flex items-center gap-1 rounded-full border px-3.5 py-1.5 text-[13px] transition-colors"
              style={{ borderColor: "var(--tk-line)", color: "var(--tk-muted)" }}
              onClick={onExit}
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
            return (
              <div key={q.id} id={`pq-${q.id}`} className="tk-card scroll-mt-28 p-5">
                <div className="flex items-start justify-between gap-3">
                  <p className="prose-lesson text-[15px] font-medium leading-relaxed">
                    <span className="accent-fg mr-2 font-bold">{qi + 1}.</span>
                    <InlineText text={q.stem} />
                  </p>
                  {a &&
                    (a.picked === q.answer ? (
                      <CheckCircle2 size={18} className="mt-1 shrink-0 text-emerald-500" />
                    ) : (
                      <XCircle size={18} className="mt-1 shrink-0 text-rose-400" />
                    ))}
                </div>
                <div className="mt-3.5 grid gap-2 md:grid-cols-2 2xl:grid-cols-3">
                  {q.options.map((opt, i) => (
                    <button
                      key={i}
                      type="button"
                      disabled={!!a}
                      className={cn(
                        "flex items-center gap-2.5 rounded-xl border px-3.5 py-2.5 text-left text-[13.5px] transition-all",
                        !a &&
                          "border-black/10 hover:border-[var(--tk-accent)] hover:bg-[var(--tk-accent-soft)]",
                        a && i === q.answer && "border-emerald-400 bg-emerald-50",
                        a && a.picked === i && i !== q.answer && "animate-shake border-rose-300 bg-rose-50",
                        a && a.picked !== i && i !== q.answer && "border-black/5 opacity-50",
                      )}
                      onClick={() => pick(q, i)}
                    >
                      <span
                        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11.5px] font-bold"
                        style={{ background: "rgba(0,0,0,0.05)" }}
                      >
                        {LETTERS[i]}
                      </span>
                      <span className="prose-lesson">
                        <InlineText text={opt} />
                      </span>
                    </button>
                  ))}
                </div>
                {a && (
                  <div
                    className={cn(
                      "mt-3 rounded-xl px-4 py-3 text-[13px] leading-relaxed",
                      a.picked === q.answer
                        ? "bg-emerald-50 text-emerald-800"
                        : "bg-rose-50 text-rose-800",
                    )}
                  >
                    <b>正确答案:{LETTERS[q.answer]}。</b>
                    {q.explanation}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* 答题卡 */}
        <aside className="hidden w-44 shrink-0 lg:block 2xl:w-60">
          <div className="tk-card sticky top-32 p-4">
            <div className="mb-3 text-[13px] font-bold">答题卡</div>
            <div className="grid grid-cols-6 gap-1.5">
              {questions.map((q, i) => {
                const a = answers[q.id];
                return (
                  <button
                    key={q.id}
                    type="button"
                    className={cn(
                      "h-7 rounded-md text-[11px] font-bold transition-colors",
                      !a
                        ? "bg-black/5"
                        : a.picked === q.answer
                          ? "bg-emerald-500 text-white"
                          : "bg-rose-400 text-white",
                    )}
                    style={!a ? { color: "var(--tk-muted)" } : undefined}
                    onClick={() => jump(q.id)}
                  >
                    {i + 1}
                  </button>
                );
              })}
            </div>
            {allDone ? (
              <div className="mt-4 rounded-xl bg-emerald-50 p-3 text-center">
                <Award size={20} className="mx-auto text-emerald-500" />
                <div className="mt-1 text-[13px] font-bold text-emerald-700">整卷完成</div>
                <div className="text-[12px] text-emerald-600/80">
                  {score} / {questions.length} · {Math.round((score / questions.length) * 100)} 分
                </div>
              </div>
            ) : (
              <p
                className="mt-3 text-[11.5px] leading-relaxed"
                style={{ color: "color-mix(in srgb, var(--tk-muted) 75%, transparent)" }}
              >
                白 = 未答,绿 = 答对,红 = 答错;点题号跳转。
              </p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
