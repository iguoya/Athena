// 视图路由类型:单课程应用,视图不带 courseId。
export type View =
  | { kind: "home" }
  | { kind: "course" }
  | { kind: "topic"; sectionId: string }
  | { kind: "quiz"; sectionId: string }
  | { kind: "past" }
  | { kind: "past-quiz"; paperId: string }
  | { kind: "dashboard" };
