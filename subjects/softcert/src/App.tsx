import { useEffect, useState } from "react";
import { registry } from "./content";
import { Sidebar } from "./components/sidebar";
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

  return (
    <div className="flex min-h-screen">
      <Sidebar view={view} go={setView} />

      <main className="min-w-0 flex-1 px-6 pb-16 pt-4">
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

      <footer className="fixed bottom-0 right-0 left-64 border-t border-black/5 bg-white/70 py-3 text-center text-[11.5px] text-ink/35 backdrop-blur">
        {registry.exam.full_name} · 两科同时 ≥{registry.exam.passing_score} 分通过 ·
        菜单目录对齐官方教材,出处在 content/sources.json
      </footer>
    </div>
  );
}
