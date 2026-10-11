// 单题聚焦式作答器:每答一题即写进度库(ADR 0052:作答先入库)。
// 章节随堂考核用;整卷形态见 PaperRunner。
import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, ArrowRight, Award } from "lucide-react";
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

export default function QuizRunner({ title, questions, mode, course, chapterId, kpId, onExit }: Props) {
  const [idx, setIdx] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [answers, setAnswers] = useState<{ question: Question; picked: number }[]>([]);

  const question = questions[idx];
  const judged = picked !== null;
  const correct = judged && picked === question?.answer;
  // 最后一题作答后先停在解析页,点「看结果」(advance 把 idx 推到末尾)才进结果页。
  const finished = idx >= questions.length;
  const score = answers.filter((a) => a.picked === a.question.answer).length;
  const ratio = score / questions.length;

  function submit(choice: number) {
    if (judged) return;
    setPicked(choice);
    setAnswers((prev) => [...prev, { question, picked: choice }]);
    recordAttempt({
      course,
      chapterId,
      kpId,
      questionId: question.id,
      correct: choice === question.answer,
      mode,
    }).catch(() => {});
  }

  function advance() {
    if (idx + 1 < questions.length) {
      setIdx(idx + 1);
      setPicked(null);
    } else {
      setIdx(questions.length); // 触发 finished
    }
  }

  // 键盘流:A–D / 1–4 作答,Enter 下一题——刷题不用碰鼠标,与 softcert 的
  // 纯点击作答形成体验差异。
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (finished) return;
      const k = e.key.toLowerCase();
      if (!judged) {
        const map: Record<string, number> = { a: 0, b: 1, c: 2, d: 3, "1": 0, "2": 1, "3": 2, "4": 3 };
        if (k in map) submit(map[k]);
      } else if (k === "enter") {
        advance();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  // 结果页
  if (finished) {
    return (
      <div className="mx-auto max-w-2xl space-y-5 pt-8">
        <div className="tk-card p-8 text-center">
          <Award
            size={44}
            className={cn("mx-auto", ratio >= 0.6 ? "text-emerald-500" : "text-amber-500")}
          />
          <h2 className="tk-display mt-3 text-[22px] font-bold">
            {ratio >= 0.8 ? "稳了" : ratio >= 0.6 ? "过线水平" : "回炉再战"}
          </h2>
          <p className="mt-1 text-[14px]" style={{ color: "var(--tk-muted)" }}>
            {score} / {questions.length} 正确(及格线 60%:{ratio >= 0.6 ? "已过" : "未过"})
          </p>
          <div
            className="mx-auto mt-4 h-2.5 w-64 overflow-hidden rounded-full"
            style={{ background: "rgba(0,0,0,0.06)" }}
          >
            <div
              className={cn(
                "h-full rounded-full transition-all duration-700 ease-out",
                ratio >= 0.6
                  ? "bg-gradient-to-r from-emerald-400 to-teal-500"
                  : "bg-gradient-to-r from-amber-400 to-orange-500",
              )}
              style={{ width: `${ratio * 100}%` }}
            />
          </div>
          <p
            className="mt-4 text-[12.5px]"
            style={{ color: "color-mix(in srgb, var(--tk-muted) 80%, transparent)" }}
          >
            作答已写入进度库,战况页可见派生的掌握度。
          </p>
          <button
            type="button"
            className="accent-gradient mt-5 inline-flex items-center gap-1.5 rounded-full px-5 py-2.5 text-[14px] font-semibold text-white shadow-md hover:opacity-90"
            onClick={onExit}
          >
            <ArrowRight size={15} /> 返回
          </button>
        </div>
        <div className="space-y-3">
          {answers.map((a, i) => (
            <div key={i} className="tk-card p-4">
              <div className="flex items-start gap-2.5">
                {a.picked === a.question.answer ? (
                  <CheckCircle2 size={17} className="mt-0.5 shrink-0 text-emerald-500" />
                ) : (
                  <XCircle size={17} className="mt-0.5 shrink-0 text-rose-400" />
                )}
                <div className="min-w-0">
                  <p className="prose-lesson text-[13.5px] font-medium">
                    {i + 1}. <InlineText text={a.question.stem} />
                  </p>
                  <p className="mt-1 text-[12.5px]" style={{ color: "var(--tk-muted)" }}>
                    你的答案:{LETTERS[a.picked]}
                    {a.picked !== a.question.answer && <> · 正确:{LETTERS[a.question.answer]}</>}
                  </p>
                  {a.picked !== a.question.answer && (
                    <p className="prose-lesson mt-1 text-[12.5px]" style={{ color: "var(--tk-muted)" }}>
                      <InlineText text={a.question.explanation} />
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // 作答页
  return (
    <div className="mx-auto max-w-2xl space-y-5 pt-6">
      <div className="flex items-center justify-between">
        <h1 className="tk-display text-[18px] font-bold">{title}</h1>
        <span className="text-[13px]" style={{ color: "var(--tk-muted)" }}>
          第 {idx + 1} / {questions.length} 题
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full" style={{ background: "rgba(0,0,0,0.06)" }}>
        <div
          className="accent-gradient h-full rounded-full transition-all duration-300"
          style={{ width: `${((idx + (judged ? 1 : 0)) / questions.length) * 100}%` }}
        />
      </div>
      <p
        className="text-center text-[11px]"
        style={{ color: "color-mix(in srgb, var(--tk-muted) 70%, transparent)" }}
      >
        键盘 A–D 或 1–4 作答 · Enter 下一题
      </p>

      <div className="tk-card p-6">
        <p className="prose-lesson text-[15.5px] font-medium leading-relaxed">
          <InlineText text={question.stem} />
        </p>
        <div className="mt-5 space-y-2.5">
          {question.options.map((opt, i) => (
            <button
              key={i}
              type="button"
              disabled={judged}
              className={cn(
                "flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-[14px] transition-all",
                !judged &&
                  "border-black/10 hover:border-[var(--tk-accent)] hover:bg-[var(--tk-accent-soft)]",
                judged && i === question.answer && "animate-pop border-emerald-400 bg-emerald-50",
                judged &&
                  picked === i &&
                  i !== question.answer &&
                  "animate-shake border-rose-300 bg-rose-50",
                judged && picked !== i && i !== question.answer && "border-black/5 opacity-55",
              )}
              onClick={() => submit(i)}
            >
              <span
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[12.5px] font-bold"
                style={{ background: "rgba(0,0,0,0.05)" }}
              >
                {LETTERS[i]}
              </span>
              <span className="prose-lesson">
                <InlineText text={opt} />
              </span>
              {judged && i === question.answer && (
                <CheckCircle2 size={18} className="ml-auto shrink-0 text-emerald-500" />
              )}
              {judged && picked === i && i !== question.answer && (
                <XCircle size={18} className="ml-auto shrink-0 text-rose-400" />
              )}
            </button>
          ))}
        </div>

        {judged && (
          <div className="mt-5">
            <div
              className={cn(
                "rounded-xl px-4 py-3.5 text-[13.5px] leading-relaxed",
                correct ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-800",
              )}
            >
              <b>{correct ? "答对了。" : "答错了。"}</b>
              {question.explanation}
            </div>
            <div className="mt-2.5 flex items-center justify-between">
              <span
                className="text-[11.5px]"
                style={{ color: "color-mix(in srgb, var(--tk-muted) 75%, transparent)" }}
              >
                出处:
                {question.source.relation === "authored"
                  ? "自造考点题"
                  : question.source.relation === "adapted"
                    ? "教材改编"
                    : "真题"}
                {question.source.locator ? ` · ${question.source.locator}` : ""}
              </span>
              <button
                type="button"
                className="accent-gradient inline-flex items-center gap-1 rounded-full px-4 py-2 text-[13px] font-semibold text-white shadow hover:opacity-90"
                onClick={advance}
              >
                {idx + 1 < questions.length ? "下一题" : "看结果"} <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
