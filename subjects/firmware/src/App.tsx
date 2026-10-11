import { cn } from "@/lib/utils";

// 骨架定位页：只陈述本应用是什么、承接什么，内容驱动 UI 随内容填充期落地
// （ADR 0058）；定位信息在这里硬编码，前端不读 app.json（ADR 0046）。
const INFO = {
  title: "嵌入式程序设计",
  letter: "嵌",
  accent: "#5A2A8A",
  exam: "软考中级·嵌入式系统设计师",
  chapters: "第 6、8、11 章（嵌入式程序设计、模块测试、案例编程题）",
  parentTitle: "嵌入式系统设计师",
  engine: "gcc 真编译 + 位级可视化",
};

const FACTS: { label: string; value: string }[] = [
  { label: "承接章节", value: INFO.chapters },
  { label: "实验引擎", value: INFO.engine },
  { label: "状态", value: "骨架阶段（ADR 0103）：工程壳与规范先行，内容待填充。" },
];

export default function App() {
  return (
    <main className="grid min-h-screen place-items-center p-8">
      <section className="max-w-[720px] rounded-2xl border border-line bg-surface px-10 py-8">
        <header className="flex items-center gap-4">
          <span
            className={cn(
              "grid size-14 place-items-center rounded-[14px] text-[28px] font-bold text-white",
            )}
            style={{ background: INFO.accent }}
          >
            {INFO.letter}
          </span>
          <div>
            <h1 className="m-0 text-2xl">{INFO.title}</h1>
            <p className="mt-1 text-sm text-muted">
              {INFO.exam} · 实践课程（挂靠 {INFO.parentTitle}）
            </p>
          </div>
        </header>
        <dl className="mt-6 grid gap-3">
          {FACTS.map((f) => (
            <div key={f.label} className="grid grid-cols-[96px_1fr] gap-3">
              <dt className="text-sm text-muted">{f.label}</dt>
              <dd className="m-0 text-sm leading-relaxed">{f.value}</dd>
            </div>
          ))}
        </dl>
      </section>
    </main>
  );
}
