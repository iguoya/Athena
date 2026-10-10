import { openApp, stopApp, type AppDto, type CatalogDto } from "../api";

const STATE_LABEL: Record<AppDto["state"], string> = {
  stopped: "未运行",
  starting: "启动中…",
  ready: "运行中",
};

function Tile({ app }: { app: AppDto }) {
  return (
    <div
      className="tile"
      data-state={app.state}
      title={`${app.summary}\n${STATE_LABEL[app.state]}（双击停止）`}
      onClick={() => openApp(app.id).catch(console.error)}
      onContextMenu={(e) => {
        e.preventDefault();
        if (app.state !== "stopped") stopApp(app.id).catch(console.error);
      }}
    >
      {app.icon ? (
        <img src={app.icon} alt="" />
      ) : (
        <div className="fallback" style={{ background: app.accent }}>
          {app.letter}
        </div>
      )}
      <span className="name">{app.title}</span>
      <span className="dot" />
    </div>
  );
}

// 2D 平铺视图：按领域分区的快速启动网格（同一份 catalog 数据，与 3D 共享后端）。
export default function FlatView({ catalog }: { catalog: CatalogDto }) {
  const groups = new Map<string, AppDto[]>();
  for (const app of catalog.apps) {
    const key = app.group ?? "其他";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(app);
  }
  return (
    <div style={{ height: "100vh", overflowY: "auto", padding: "52px 24px 24px" }}>
      {[...groups.entries()].map(([name, apps]) => (
        <section key={name} style={{ marginBottom: 28 }}>
          <h3 style={{ fontSize: 13, color: "#6b7086", margin: "8px 4px", fontWeight: 600 }}>
            {name}
          </h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {apps.map((a) => (
              <Tile key={a.id + a.pos.join()} app={a} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
