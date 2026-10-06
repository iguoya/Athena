import type { Contract, Priority, RouteBalance, RouteLens, Stage } from "@/content/types";

// 界面上所有枚举的中文名与颜色变量，集中在这里，组件里不散落字符串。

export const PRIORITY_LABEL: Record<Priority, string> = {
  essential: "必要",
  important: "重要",
  optional: "可选",
};

export const PRIORITY_HINT: Record<Priority, string> = {
  essential: "缺了它，这个学科的培养目标就不成立",
  important: "系统与工程能力的一部分，缺了会有明显短板",
  optional: "台阶或方向选修，可以晚点再学",
};

export const CONTRACT_LABEL: Record<Contract, string> = {
  timing: "时序",
  memory: "存储与数据通路",
  bus: "总线与协议",
  power: "功耗与热",
  boot: "启动与可信",
  verify: "可验证与观测",
};

export const BALANCE_LABEL: Record<RouteBalance, string> = {
  software: "偏软件",
  balanced: "软硬各半",
  hardware: "偏硬件",
};

export const LENS_LABEL: Record<RouteLens, string> = {
  direction: "按技术方向",
  stack: "按层次",
  artifact: "按终点产物",
};

export const LENS_HINT: Record<RouteLens, string> = {
  direction: "选一个技术方向，沿它的阶段走下去",
  stack: "沿技术栈自底向上或自顶向下，把层与层的接缝走一遍",
  artifact: "先定终点制品，再倒推要学什么",
};

export const VALIDATION_LABEL: Record<string, string> = {
  measurement: "实测",
  benchmark: "基准对比",
  integration: "联调",
  review: "评审",
  simulation: "仿真",
  analysis: "分析",
};

export const VOLATILITY_LABEL: Record<string, string> = {
  stable: "稳定",
  evolving: "演进中",
  volatile: "变化快",
};

export const MASTERY_LABEL: Record<string, string> = {
  familiarity: "熟悉",
  usage: "运用",
  assessment: "评估",
};

export const RELATION_LABEL: Record<string, string> = {
  requires: "强先修",
  enables: "来路",
  adapted: "改编自",
  informed: "参考",
  see_also: "另见",
  verbatim: "原文",
  quoted: "引用",
  authored: "自撰",
};

export const stageVar = (stage: Stage | undefined): string => `var(--stage-${stage ?? "senior"})`;
export const contractVar = (contract: Contract): string => `var(--contract-${contract})`;
export const balanceVar = (balance: RouteBalance): string => `var(--balance-${balance})`;

export const TRACK_LABEL: Record<string, string> = {
  hardware: "硬件",
  electronics: "电子",
  systems: "系统",
  software: "软件",
  language: "语言",
  engineering: "工程",
  assurance: "验证与保障",
  compute: "计算",
  control: "控制",
  ai: "智能",
  capstone: "收口",
};
