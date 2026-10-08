// 内容在构建期静态打进 bundle:发行包不携带 content 资源,类型错误在 tsc 就拦下。
import registryJson from "../content/courses.json";
import swdCourseJson from "../content/swd/course.json";
import esdCourseJson from "../content/esd/course.json";
import papersJson from "../content/past-exams/papers.json";
import type {
  ChapterLesson,
  ChapterQuiz,
  Course,
  CourseRegistry,
  PastPaperRegistry,
  Section,
} from "./types";

import csNumberLesson from "../content/swd/chapters/cs-number.json";
import csCpuLesson from "../content/swd/chapters/cs-cpu.json";
import csMemoryLesson from "../content/swd/chapters/cs-memory.json";
import csIoLesson from "../content/swd/chapters/cs-io.json";
import csReliabilityLesson from "../content/swd/chapters/cs-reliability.json";
import csSecurityLesson from "../content/swd/chapters/cs-security.json";
import osProcessLesson from "../content/swd/chapters/os-process.json";
import osSchedLesson from "../content/swd/chapters/os-sched.json";
import osMemoryLesson from "../content/swd/chapters/os-memory.json";
import osFileLesson from "../content/swd/chapters/os-file.json";
import osDeviceLesson from "../content/swd/chapters/os-device.json";
import osRtosLesson from "../content/esd/chapters/os-rtos.json";

import csNumberQuiz from "../content/swd/quizzes/cs-number.json";
import csCpuQuiz from "../content/swd/quizzes/cs-cpu.json";
import csMemoryQuiz from "../content/swd/quizzes/cs-memory.json";
import csIoQuiz from "../content/swd/quizzes/cs-io.json";
import csReliabilityQuiz from "../content/swd/quizzes/cs-reliability.json";
import csSecurityQuiz from "../content/swd/quizzes/cs-security.json";
import osProcessQuiz from "../content/swd/quizzes/os-process.json";
import osSchedQuiz from "../content/swd/quizzes/os-sched.json";
import osMemoryQuiz from "../content/swd/quizzes/os-memory.json";
import osFileQuiz from "../content/swd/quizzes/os-file.json";
import osDeviceQuiz from "../content/swd/quizzes/os-device.json";
import osRtosQuiz from "../content/esd/quizzes/os-rtos.json";

const lessons: Record<string, ChapterLesson> = Object.fromEntries(
  [
    csNumberLesson,
    csCpuLesson,
    csMemoryLesson,
    csIoLesson,
    csReliabilityLesson,
    csSecurityLesson,
    osProcessLesson,
    osSchedLesson,
    osMemoryLesson,
    osFileLesson,
    osDeviceLesson,
    osRtosLesson,
  ].map((l) => [l.section_id, l as unknown as ChapterLesson]),
);

const quizzes: Record<string, ChapterQuiz> = Object.fromEntries(
  [
    csNumberQuiz,
    csCpuQuiz,
    csMemoryQuiz,
    csIoQuiz,
    csReliabilityQuiz,
    csSecurityQuiz,
    osProcessQuiz,
    osSchedQuiz,
    osMemoryQuiz,
    osFileQuiz,
    osDeviceQuiz,
    osRtosQuiz,
  ].map((q) => [q.section_id, q as unknown as ChapterQuiz]),
);

export const registry = registryJson as unknown as CourseRegistry;

export const courses: Course[] = [
  swdCourseJson as unknown as Course,
  esdCourseJson as unknown as Course,
];

export const pastPapers = papersJson as unknown as PastPaperRegistry;

export function courseById(id: string): Course {
  const found = courses.find((c) => c.id === id);
  if (!found) throw new Error(`未知课程:${id}`);
  return found;
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
  course: Course;
  chapter: import("./types").Chapter;
  section: Section;
}

/** 跨课程定位一个节。 */
export function findSection(courseId: string, sectionId: string): SectionRef {
  const course = courseById(courseId);
  for (const chapter of course.chapters) {
    const section = chapter.sections.find((s) => s.id === sectionId);
    if (section) return { course, chapter, section };
  }
  throw new Error(`课程 ${courseId} 没有节 ${sectionId}`);
}

/** 全部「有评级的节」跨课程索引:requires 校验与仪表用。 */
export function allGradedSections() {
  return courses.flatMap((c) =>
    c.chapters.flatMap((ch) =>
      ch.sections.filter((s) => s.kp).map((s) => ({ course: c, chapter: ch, section: s })),
    ),
  );
}

/** 全部节(含待建),仪表的完整清单用。 */
export function allSections() {
  return courses.flatMap((c) =>
    c.chapters.flatMap((ch) =>
      ch.sections.map((s) => ({ course: c, chapter: ch, section: s })),
    ),
  );
}
