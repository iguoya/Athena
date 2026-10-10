// 骨架定位页：只陈述本应用是什么、在课程路线的哪一环，内容驱动 UI 随内容填充期
// 落地（ADR 0058）；定位信息在这里硬编码，前端不读 app.json（ADR 0046）。
const INFO = {
  title: "深度学习与 PyTorch",
  letter: "DL",
  accent: "#7C3AED",
  group: "人工智能",
  route: "大模型的底层地基（ADR 0120）",
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
            <p className="skeleton-sub">{INFO.group} · ADR 0120 课程路线</p>
          </div>
        </header>
        <dl className="skeleton-facts">
          <div>
            <dt>路线位置</dt>
            <dd>{INFO.route}</dd>
          </div>
          <div>
            <dt>状态</dt>
            <dd>骨架阶段（ADR 0122）：工程壳与规范先行，内容待填充。</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
