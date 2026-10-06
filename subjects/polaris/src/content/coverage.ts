import type { Catalog } from "./catalog";
import type { Domain, PolarisNode, Route } from "./types";

/**
 * 十四个能力域（ADR 0018，ADR 0021 增加控制与电力两个）。`side` 只用来给雷达上色，说明这个域偏软件、偏硬件还是在软硬交界处；
 * 顺序就是雷达上的顺序：软件侧在上，交界处居中，硬件侧在下。
 */
export const DOMAINS: readonly { id: Domain; label: string; short: string; side: "software" | "boundary" | "hardware"; hint: string }[] = [
  { id: "foundations", short: "数理", label: "数学与理论", side: "software", hint: "离散数学、概率、线性代数：算法、信号与控制共用的判断语言" },
  { id: "programming", short: "程序", label: "程序设计与工程方法", side: "software", hint: "语言、工具链、测试与协作" },
  { id: "algorithms", short: "算法", label: "数据结构与算法", side: "software", hint: "复杂度、结构选择与正确性" },
  { id: "systems", short: "系统", label: "操作系统、网络与并发", side: "software", hint: "调度、内存、通信与并发" },
  { id: "acceleration", short: "加速", label: "并行、加速与 AI 系统", side: "boundary", hint: "GPU、加速器、模型编译与端侧推理" },
  { id: "security", short: "安全", label: "安全与可信", side: "boundary", hint: "启动链、根信任与物理攻击面" },
  { id: "assurance", short: "验证", label: "验证、可靠性与系统工程", side: "boundary", hint: "测试、在环验证、功能安全与接口管理" },
  { id: "embedded", short: "嵌入式", label: "嵌入式与软硬接口", side: "boundary", hint: "寄存器、中断、驱动、固件与板级支持" },
  { id: "architecture", short: "体系", label: "体系结构", side: "hardware", hint: "指令集、微架构、存储层次与软硬划分" },
  { id: "digital", short: "数字", label: "数字逻辑与 HDL", side: "hardware", hint: "同步时序、FPGA 与数字实现" },
  { id: "circuits", short: "电路", label: "电路、测量与电源", side: "hardware", hint: "模拟与数字电路、PCB、测量与功耗" },
  { id: "signals", short: "信号", label: "信号与通信", side: "hardware", hint: "信号处理、通信链路与测量系统" },
  { id: "control", short: "控制", label: "控制与自动化", side: "boundary", hint: "反馈控制、状态估计、运动控制与工业自动化" },
  { id: "power", short: "电力", label: "电力、电机与电力电子", side: "hardware", hint: "变换器、电机与驱动、电力系统" },
];

export interface DomainCoverage {
  domain: Domain;
  /** 这条路线在该域里引用的节点数。 */
  covered: number;
  /** 开放地图里该域的节点总数。 */
  total: number;
  /** covered / total，用于雷达。 */
  fraction: number;
}

function openNodes(catalog: Catalog): PolarisNode[] {
  return catalog.maps.flatMap((map) => map.nodes);
}

export function domainTotals(catalog: Catalog): Map<Domain, number> {
  const totals = new Map<Domain, number>();
  for (const node of openNodes(catalog)) {
    if (node.domain) totals.set(node.domain, (totals.get(node.domain) ?? 0) + 1);
  }
  return totals;
}

export function routeNodeIds(route: Route): Set<string> {
  return new Set(route.stages.flatMap((stage) => stage.nodes));
}

/** 一条路线在十四个域上各覆盖多少。由路线引用的节点的 domain 统计得到，不依赖任何个人数据。 */
export function routeCoverage(catalog: Catalog, route: Route): DomainCoverage[] {
  const totals = domainTotals(catalog);
  const counts = new Map<Domain, number>();
  for (const id of routeNodeIds(route)) {
    const domain = catalog.nodeById.get(id)?.domain;
    if (domain) counts.set(domain, (counts.get(domain) ?? 0) + 1);
  }
  return DOMAINS.map(({ id }) => {
    const total = totals.get(id) ?? 0;
    const covered = counts.get(id) ?? 0;
    return { domain: id, covered, total, fraction: total === 0 ? 0 : Math.min(1, covered / total) };
  });
}

export interface BlindSpot {
  domain: Domain;
  /** 通才阶梯里该域的节点，路线没有引用的，最多两个，作为「补什么」的建议。 */
  suggestions: PolarisNode[];
}

export const LADDER_ID = "route.generalist-ladder";

/**
 * 偏科提示：路线完全没碰到的能力域，以及从通才阶梯里挑出的补法。
 * 阶梯本身就是全覆盖的（测试守着），所以每个盲区都能给出建议。
 */
export function blindSpots(catalog: Catalog, route: Route): BlindSpot[] {
  const have = routeNodeIds(route);
  const ladder = catalog.routes.find((r) => r.id === LADDER_ID);
  const ladderNodes = ladder ? [...routeNodeIds(ladder)].map((id) => catalog.nodeById.get(id)!).filter(Boolean) : [];
  return routeCoverage(catalog, route)
    .filter((entry) => entry.covered === 0 && entry.total > 0)
    .map((entry) => ({
      domain: entry.domain,
      suggestions: ladderNodes.filter((node) => node.domain === entry.domain && !have.has(node.id)).slice(0, 2),
    }));
}

/** 路线碰到的能力域个数。 */
export function coveredDomains(catalog: Catalog, route: Route): number {
  return routeCoverage(catalog, route).filter((entry) => entry.covered > 0).length;
}
