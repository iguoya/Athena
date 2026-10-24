// 数据模型的类型镜像，字段含义以 comms/selfstudy-survey/artifacts/claude-code/DESIGN.md §3 为准。
// 校验（枚举、引用、verify 规则）归 scripts/check.py，这里只描述形状。

export type Level = "official" | "notice" | "report" | "pending";

export interface Verify {
  level: Level;
  source?: string;
  date?: string;
  note?: string;
}

export type OfferStatus = "open" | "stopped" | "upcoming" | "none" | "pending";
export type Category = "public" | "basic" | "core" | "required" | "elective" | "topup" | "practice" | "graduation";
export type ExamKind = "unified" | "provincial" | "host" | null;

export interface TextItem {
  text: string;
  verify: Verify;
}

export interface Authority {
  name: string | null;
  url: string | null;
  verify: Verify;
}

export interface CalendarEntry {
  session: string;
  exam?: string;
  register?: string;
  note?: string;
  verify: Verify;
}

export interface Policy {
  entry: TextItem | null;
  graduate: TextItem | null;
  degree: TextItem | null;
  exemption: TextItem | null;
}

export interface Offering {
  major: string;
  track: string | null;
  local_code?: string;
  status: OfferStatus;
  hosts: string[];
  plans?: string[];
  verify: Verify;
}

export interface PracticeInfo {
  type: string;
  credits?: number;
  note?: string;
}

export interface PlanCourse {
  code: string;
  name: string;
  credits: number;
  category: Category;
  elective_group: string | null;
  exam: ExamKind;
  practice: PracticeInfo | null;
  // 实践课行指向它所配的理论课代码（广东等省实践课单列课程代码与学分）
  pair?: string | null;
  textbook: string | null;
  note?: string;
}

export interface Plan {
  id: string;
  major: string;
  track: string | null;
  hosts: string[];
  version: string;
  effective: string | null;
  state: "current" | "legacy" | "upcoming" | "superseded";
  source_files?: string[];
  total_credits: number | null;
  required_credits: number | null;
  rules?: string;
  courses: PlanCourse[];
  graduation: { thesis: boolean; credits: number; note?: string } | null;
  verify: Verify;
}

export interface EventItem {
  date: string;
  kind: "new-plan" | "stop" | "code-change" | "policy" | "other";
  major?: string;
  text: string;
  verify: Verify;
}

export interface Province {
  schema: number;
  id: string;
  name: string;
  authority: Authority;
  calendar: CalendarEntry[];
  policy: Policy;
  offerings: Offering[];
  plans: Plan[];
  events: EventItem[];
}

export interface Scope {
  updated: string;
  catalog: { name: string; verified: boolean };
  classes: { code: string; name: string; tier: "core" | "edge" }[];
  majors: { code: string; name: string; class: string; tier: "core" | "edge" }[];
}

export interface CourseInfo {
  name: string;
  aliases?: string[];
  kind: "theory" | "practice" | "mixed" | "graduation";
  note?: string;
}

export interface Textbook {
  title: string;
  authors: string[];
  publisher: string;
  edition: string;
  isbn: string | null;
  kind: "national" | "host" | "provincial" | "other" | null;
  outline?: string;
  verify: Verify;
}
