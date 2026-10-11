// 历年真题列表:按年份成卷,点开即练(verbatim,作答计入掌握度)。
import { Play, ScrollText } from "lucide-react";
import { pastPaperFiles } from "../content";
import type { View } from "./types";

export default function PastExamsView({ go }: { go: (v: View) => void }) {
  return (
    <div className="space-y-6 pt-8">
      <header>
        <h1 className="tk-display text-[26px] font-bold tracking-tight">历年真题演练</h1>
        <p className="mt-1.5 text-[14px]" style={{ color: "var(--tk-muted)" }}>
          真题是判分内容的最高出处(verbatim)。按年份成卷练习,作答同样计入掌握度。
        </p>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {pastPaperFiles.map((p) => (
          <button
            key={p.id}
            type="button"
            className="tk-card tk-card-hover p-5 text-left"
            onClick={() => go({ kind: "past-quiz", paperId: p.id })}
          >
            <div className="accent-fg text-[12px] font-medium">
              {p.subject} · {p.session}
            </div>
            <div className="tk-display mt-1 text-[17px] font-bold">{p.title}</div>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-[12px]" style={{ color: "var(--tk-muted)" }}>
                {p.questions.length} 题 · 点开即练
              </span>
              <Play size={16} className="text-emerald-500" />
            </div>
          </button>
        ))}
      </section>

      <section className="tk-card mx-auto max-w-2xl p-5">
        <div className="flex items-center gap-2 text-[13.5px] font-bold">
          <ScrollText size={15} className="accent-fg" /> 继续扩卷
        </div>
        <p className="mt-2 text-[13px] leading-relaxed" style={{ color: "var(--tk-muted)" }}>
          用
          <code className="accent-soft accent-fg rounded px-1.5 py-0.5 font-mono text-[12px]">
            scripts/import-past-exam.py
          </code>
          从 qicoder 电子书导入更多年份(--list 看可导入的卷);导入格式与出处要求见
          content/past-exams/README.md。
        </p>
      </section>
    </div>
  );
}
