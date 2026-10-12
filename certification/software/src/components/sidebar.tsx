// 左侧菜单:全局导航 + 课程章树。课程组可折叠,当前课程的组自动展开,
// 激活节高亮——学习流里切章切节不再经过课程页。
import { BookOpen, ChevronDown, Gauge, Home, ScrollText } from "lucide-react";
import { courses } from "../content";
import type { View } from "../App";

export function Sidebar({ view, go }: { view: View; go: (v: View) => void }) {
  const activeCourseId =
    view.kind === "course" || view.kind === "topic" || view.kind === "quiz"
      ? view.courseId
      : null;
  const activeSectionId = view.kind === "topic" || view.kind === "quiz" ? view.sectionId : null;

  const navBtn = (active: boolean) =>
    `flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-[13.5px] font-medium transition-colors ${
      active ? "bg-brand-500 text-white shadow-sm" : "text-ink/65 hover:bg-brand-50 hover:text-brand-700"
    }`;

  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-black/5 bg-white/60">
      <div className="flex items-center gap-2.5 px-4 pb-2 pt-4">
        <img src="/icon.svg" alt="" width={34} height={34} className="rounded-xl" />
        <div>
          <div className="text-[15px] font-bold leading-tight">软考</div>
          <div className="text-[11px] text-ink/45">两科同时 ≥45 通过</div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 pb-6">
        <button type="button" className={navBtn(view.kind === "home")} onClick={() => go({ kind: "home" })}>
          <Home size={16} /> 首页
        </button>

        {courses.map((c) => {
          const open = activeCourseId === c.id;
          return (
            <div key={c.id} className="mt-1">
              <button
                type="button"
                onClick={() => go({ kind: "course", courseId: c.id })}
                className={`flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-[13.5px] font-semibold transition-colors ${
                  open ? "bg-brand-50 text-brand-800" : "text-ink/65 hover:bg-brand-50 hover:text-brand-700"
                }`}
              >
                <BookOpen size={16} style={{ color: open ? c.accent : undefined }} />
                <span className="flex-1 text-left">{c.title}</span>
                <ChevronDown
                  size={14}
                  className={`transition-transform ${open ? "rotate-0" : "-rotate-90"}`}
                />
              </button>
              {open && (
                <div className="mb-1 ml-4 border-l border-black/8 pl-2">
                  {c.chapters.map((ch) => (
                    <div key={ch.id} className="mt-1.5">
                      <div className="px-2 py-1 text-[11.5px] font-semibold text-ink/40">
                        第 {ch.no} 章 · {ch.title}
                      </div>
                      {ch.sections.length === 0 ? (
                        <div className="px-2 py-0.5 text-[11.5px] text-ink/25">待建</div>
                      ) : (
                        ch.sections.map((sec) => {
                          const active = activeSectionId === sec.id;
                          return (
                            <button
                              key={sec.id}
                              type="button"
                              onClick={() => go({ kind: "topic", courseId: c.id, sectionId: sec.id })}
                              className={`block w-full rounded-lg px-2 py-1 text-left text-[12.5px] transition-colors ${
                                active
                                  ? "bg-brand-500 font-semibold text-white"
                                  : "text-ink/60 hover:bg-brand-50 hover:text-brand-700"
                              }`}
                            >
                              {sec.title}
                            </button>
                          );
                        })
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        <div className="mt-1 border-t border-black/5 pt-2">
          <button type="button" className={navBtn(view.kind === "past")} onClick={() => go({ kind: "past" })}>
            <ScrollText size={16} /> 真题演练
          </button>
          <button type="button" className={navBtn(view.kind === "dashboard")} onClick={() => go({ kind: "dashboard" })}>
            <Gauge size={16} /> 战况
          </button>
        </div>
      </nav>
    </aside>
  );
}
