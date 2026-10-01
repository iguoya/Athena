import { NAV } from "@/components/nav";
import { useLocation } from "react-router";

// Pages that later milestones fill in (see the milestones in the scope doc).
export function Placeholder() {
  const { pathname } = useLocation();
  const label = NAV.find((n) => n.to === pathname)?.label ?? "";
  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="font-display text-4xl font-semibold">{label}</h1>
      <div className="glass mt-6 p-8 text-muted">这一页在后面的里程碑里做。</div>
    </div>
  );
}
