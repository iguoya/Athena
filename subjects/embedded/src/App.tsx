// 应用骨架:顶部指挥台 + 全宽单列内容。
// 与 softcert 的「左侧栏 + 内容区」刻意区分(ADR 0090:两种体验):全局导航
// (视图胶囊 + 皮肤切换)全部收进固定顶栏,不设侧栏;课程导航走课程页的
// 学习路径时间线。
import { useEffect, useState } from "react";
import { BookOpen, Gauge, Home, Palette, ScrollText, type LucideIcon } from "lucide-react";
import { course } from "./content";
import { SKINS, applySkin, currentSkin, type SkinId } from "./theme";
import HomeView from "./views/HomeView";
import CourseView from "./views/CourseView";
import TopicView from "./views/TopicView";
import QuizView from "./views/QuizView";
import PastExamsView from "./views/PastExamsView";
import PaperQuizView from "./views/PaperQuizView";
import DashboardView from "./views/DashboardView";
import type { View } from "./views/types";
import { cn } from "@/lib/utils";

// 顶栏视图胶囊:course 在课程/学习/考核视图下都亮
const NAV: { kind: "home" | "course" | "past" | "dashboard"; label: string; icon: LucideIcon }[] = [
  { kind: "home", label: "首页", icon: Home },
  { kind: "course", label: "学习路径", icon: BookOpen },
  { kind: "past", label: "真题演练", icon: ScrollText },
  { kind: "dashboard", label: "战况", icon: Gauge },
];

export default function App() {
  const [view, setView] = useState<View>({ kind: "home" });
  const [skin, setSkin] = useState<SkinId>(currentSkin());

  const go = (v: View) => setView(v);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [view]);

  const activeSectionId = view.kind === "topic" || view.kind === "quiz" ? view.sectionId : null;

  function navActive(kind: View["kind"]): boolean {
    if (kind === "course") return view.kind === "course" || activeSectionId !== null;
    if (kind === "past") return view.kind === "past" || view.kind === "past-quiz";
    return view.kind === kind;
  }

  function pickSkin(id: SkinId) {
    setSkin(id);
    applySkin(id);
  }

  return (
    <>
      <div className="app-backdrop" />
      <div className="flex min-h-screen flex-col">
        {/* 顶部指挥台 */}
        <header
          className="sticky top-0 z-20 border-b"
          style={{
            borderColor: "var(--tk-line)",
            background: "var(--tk-surface)",
            backdropFilter: "blur(12px)",
          }}
        >
          <div className="mx-auto flex h-14 max-w-[1100px] items-center gap-3 px-6">
            <img src="/icon.svg" alt="" width="30" height="30" className="rounded-lg" />
            <div className="min-w-0">
              <div className="tk-display truncate text-[14px] font-bold leading-tight">嵌入式系统设计师</div>
              <div className="text-[10.5px]" style={{ color: "var(--tk-muted)" }}>
                软考中级 · 一年一考
              </div>
            </div>

            <nav className="ml-auto flex items-center gap-1">
              {NAV.map((item) => (
                <button
                  key={item.kind}
                  type="button"
                  className={cn(
                    "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-colors",
                    navActive(item.kind)
                      ? "accent-gradient text-white shadow-sm"
                      : "hover:bg-[var(--tk-accent-soft)]",
                  )}
                  onClick={() => go({ kind: item.kind })}
                >
                  <item.icon size={15} />
                  {item.label}
                </button>
              ))}
            </nav>

            {/* 皮肤切换:一套组件、令牌换氛围 */}
            <div
              className="ml-1 flex items-center gap-1.5 border-l pl-3"
              style={{ borderColor: "var(--tk-line)" }}
            >
              {SKINS.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  title={`${s.name} · ${s.hint}`}
                  className={cn(
                    "h-6 w-6 rounded-full border-2 transition-transform hover:scale-110",
                    skin === s.id ? "border-[var(--tk-accent)]" : "border-transparent",
                  )}
                  style={{ background: s.dot }}
                  onClick={() => pickSkin(s.id)}
                />
              ))}
              <Palette size={13} className="ml-0.5" style={{ color: "var(--tk-muted)" }} />
            </div>
          </div>
        </header>

        {/* 主视图:全宽单列居中 */}
        <main className="mx-auto w-full max-w-[1100px] flex-1 px-6 pb-12 pt-6">
          {view.kind === "home" && <HomeView go={go} />}
          {view.kind === "course" && <CourseView go={go} />}
          {view.kind === "topic" && <TopicView key={view.sectionId} sectionId={view.sectionId} go={go} />}
          {view.kind === "quiz" && <QuizView key={view.sectionId} sectionId={view.sectionId} go={go} />}
          {view.kind === "past" && <PastExamsView go={go} />}
          {view.kind === "past-quiz" && <PaperQuizView key={view.paperId} paperId={view.paperId} go={go} />}
          {view.kind === "dashboard" && <DashboardView />}
        </main>

        <footer
          className="border-t py-4 text-center text-[11.5px]"
          style={{
            borderColor: "var(--tk-line)",
            color: "color-mix(in srgb, var(--tk-muted) 70%, transparent)",
          }}
        >
          软考中级·嵌入式系统设计师 · {course.exam.score_range} ·
          菜单目录对齐官方教材,出处在 content/sources.json
        </footer>
      </div>
    </>
  );
}
