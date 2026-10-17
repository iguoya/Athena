import { useEffect, useState } from "react";
import { listen } from "@tauri-apps/api/event";
import {
  fetchCatalog,
  patchStates,
  rescanApps,
  type CatalogDto,
  type RescanResult,
  type StateRow,
} from "./api";
import { useWindowVisible } from "./visibility";
import MindmapView from "./mindmap/MindmapView";
import OrbitScene from "./scene/OrbitScene";

function formatRescan(result: RescanResult): string {
  if (!result.changed) return `没有变化，共 ${result.total} 个`;
  const parts: string[] = [];
  if (result.added.length > 0) parts.push(`新增 ${result.added.join("、")}`);
  if (result.removed.length > 0) parts.push(`移除 ${result.removed.join("、")}`);
  return parts.join("；") || `已更新，共 ${result.total} 个`;
}

export default function App() {
  const [catalog, setCatalog] = useState<CatalogDto | null>(null);
  const [view, setView] = useState<"orbit" | "mindmap">("orbit");
  // 归档默认不呈现（ADR 0139）；思维导图视图可开关查看，3D 视图不做开关。
  const [showArchived, setShowArchived] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [scanNote, setScanNote] = useState<string | null>(null);
  const visible = useWindowVisible();

  const onScan = () => {
    setScanning(true);
    setScanNote(null);
    rescanApps()
      .then((result) => setScanNote(formatRescan(result)))
      .catch((e) => setScanNote(String(e)))
      .finally(() => setScanning(false));
  };

  useEffect(() => {
    // 托盘常驻时挂起。回来时读一次当前清单；新目录要等「扫描应用」。
    // 状态点由后端在变了的时候推过来。
    if (!visible) return;
    let alive = true;
    const pull = () =>
      fetchCatalog()
        .then((c) => {
          if (!alive) return;
          setCatalog(c);
          setError(null);
        })
        .catch((e) => alive && setError(String(e)));
    pull();
    const catalogSub = listen("launcher://catalog-changed", () => {
      if (alive) pull();
    });
    const stateSub = listen<StateRow[]>("launcher://states", (event) => {
      if (!alive) return;
      setCatalog((prev) => {
        if (!prev) return prev;
        const apps = patchStates(prev.apps, event.payload);
        return apps ? { ...prev, apps } : prev;
      });
    });
    return () => {
      alive = false;
      catalogSub.then((unlisten) => unlisten());
      stateSub.then((unlisten) => unlisten());
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
        <button onClick={onScan} disabled={scanning}>
          {scanning ? "扫描中…" : "扫描应用"}
        </button>
        {scanNote && <span className="hint">{scanNote}</span>}
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
