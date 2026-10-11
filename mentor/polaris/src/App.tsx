import { useEffect } from "react";
import { loadCatalog } from "@/content/load";
import { useApp } from "@/state/store";
import { TopBar } from "@/ui/TopBar";
import { BaseView } from "@/views/BaseView";
import { HomeView } from "@/views/HomeView";
import { RouteView } from "@/views/RouteView";

const catalog = loadCatalog();

export function App() {
  const loc = useApp((s) => s.loc);
  const edgeKey = useApp((s) => s.edgeKey);
  const setEdge = useApp((s) => s.setEdge);
  const selectNode = useApp((s) => s.selectNode);

  // Esc 一层一层退：先收连线卡片，再关抽屉（ADR 0013 决策 7：走进去，再走出来）。
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (edgeKey) setEdge(null);
      else if (loc.view !== "home" && loc.nodeId) selectNode(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [edgeKey, loc, setEdge, selectNode]);

  return (
    <div className="flex h-full flex-col">
      <TopBar catalog={catalog} />
      <main className="min-h-0 flex-1">
        {loc.view === "home" && <HomeView catalog={catalog} />}
        {loc.view === "route" && <RouteView key={loc.routeId} catalog={catalog} routeId={loc.routeId} nodeId={loc.nodeId} />}
        {loc.view === "base" && <BaseView key={loc.mapId} catalog={catalog} mapId={loc.mapId} nodeId={loc.nodeId} />}
      </main>
    </div>
  );
}
