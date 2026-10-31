// 内容在构建期由 Vite 打进前端：数据是几十个 JSON，不值得走一趟运行期读取（ADR 0174 同款）。
// 省份文件一省一份，glob 引入；缺文件不会报错，所以覆盖率在界面上如实显示，而不是在这里兜底。
import scopeJson from "../content/scope.json";
import athenaJson from "../content/athena-map.json";
import pendingJson from "../content/pending.json";
import type {
  CourseInfo,
  Offering,
  OfferStatus,
  PendingDoc,
  Plan,
  Province,
  Scope,
  Textbook,
} from "./types";

export const scope = scopeJson as unknown as Scope;
export const pending = pendingJson as unknown as PendingDoc;
// 课程库与教材库按成员分文件存放（两个代理并行采集，同一个 JSON 会读改写互相覆盖），读取时合并。
const courseFiles = import.meta.glob("../content/courses/*.json", { eager: true, import: "default" });
const textbookFiles = import.meta.glob("../content/textbooks/*.json", { eager: true, import: "default" });
function merge<T>(files: Record<string, unknown>, key: string): Record<string, T> {
  const out: Record<string, T> = {};
  for (const f of Object.values(files)) Object.assign(out, (f as Record<string, Record<string, T>>)[key]);
  return out;
}
export const courses = merge<CourseInfo>(courseFiles, "courses");
export const textbooks = merge<Textbook>(textbookFiles, "textbooks");
export const athenaMap = (athenaJson as unknown as { map: Record<string, string[]> }).map;

const modules = import.meta.glob("../content/provinces/*.json", { eager: true, import: "default" });
// 按行政区划惯例的地理顺序排（北京、天津、河北……），不按拼音，读者按地区找省更顺手。
const ORDER = [
  "beijing", "tianjin", "hebei", "shanxi", "neimenggu", "liaoning", "jilin", "heilongjiang",
  "shanghai", "jiangsu", "zhejiang", "anhui", "fujian", "jiangxi", "shandong", "henan",
  "hubei", "hunan", "guangdong", "guangxi", "hainan", "chongqing", "sichuan", "guizhou",
  "yunnan", "xizang", "shaanxi", "gansu", "qinghai", "ningxia", "xinjiang",
];
export const provinces: Province[] = (Object.values(modules) as Province[]).sort(
  (a, b) => ORDER.indexOf(a.id) - ORDER.indexOf(b.id),
);

// 计划的主考院校：以 offerings 为准（主考变动频繁、有自己的核对记录），plan 级只在计划间确有差异时写。
export function planHosts(province: Province, plan: Plan): string[] {
  if (plan.hosts?.length) return plan.hosts;
  const o = province.offerings.find((x) => x.plans?.includes(plan.id));
  return o?.hosts ?? [];
}

export const majorName = (code: string) => scope.majors.find((m) => m.code === code)?.name ?? code;
export const majorsOfClass = (cls: string) => scope.majors.filter((m) => m.class === cls);

export interface PlanRef {
  province: Province;
  plan: Plan;
}

export const allPlans: PlanRef[] = provinces.flatMap((province) =>
  province.plans.map((plan) => ({ province, plan })),
);

export function offeringsOf(province: Province, major: string): Offering[] {
  return province.offerings.filter((o) => o.major === major);
}

// 一个格子可能有多条（方向不同、主考院校不同）；多条取「最积极」的状态给矩阵着色。
const RANK: OfferStatus[] = ["open", "upcoming", "stopped", "none", "pending"];
export function cellStatus(province: Province, major: string): OfferStatus {
  const os = offeringsOf(province, major);
  if (os.length === 0) return "pending";
  return os.map((o) => o.status).sort((a, b) => RANK.indexOf(a) - RANK.indexOf(b))[0];
}

export const STATUS_LABEL: Record<OfferStatus, string> = {
  open: "开考",
  stopped: "停考",
  upcoming: "新计划",
  none: "未开设",
  pending: "待查",
};

export const CATEGORY_LABEL: Record<string, string> = {
  public: "公共课",
  required: "必考",
  topup: "加考",
  basic: "专业基础",
  core: "专业核心",
  elective: "选考",
  practice: "实践课",
  graduation: "毕业环节",
};

export const LEVEL_LABEL: Record<string, string> = {
  official: "官方原文",
  notice: "官方发布",
  report: "第三方线索",
  pending: "待核对",
};

export const EXAM_LABEL: Record<string, string> = {
  unified: "全国统考",
  provincial: "省统考",
  host: "主考院校",
};

export function isStale(date?: string): boolean {
  if (!date) return false;
  const t = Date.parse(date);
  return Number.isFinite(t) && Date.now() - t > 365 * 24 * 3600 * 1000;
}

// 覆盖率：矩阵格子里「有人核对过」的比例，以及其中官方来源的比例。
export function coverage() {
  const majors = scope.majors;
  const total = provinces.length * majors.length;
  let known = 0;
  let official = 0;
  for (const p of provinces) {
    for (const m of majors) {
      const os = offeringsOf(p, m.code).filter((o) => o.status !== "pending");
      if (os.length > 0) {
        known += 1;
        if (os.some((o) => o.verify.level === "official" || o.verify.level === "notice")) official += 1;
      }
    }
  }
  return { total, known, official, plans: allPlans.length };
}
