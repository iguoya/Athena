// 骨架定位页：只陈述本应用是什么、承接什么，内容驱动 UI 随内容填充期落地
// （ADR 0058）；定位信息在这里硬编码，前端不读 app.json（ADR 0046）。
const INFO = {
  title: "网络与信息安全",
  letter: "网",
  accent: "#B03A2E",
  exam: "软考中级·软件设计师",
  chapters: "第 10 章（网络与信息安全）",
  parentTitle: "软件设计师",
  engine: "Tokio 真 socket + RustCrypto 真算",
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
            <p className="skeleton-sub">
              {INFO.exam} · 实践课程（挂靠 {INFO.parentTitle}）
            </p>
          </div>
        </header>
        <dl className="skeleton-facts">
          <div>
            <dt>承接章节</dt>
            <dd>{INFO.chapters}</dd>
          </div>
          <div>
            <dt>实验引擎</dt>
            <dd>{INFO.engine}</dd>
          </div>
          <div>
            <dt>状态</dt>
            <dd>骨架阶段（ADR 0103）：工程壳与规范先行，内容待填充。</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
