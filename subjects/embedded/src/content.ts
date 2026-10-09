// 内容在构建期静态打进 bundle:发行包不携带 content 资源,类型错误在 tsc 就拦下。
// 本应用单课程:course.json 就是根,不再有 courses.json 注册表层。
import courseJson from "../content/esd/course.json";
import papersJson from "../content/past-exams/papers.json";
import type {
  Chapter,
  ChapterLesson,
  ChapterQuiz,
  Course,
  KpSummary,
  PastExamQuestion,
  PastPaperFile,
  PastPaperRegistry,
  Section,
} from "./types";

import esdMcuLesson from "../content/esd/chapters/esd-mcu.json";
import esdMemoryLesson from "../content/esd/chapters/esd-memory.json";
import esdBusLesson from "../content/esd/chapters/esd-bus.json";
import esdTaskMgmtLesson from "../content/esd/chapters/esd-task-mgmt.json";
import osRtosLesson from "../content/esd/chapters/os-rtos.json";

import esdMcuQuiz from "../content/esd/quizzes/esd-mcu.json";
import esdMemoryQuiz from "../content/esd/quizzes/esd-memory.json";
import esdBusQuiz from "../content/esd/quizzes/esd-bus.json";
import osRtosQuiz from "../content/esd/quizzes/os-rtos.json";

export const course = courseJson as unknown as Course;

const lessons: Record<string, ChapterLesson> = Object.fromEntries(
  [esdMcuLesson, esdMemoryLesson, esdBusLesson, esdTaskMgmtLesson, osRtosLesson].map((l) => [
    l.section_id,
    l as unknown as ChapterLesson,
  ]),
);

const quizzes: Record<string, ChapterQuiz> = Object.fromEntries(
  [esdMcuQuiz, esdMemoryQuiz, esdBusQuiz, osRtosQuiz].map((q) => [
    q.section_id,
    q as unknown as ChapterQuiz,
  ]),
);

export const pastPapers = papersJson as unknown as PastPaperRegistry;

// 卷子文件由 scripts/import-past-exam.py 生成,构建期收集——导入即生效。
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const paperModules = import.meta.glob<any>("../../content/past-exams/papers/*.json", {
  eager: true,
});
export const pastPaperFiles = Object.values(paperModules)
  .map((m) => m.default as PastPaperFile)
  .sort((a, b) => b.year - a.year || b.session.localeCompare(a.session));

/** 按知识点正则筛选历年真题(verbatim)。 */
export function pastExamQuestions(pattern: string): PastExamQuestion[] {
  const re = new RegExp(pattern);
  return pastPaperFiles
    .flatMap((p) => p.questions)
    .filter((q) => re.test(q.knowledge ?? "") || re.test(q.stem));
}

export function lessonOf(sectionId: string): ChapterLesson {
  const found = lessons[sectionId];
  if (!found) throw new Error(`节 ${sectionId} 还没有教学内容`);
  return found;
}

export function quizOf(sectionId: string): ChapterQuiz {
  const found = quizzes[sectionId];
  if (!found) throw new Error(`节 ${sectionId} 还没有考核题`);
  return found;
}

export interface SectionRef {
  chapter: Chapter;
  section: Section;
}

export function findSection(sectionId: string): SectionRef {
  for (const chapter of course.chapters) {
    const section = chapter.sections.find((s) => s.id === sectionId);
    if (section) return { chapter, section };
  }
  throw new Error(`课程没有节 ${sectionId}`);
}

/** 全部「有评级的节」索引:requires 校验与仪表用。 */
export function allGradedSections() {
  return course.chapters.flatMap((ch) =>
    ch.sections.filter((s) => s.kp).map((s) => ({ chapter: ch, section: s })),
  );
}

/** 全部节(含待建),仪表的完整清单用。 */
export function allSections() {
  return course.chapters.flatMap((ch) =>
    ch.sections.map((s) => ({ chapter: ch, section: s })),
  );
}

/** 知识点在作答记录上的掌握率:正确率 × 作答量饱和(8 题封顶),无记录为 0。 */
export function masteryOf(kpId: string | undefined, summary: KpSummary[]): number {
  if (!kpId) return 0;
  const s = summary.find((x) => x.kp_id === kpId);
  if (!s || s.total === 0) return 0;
  return Math.min(1, s.correct / s.total) * Math.min(1, s.total / 8);
}
