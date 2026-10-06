// `content/polaris.json` 的形状。内容契约由 scripts/contract.py 守（ADR 0015 决策 2），
// 这里只描述形状，运行时不再校验，也不再声明契约里没有的字段。

export type ViewKind = "academic" | "codesign" | "frontier" | "career" | "engineering" | "target";
export type Stage = "junior" | "intermediate" | "senior";
export type Priority = "essential" | "important" | "optional";
export type Relation = "requires" | "enables";

/** 软硬接口节点属于哪一份跨层契约（ADR 0016 决策 4）。 */
export type Contract = "timing" | "memory" | "bus" | "power" | "boot" | "verify";

/** 十二个能力域（ADR 0018 决策 1）：衡量一条路线是否偏科的尺子。 */
export type Domain =
  | "foundations"
  | "programming"
  | "algorithms"
  | "systems"
  | "acceleration"
  | "security"
  | "assurance"
  | "embedded"
  | "architecture"
  | "digital"
  | "circuits"
  | "signals";

export interface SourceRef {
  relation: string;
  source_id: string;
  locator: string;
}

export interface Chapter {
  id: string;
  title: string;
  summary: string;
  mastery: "familiarity" | "usage" | "assessment";
  kind?: "theory" | "practice";
  hands_on?: boolean;
  requires?: string[];
  /** 这一章的出处；必须是所属节点自己引用过的来源（ADR 0019）。 */
  ref?: { source_id: string; locator: string };
}

export interface PolarisNode {
  id: string;
  title: string;
  track: string;
  stable_definition: string;
  engineering_role: string;
  practice: string;
  validation: string;
  validation_note?: string;
  volatility: "stable" | "evolving" | "volatile";
  source_refs: SourceRef[];
  requires?: string[];
  pitfall?: string;
  priority?: Priority;
  priority_reason?: string;
  industry_reason?: string;
  stage?: Stage;
  stage_reason?: string;
  targets?: string[];
  app?: string;
  entry?: boolean;
  verify?: "code" | "board" | "bench";
  chapters?: Chapter[];
  /** 开放地图的节点必有。 */
  domain?: Domain;
  // 软硬接口节点（view_kind 为 codesign）
  contract?: Contract;
  hw_side?: string;
  sw_side?: string;
}

export interface PolarisEdge {
  from: string;
  to: string;
  relation: Relation;
  rationale: string;
  evidence_refs: SourceRef[];
  strong?: boolean;
}

export interface TheoryTopic {
  name: string;
  content: string;
  role: string;
}

export interface PolarisMap {
  id: string;
  title: string;
  summary: string;
  view_kind: ViewKind;
  graph_kind?: "course";
  nodes: PolarisNode[];
  edges: PolarisEdge[];
  theory?: TheoryTopic[];
}

export type RouteLens = "direction" | "stack" | "artifact";
export type RouteBalance = "software" | "balanced" | "hardware";

export interface RouteStage {
  title: string;
  goal: string;
  nodes: string[];
  checkpoint: string;
}

export interface Route {
  id: string;
  title: string;
  summary: string;
  lens: RouteLens;
  balance: RouteBalance;
  audience: string;
  artifact: string;
  stages: RouteStage[];
  /** 常见的偏科与补法（ADR 0018）。 */
  pitfalls?: string[];
  /** 高端岗位能力画像：来自公开招聘的时效性样本，不构成录用承诺。 */
  profile?: string;
  source_refs: SourceRef[];
}

export interface Principle {
  id: string;
  title: string;
  body: string;
  source_refs: SourceRef[];
}

export interface Source {
  id: string;
  title: string;
  url: string;
  kind: string;
}

export interface PolarisDocument {
  title: string;
  subtitle: string;
  maps: PolarisMap[];
  cross_edges: PolarisEdge[];
  routes?: Route[];
  principles?: Principle[];
}
