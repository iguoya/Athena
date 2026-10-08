import { ScrollText, FileDown, ShieldCheck, Play } from "lucide-react";
import type { PastPaperFile } from "../types";
import type { View } from "../App";
import { QuizRunner } from "./quiz";

// 卷子文件由 scripts/import-past-exam.py 生成,构建期收集——导入即出现在列表里。
const paperModules = import.meta.glob<{ default: PastPaperFile }>(
  "../../content/past-exams/papers/*.json",
  { eager: true },
);
const paperFiles: PastPaperFile[] = Object.values(paperModules)
  .map((m) => m.default)
  .sort((a, b) => b.year - a.year || b.session.localeCompare(a.session));

export function PastExamsPage({ go }: { go: (v: View) => void }) {
  const papers = paperFiles;
  return (
    <div className="space-y-6 pt-8">
      <header>
        <h1 className="text-[26px] font-bold tracking-tight">历年真题演练</h1>
        <p className="mt-1.5 text-[14px] text-ink/60">
          真题是判分内容的最高出处(verbatim)。按年份成卷练习,作答同样计入掌握度。
        </p>
      </header>

      {papers.length === 0 ? (
        <EmptyGuide />
      ) : (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {papers.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => go({ kind: "past-quiz", paperId: p.id })}
              className="card card-hover p-5 text-left"
            >
              <div className="text-[12px] font-medium text-brand-600">
                {p.subject} · {p.session}
              </div>
              <div className="mt-1 text-[17px] font-bold">{p.title}</div>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-[12px] text-ink/45">{p.questions.length} 题 · 点开即练</span>
                <Play size={16} className="text-emerald-500" />
              </div>
            </button>
          ))}
        </section>
      )}

      <section className="card mx-auto max-w-2xl p-5">
        <div className="flex items-center gap-2 text-[13.5px] font-bold">
          <ScrollText size={15} className="text-brand-600" /> 继续扩卷
        </div>
        <p className="mt-2 text-[13px] leading-relaxed text-ink/60">
          用 <code className="rounded bg-brand-50 px-1.5 py-0.5 font-mono text-[12px]">scripts/import-past-exam.py</code>{" "}
          从 qicoder 电子书导入更多年份(--list 看可导入的卷);软设真题 PDF 全套
          (2009–2023)在 huafeishuzhi/exam-ruankao 仓库,嵌入式真题在同站电子书。
        </p>
      </section>
    </div>
  );
}

function EmptyGuide() {
  return (
    <div className="card mx-auto max-w-2xl p-8 text-center">
      <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-fuchsia-500 to-purple-600 text-white shadow-lg">
        <ScrollText size={26} />
      </span>
      <h2 className="mt-4 text-[18px] font-bold">还没有导入真题卷</h2>
      <p className="mx-auto mt-2 max-w-md text-[13.5px] leading-relaxed text-ink/60">
        运行 scripts/import-past-exam.py 从 qicoder 电子书导入;导入格式与出处要求见
        content/past-exams/README.md。
      </p>
      <div className="mx-auto mt-5 max-w-md space-y-2.5 text-left">
        <Step icon={<FileDown size={15} />} text="--list 列出可导入的历年卷" />
        <Step icon={<ShieldCheck size={15} />} text="--from-url 导入,题目 verbatim 入库、出处自动登记" />
      </div>
    </div>
  );
}

function Step({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-2.5 rounded-xl bg-paper px-3.5 py-2.5 text-[13px] text-ink/70">
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-600">
        {icon}
      </span>
      {text}
    </div>
  );
}

/** 真题卷练习:与随堂考核同一个作答器,mode=past-exam。 */
export function PastPaperQuizPage({ paperId, go }: { paperId: string; go: (v: View) => void }) {
  const paper = paperFiles.find((p) => p.id === paperId);
  if (!paper) {
    return (
      <div className="pt-10 text-center text-[14px] text-ink/50">
        卷子 {paperId} 不在构建产物里——确认 content/past-exams/papers/ 下有对应文件后重新构建。
      </div>
    );
  }
  return (
    <QuizRunner
      title={paper.title}
      questions={paper.questions}
      mode="past-exam"
      course="past-exam"
      chapterId={paper.id}
      kpId={paper.id}
      onExit={() => go({ kind: "past" })}
    />
  );
}
