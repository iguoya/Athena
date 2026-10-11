import { useEffect, useState } from "react";
import { fetchCatalog, type CatalogDto } from "./api";
import { useWindowVisible } from "./visibility";
import MindmapView from "./mindmap/MindmapView";
import OrbitScene from "./scene/OrbitScene";

export default function App() {
  const [catalog, setCatalog] = useState<CatalogDto | null>(null);
  const [view, setView] = useState<"orbit" | "mindmap">("orbit");
  // 归档默认不呈现（ADR 0139）；思维导图视图可开关查看，3D 视图不做开关。
  const [showArchived, setShowArchived] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const visible = useWindowVisible();

  useEffect(() => {
    // 托盘常驻时挂起：不拉清单也不排下一轮，回来时立即拉一次。
    if (!visible) return;
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let lastSig = "";
    let pulls = 0;
    const pull = () =>
      fetchCatalog()
        .then((c) => {
          if (!alive) return;
          // 后端每轮重建 DTO，状态没变就不进 React：稳态轮询零重渲染。
          // 图标文件内容的变化签名上看不见，每 10 轮（约 30 秒）强制刷一次兜底。
          const sig = c.apps
            .map((a) => `${a.id}:${a.state}:${a.lifecycle}:${a.orbit}:${a.pos.join()}`)
            .join(",");
          pulls += 1;
          if (sig !== lastSig || pulls % 10 === 0) {
            lastSig = sig;
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
  }, [visible]);

  if (error) return <div className="status">清单读取失败：{error}</div>;
  if (!catalog) return <div className="status">读取清单…</div>;

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative" }}>
      <div className="toolbar">
        <span className="brand">Athena 启动器</span>
        <button onClick={() => setView(view === "orbit" ? "mindmap" : "orbit")}>
          {view === "orbit" ? "椭圆视图" : "轨道视图"}
        </button>
        {view === "mindmap" && (
          <label style={{ display: "inline-flex", alignItems: "center", gap: 5, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            显示归档
          </label>
        )}
        <span className="hint">点图标启动 · 悬停看关系（3D）</span>
      </div>
      {view === "orbit" ? (
        <OrbitScene catalog={catalog} paused={!visible} />
      ) : (
        <MindmapView paused={!visible} showArchived={showArchived} />
      )}
    </div>
  );
}
