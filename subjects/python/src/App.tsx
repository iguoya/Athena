// 骨架定位页：只陈述本应用是什么、在课程路线的哪一环，内容驱动 UI 随内容填充期
// 落地（ADR 0058）；定位信息在这里硬编码，前端不读 app.json（ADR 0046）。
const INFO = {
  title: "Python 与 AI 工具链",
  letter: "Py",
  accent: "#3776AB",
  group: "人工智能",
  route: "人工智能路线第 1 门（主仓库 ADR 0120）：应用线通 llm-app，原理线通 machine-learning",
  engine: "本机 Python/uv 子进程真跑（白名单 spawn）",
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
            <p className="skeleton-sub">{INFO.group} · 课程路线入口</p>
          </div>
        </header>
        <dl className="skeleton-facts">
          <div>
            <dt>路线位置</dt>
            <dd>{INFO.route}</dd>
          </div>
          <div>
            <dt>实验引擎</dt>
            <dd>{INFO.engine}</dd>
          </div>
          <div>
            <dt>状态</dt>
            <dd>骨架阶段（ADR 0120）：工程壳与规范先行，内容待填充。</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
