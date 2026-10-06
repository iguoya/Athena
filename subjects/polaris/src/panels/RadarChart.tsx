import { DOMAINS, type DomainCoverage } from "@/content/coverage";
import { balanceVar } from "@/ui/labels";

/** 域所在的侧：软件、硬件、软硬交界（用「软硬各半」的颜色）。 */
export const sideColor = (side: "software" | "boundary" | "hardware"): string =>
  balanceVar(side === "boundary" ? "balanced" : side);

interface Props {
  coverage: DomainCoverage[];
  size?: number;
}

/**
 * 全部能力域的覆盖雷达（ADR 0018）。半径取覆盖率的平方根，免得小域被大域压扁；
 * 没碰到的域在轴端画一个空心点，并不只靠颜色——旁边的列表也会写出来。
 */
export function RadarChart({ coverage, size = 260 }: Props) {
  const center = size / 2;
  const radius = size / 2 - 36;
  const point = (index: number, r: number): [number, number] => {
    const angle = -Math.PI / 2 + (index / DOMAINS.length) * Math.PI * 2;
    return [center + Math.cos(angle) * r, center + Math.sin(angle) * r];
  };
  const polygon = coverage
    .map((entry, index) => point(index, radius * Math.sqrt(entry.fraction)).join(","))
    .join(" ");

  return (
    <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} role="img" aria-label="能力域覆盖雷达" className="shrink-0">
      {[0.25, 0.5, 0.75, 1].map((ring) => (
        <polygon
          key={ring}
          points={DOMAINS.map((_, i) => point(i, radius * Math.sqrt(ring)).join(",")).join(" ")}
          fill="none"
          stroke="var(--line)"
          strokeWidth={1}
        />
      ))}
      {DOMAINS.map((domain, index) => {
        const [x, y] = point(index, radius);
        const [lx, ly] = point(index, radius + 17);
        const entry = coverage[index];
        const missing = entry.covered === 0;
        const anchor = Math.abs(lx - center) < 6 ? "middle" : lx > center ? "start" : "end";
        return (
          <g key={domain.id}>
            <line x1={center} y1={center} x2={x} y2={y} stroke="var(--line)" strokeWidth={1} />
            <circle
              cx={x}
              cy={y}
              r={4}
              fill={missing ? "var(--surface)" : sideColor(domain.side)}
              stroke={sideColor(domain.side)}
              strokeWidth={1.6}
            />
            <text x={lx} y={ly} textAnchor={anchor} dominantBaseline="middle" fontSize={10.5} fill={missing ? "var(--faint)" : "var(--ink)"}>
              {domain.short}
              <title>{`${domain.label}：${entry.covered} / ${entry.total}`}</title>
            </text>
          </g>
        );
      })}
      <polygon points={polygon} fill="var(--accent)" fillOpacity={0.18} stroke="var(--accent)" strokeWidth={2} strokeLinejoin="round" />
      {coverage.map((entry, index) => {
        if (entry.covered === 0) return null;
        const [x, y] = point(index, radius * Math.sqrt(entry.fraction));
        return <circle key={entry.domain} cx={x} cy={y} r={3} fill="var(--accent)" />;
      })}
    </svg>
  );
}
