// 骨架定位页：只陈述本应用是什么、在课程路线的哪一环，内容驱动 UI 随内容填充期
// 落地（ADR 0058）；定位信息在这里硬编码，前端不读 app.json（ADR 0046）。
const INFO = {
  title: "端侧 AI 推理与部署",
  letter: "EA",
  accent: "#0F766E",
  group: "人工智能",
  route: "把模型压小、转格式，在固定设备上测出延迟、内存与精度并满足预算（ADR 0152）",
};

export default function App() {
  return (
    <main className="skeleton-page">
      <section className="skeleton-card">
        <header className="skeleton-head">
          <span className="skeleton-badge" style={{ background: INFO.accent }}>
            {INFO.letter}
          </span>
          <div>
            <h1>{INFO.title}</h1>
            <p className="skeleton-sub">{INFO.group} · ADR 0152 课程路线</p>
          </div>
        </header>
        <dl className="skeleton-facts">
          <div>
            <dt>路线位置</dt>
            <dd>{INFO.route}</dd>
          </div>
          <div>
            <dt>状态</dt>
            <dd>立项与骨架：第 1–5 章按顺序编写中，上板与 NPU 一章等开发板到手后再写。</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
