import { useEffect, useState } from "react";
import { fetchCatalog, type CatalogDto } from "./api";
import MindmapView from "./mindmap/MindmapView";
import OrbitScene from "./scene/OrbitScene";

export default function App() {
  const [catalog, setCatalog] = useState<CatalogDto | null>(null);
  const [view, setView] = useState<"orbit" | "mindmap">("orbit");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const pull = () =>
      fetchCatalog()
        .then((c) => {
          if (alive) {
            setCatalog(c);
            setError(null);
          }
        })
        .catch((e) => alive && setError(String(e)))
        .finally(() => {
          // 上一轮回来才排下一轮：命令慢于间隔时排队而不是叠加。
          if (alive) timer = setTimeout(pull, 3000);
        });
    pull();
    // 状态从系统实况读（ADR 0046）：骨架阶段轮询，事件推送留给下一轮。
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, []);

  if (error) return <div className="status">清单读取失败：{error}</div>;
  if (!catalog) return <div className="status">读取清单…</div>;

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative" }}>
      <div className="toolbar">
        <span className="brand">Athena 启动器</span>
        <button onClick={() => setView(view === "orbit" ? "mindmap" : "orbit")}>
          {view === "orbit" ? "椭圆视图" : "轨道视图"}
        </button>
        <span className="hint">点图标启动 · 悬停看关系（3D）</span>
      </div>
      {view === "orbit" ? (
        <OrbitScene catalog={catalog} />
      ) : (
        <MindmapView />
      )}
    </div>
  );
}
