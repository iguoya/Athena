export type ViewId =
  | "overview"
  | "majors"
  | "provinces"
  | "courses"
  | "textbooks"
  | "practice"
  | "events"
  | "method";

export interface Route {
  view: ViewId;
  major?: string;
  province?: string;
  course?: string;
}

export type Go = (r: Route) => void;

export const VIEWS: { id: ViewId; label: string; hint: string }[] = [
  { id: "overview", label: "总览", hint: "省 × 专业开设矩阵" },
  { id: "majors", label: "专业", hint: "同一专业跨省课程对比" },
  { id: "provinces", label: "省份", hint: "考期、政策与开考专业" },
  { id: "courses", label: "课程", hint: "课程在哪些省出现" },
  { id: "textbooks", label: "教材", hint: "指定教材与版次" },
  { id: "practice", label: "实践环节", hint: "实践考核与毕业设计" },
  { id: "events", label: "变动", hint: "新旧计划与停考" },
  { id: "method", label: "方法与来源", hint: "核对规则与覆盖率" },
];
