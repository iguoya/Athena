// 内容在构建期静态打进 bundle:发行包不携带 content 资源,类型错误在 tsc 就拦下。
import registryJson from "../content/courses.json";
import csCourseJson from "../content/computer-system/course.json";
import osCourseJson from "../content/operating-system/course.json";
import papersJson from "../content/past-exams/papers.json";
import type {
  ChapterLesson,
  ChapterQuiz,
  Course,
  CourseRegistry,
  PastPaperRegistry,
} from "./types";

import csNumberLesson from "../content/computer-system/chapters/cs-number.json";
import csCpuLesson from "../content/computer-system/chapters/cs-cpu.json";
import csMemoryLesson from "../content/computer-system/chapters/cs-memory.json";
import csIoLesson from "../content/computer-system/chapters/cs-io.json";
import csReliabilityLesson from "../content/computer-system/chapters/cs-reliability.json";
import csSecurityLesson from "../content/computer-system/chapters/cs-security.json";
import osProcessLesson from "../content/operating-system/chapters/os-process.json";
import osSchedLesson from "../content/operating-system/chapters/os-sched.json";
import osMemoryLesson from "../content/operating-system/chapters/os-memory.json";
import osFileLesson from "../content/operating-system/chapters/os-file.json";
import osDeviceLesson from "../content/operating-system/chapters/os-device.json";
import osRtosLesson from "../content/operating-system/chapters/os-rtos.json";

import csNumberQuiz from "../content/computer-system/quizzes/cs-number.json";
import csCpuQuiz from "../content/computer-system/quizzes/cs-cpu.json";
import csMemoryQuiz from "../content/computer-system/quizzes/cs-memory.json";
import csIoQuiz from "../content/computer-system/quizzes/cs-io.json";
import csReliabilityQuiz from "../content/computer-system/quizzes/cs-reliability.json";
import csSecurityQuiz from "../content/computer-system/quizzes/cs-security.json";
import osProcessQuiz from "../content/operating-system/quizzes/os-process.json";
import osSchedQuiz from "../content/operating-system/quizzes/os-sched.json";
import osMemoryQuiz from "../content/operating-system/quizzes/os-memory.json";
import osFileQuiz from "../content/operating-system/quizzes/os-file.json";
import osDeviceQuiz from "../content/operating-system/quizzes/os-device.json";
import osRtosQuiz from "../content/operating-system/quizzes/os-rtos.json";

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
  ].map((l) => [l.chapter_id, l as unknown as ChapterLesson]),
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
  ].map((q) => [q.chapter_id, q as unknown as ChapterQuiz]),
);

export const registry = registryJson as unknown as CourseRegistry;

export const courses: Course[] = [
  csCourseJson as unknown as Course,
  osCourseJson as unknown as Course,
];

export const pastPapers = papersJson as unknown as PastPaperRegistry;

export function courseById(id: string): Course {
  const found = courses.find((c) => c.id === id);
  if (!found) throw new Error(`未知课程:${id}`);
  return found;
}

export function lessonOf(chapterId: string): ChapterLesson {
  const found = lessons[chapterId];
  if (!found) throw new Error(`章节 ${chapterId} 还没有教学内容`);
  return found;
}

export function quizOf(chapterId: string): ChapterQuiz {
  const found = quizzes[chapterId];
  if (!found) throw new Error(`章节 ${chapterId} 还没有考核题`);
  return found;
}

/** 全部知识点跨课程索引:requires 校验与仪表用。 */
export function allKps() {
  return courses.flatMap((c) =>
    c.chapters.map((ch) => ({ course: c, chapter: ch, kp: ch.kp })),
  );
}
