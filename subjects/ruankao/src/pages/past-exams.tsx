import { ScrollText, FileDown, ShieldCheck } from "lucide-react";
import { pastPapers } from "../content";

/** 真题演练:papers.json 为空是预期状态(整卷真题待授权),界面要把这件事说明白。 */
export function PastExamsPage() {
  const papers = pastPapers.papers;
  return (
    <div className="space-y-6 pt-8">
      <header>
        <h1 className="text-[26px] font-bold tracking-tight">历年真题演练</h1>
        <p className="mt-1.5 text-[14px] text-ink/60">
          真题是判分内容的最高出处。按年份成卷练习,作答同样计入掌握度。
        </p>
      </header>

      {papers.length === 0 ? (
        <div className="card mx-auto max-w-2xl p-8 text-center">
          <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-fuchsia-500 to-purple-600 text-white shadow-lg">
            <ScrollText size={26} />
          </span>
          <h2 className="mt-4 text-[18px] font-bold">真题卷还空着——这是预期状态</h2>
          <p className="mx-auto mt-2 max-w-md text-[13.5px] leading-relaxed text-ink/60">
            整卷真题尚未取得再分发授权,不进仓库。章节考核里的自造题都带考纲出处;
            真题按下面的流程导入后,这里会自动按年份列出成卷练习。
          </p>
          <div className="mx-auto mt-5 max-w-md space-y-2.5 text-left">
            <Step icon={<FileDown size={15} />} text="取得官方真题集(如《试题分析与解答》年度合辑)" />
            <Step icon={<ShieldCheck size={15} />} text="按 content/past-exams/README.md 的格式一卷一文件录入,relation 用 verbatim" />
            <Step icon={<ScrollText size={15} />} text="在 papers.json 登记,跑 python3 scripts/check.py 过出处检查" />
          </div>
        </div>
      ) : (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {papers.map((p) => (
            <div key={p.id} className="card card-hover p-5">
              <div className="text-[12px] font-medium text-brand-600">{p.subject} · {p.session}</div>
              <div className="mt-1 text-[17px] font-bold">{p.title}</div>
              <div className="mt-2 text-[12px] text-ink/45">出处:{p.source_note}</div>
            </div>
          ))}
        </section>
      )}
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
