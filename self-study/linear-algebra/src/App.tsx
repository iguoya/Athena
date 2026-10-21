import { useEffect, useMemo, useState } from "react";
import curriculumBundled from "../content/curriculum.json";
import knowledgeBundled from "../content/knowledge.json";
import { invoke } from "./api";
import { SectionView } from "./SectionView";
import type { Curriculum, KnowledgePoint, SectionContent } from "./types";

// 内容是唯一源（content/），构建时打包进前端：应用独立可运行，不依赖壳提供逐节读盘命令。
const sectionModules = import.meta.glob("../content/sections/*.json", { eager: true }) as Record<
  string,
  { default: SectionContent }
>;
const sections: Record<string, SectionContent> = Object.fromEntries(
  Object.entries(sectionModules).map(([path, mod]) => [
    path.split("/").pop()!.replace(/\.json$/, ""),
    mod.default,
  ]),
);

export const figures: Record<string, string> = import.meta.glob("../content/sections/assets/*.svg", {
  query: "?raw",
  import: "default",
  eager: true,
});

const curriculum = curriculumBundled as Curriculum;
const knowledge = (knowledgeBundled as { knowledge: KnowledgePoint[] }).knowledge;

export function App() {
  const knowledgeMap = useMemo(
    () => Object.fromEntries(knowledge.map((k) => [k.id, k])) as Record<string, KnowledgePoint>,
    [],
  );
  const [mastery, setMastery] = useState<Record<string, number>>({});
  const [current, setCurrent] = useState<string | null>(null);

  useEffect(() => {
    invoke<Record<string, number>>("load_all_mastery")
      .then(setMastery)
      .catch(() => setMastery({}));
  }, []);

  async function bumpMastery(ids: string[], correct: boolean) {
    const next = { ...mastery };
    for (const id of ids) {
      const cur = next[id] ?? 0;
      next[id] = correct ? Math.min(cur + 1, 5) : Math.max(cur - 1, 0);
      await invoke("save_mastery", { topicId: id, value: next[id] }).catch(() => {});
    }
    setMastery(next);
  }

  const total = knowledge.length;
  const touched = knowledge.filter((k) => (mastery[k.id] ?? 0) > 0).length;

  return (
    <div className="app">
      <aside className="sidebar">
        <h1 className="course-title">{curriculum.course.title}</h1>
        <p className="course-code">课程代码 {curriculum.course.code}</p>
        <div className="course-info">
          <p>
            教材：《{curriculum.course.textbook.title}》
            {curriculum.course.textbook.authors} 主编，
            {curriculum.course.textbook.press}
            {curriculum.course.textbook.year}年版
          </p>
          {curriculum.course.textbook.note && (
            <p className="course-note">{curriculum.course.textbook.note}</p>
          )}
          <p>
            学法：以{curriculum.course.method.primary}为主，{curriculum.course.method.secondary}
            为辅。
          </p>
          <p className="course-progress">
            已动笔 {touched}/{total} 个知识点
          </p>
        </div>
        <nav>
          {curriculum.chapters.map((ch) => (
            <div key={ch.id} className="chapter">
              <div className="chapter-title">
                {ch.no} {ch.title}
              </div>
              {ch.sections.map((sec) => (
                <button
                  key={sec.id}
                  className={`section-link ${current === sec.id ? "active" : ""} ${
                    sections[sec.id] ? "" : "missing"
                  }`}
                  onClick={() => setCurrent(sec.id)}
                  disabled={!sections[sec.id]}
                >
                  <span>
                    {sec.no} {sec.title}
                  </span>
                  <span className="dots">
                    {sec.knowledge.map((kid) => (
                      <i
                        key={kid}
                        className={`dot m${mastery[kid] ?? 0}`}
                        title={knowledgeMap[kid]?.title ?? kid}
                      />
                    ))}
                  </span>
                </button>
              ))}
            </div>
          ))}
        </nav>
      </aside>
      <main className="main">
        {current && sections[current] ? (
          <SectionView
            key={current}
            content={sections[current]}
            curriculum={curriculum}
            knowledgeMap={knowledgeMap}
            onAnswered={bumpMastery}
          />
        ) : (
          <div className="intro">
            <h2>{curriculum.course.title}</h2>
            <p>
              从左侧选一节开始。题目以历年真题与教材例题为主（每道判分题都标出处）；
              先看节首的提取题，再动笔算例题，最后做练习。
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
