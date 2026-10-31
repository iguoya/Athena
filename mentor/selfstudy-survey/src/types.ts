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
  // 办学类型（四川社会型/应用型等），同专业不同类型各一条
  mode?: string | null;
  // 本省专业码映射到国标专业的依据（北京自有码靠「旧专业名称」列）
  matched_by?: string;
  complete?: { courses?: boolean; credits?: boolean; textbook?: boolean };
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
  hosts?: string[];
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
  // 除考试院外的自考官方门户/管理系统（往往才是计划与教材的存放地）
  selfstudy_portal?: { name: string; url: string; verify: Verify } | null;
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

// 待人工核实清单（content/pending.json）：代理查不到或未取证、需要人确认的缺口，
// 与按波次推进的采集排期，分组列出。字段含义以文件内 "_" 说明为准。
export interface PendingItem {
  id: string;
  group: "human" | "todo";
  province?: string;
  provinces?: string[];
  priority?: "high" | "medium" | "low";
  scope?: string;
  title: string;
  detail?: string;
  tried?: string;
  howto?: string;
}

export interface PendingDoc {
  schema: number;
  updated: string;
  groups: { id: string; label: string; desc: string }[];
  items: PendingItem[];
}
