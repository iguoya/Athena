import { useEffect, useState } from "react";
import { GraduationCap, ScrollText, Gauge, Home } from "lucide-react";
import { courses, registry } from "./content";
import { HomePage } from "./pages/home";
import { CoursePage } from "./pages/course";
import { TopicPage } from "./pages/topic";
import { PastExamsPage, PastPaperQuizPage } from "./pages/past-exams";
import { DashboardPage } from "./pages/dashboard";
import { QuizPage } from "./pages/quiz";

export type View =
  | { kind: "home" }
  | { kind: "course"; courseId: string }
  | { kind: "topic"; courseId: string; sectionId: string }
  | { kind: "quiz"; courseId: string; sectionId: string }
  | { kind: "past" }
  | { kind: "past-quiz"; paperId: string }
  | { kind: "dashboard" };

export default function App() {
  const [view, setView] = useState<View>({ kind: "home" });

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [view]);

  const navBtn = (active: boolean) =>
    `flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[13.5px] font-medium transition-colors ${
      active ? "bg-brand-500 text-white shadow-sm" : "text-ink/60 hover:bg-brand-50 hover:text-brand-700"
    }`;

  return (
    <div className="min-h-screen">
      <header className="glass-nav sticky top-0 z-20 border-b border-black/5">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-2 px-5">
          <img src="/icon.svg" alt="" width={30} height={30} className="rounded-lg" />
          <span className="mr-2 text-[15px] font-bold">软考</span>
          <button type="button" className={navBtn(view.kind === "home")} onClick={() => setView({ kind: "home" })}>
            <Home size={15} /> 首页
          </button>
          {courses.map((c) => (
            <button
              key={c.id}
              type="button"
              className={navBtn(view.kind === "course" && view.courseId === c.id || view.kind === "topic" && view.courseId === c.id || view.kind === "quiz" && view.courseId === c.id)}
              onClick={() => setView({ kind: "course", courseId: c.id })}
            >
              <GraduationCap size={15} /> {c.title}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-1">
            <button type="button" className={navBtn(view.kind === "past")} onClick={() => setView({ kind: "past" })}>
              <ScrollText size={15} /> 真题演练
            </button>
            <button type="button" className={navBtn(view.kind === "dashboard")} onClick={() => setView({ kind: "dashboard" })}>
              <Gauge size={15} /> 战况
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 pb-16">
        {view.kind === "home" && <HomePage go={setView} />}
        {view.kind === "course" && <CoursePage courseId={view.courseId} go={setView} />}
        {view.kind === "topic" && (
          <TopicPage
            courseId={view.courseId}
            sectionId={view.sectionId}
            go={setView}
          />
        )}
        {view.kind === "quiz" && (
          <QuizPage courseId={view.courseId} sectionId={view.sectionId} go={setView} />
        )}
        {view.kind === "past" && <PastExamsPage go={setView} />}
        {view.kind === "past-quiz" && <PastPaperQuizPage paperId={view.paperId} go={setView} />}
        {view.kind === "dashboard" && <DashboardPage />}
      </main>

      <footer className="border-t border-black/5 py-6 text-center text-[12px] text-ink/40">
        {registry.exam.full_name} · 两科同时 ≥{registry.exam.passing_score} 分通过 ·
        菜单目录对齐官方教材,出处在 content/sources.json,真题导入见 content/past-exams/README.md
      </footer>
    </div>
  );
}
