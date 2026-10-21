// 推荐路径图：三站横排、箭头指方向、工具线挂在下方。点击任何一张卡片滚到它的详情。
import type { Guide, GuideNode } from "./types";

function jump(id: string) {
  document.getElementById(`node-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function Station({ stage, node, index }: { stage: Guide["stages"][number]; node: GuideNode; index: number }) {
  return (
    <button className="station" onClick={() => jump(node.id)}>
      <span className="station-step">第 {["一", "二", "三"][index]}站</span>
      <span className="station-name">{node.title}</span>
      <span className="station-claim">{stage.claim}</span>
      <span className="station-go">看详情 ↓</span>
    </button>
  );
}

export default function PathMap({ guide }: { guide: Guide }) {
  const byId = new Map(guide.nodes.map((n) => [n.id, n]));
  const stages = guide.graph.order
    .map((id) => ({ id, stage: guide.stages.find((s) => s.node === id) }))
    .filter((x): x is { id: string; stage: Guide["stages"][number] } => Boolean(x.stage));
  const tools = guide.graph.tools.map((id) => byId.get(id)).filter((n): n is GuideNode => Boolean(n));
  const companions = guide.companions;

  return (
    <div className="pathmap">
      <div className="pathmap-main">
        {stages.map(({ id, stage }, i) => (
          <div className="pathmap-cell" key={id}>
            {i > 0 && (
              <div className="pathmap-arrow" aria-hidden="true">
                <svg viewBox="0 0 64 24" preserveAspectRatio="none">
                  <line x1="0" y1="12" x2="52" y2="12" className="arrow-line" />
                  <polygon points="50,6 62,12 50,18" className="arrow-head" />
                </svg>
                <span className="arrow-label">{i === 1 ? "直观在场，再练体系" : "教材读完，对考试组织"}</span>
              </div>
            )}
            <Station stage={stage} node={byId.get(id)!} index={i} />
          </div>
        ))}
      </div>

      <div className="pathmap-tools">
        <div className="pathmap-drop" aria-hidden="true">
          <svg viewBox="0 0 24 40" preserveAspectRatio="none">
            <line x1="12" y1="0" x2="12" y2="30" className="drop-line" />
            <polygon points="6,28 12,40 18,28" className="drop-head" />
          </svg>
          <span>随时穿插，不占站</span>
        </div>
        <div className="tool-chips">
          {tools.map((t) => (
            <button key={t.id} className="tool-chip" onClick={() => jump(t.id)}>
              <strong>{t.title}</strong>
              <span>{t.kind}</span>
            </button>
          ))}
          {companions.map((c) => (
            <div key={c.id} className="tool-chip companion">
              <strong>{c.title}</strong>
              <span>随手实验台 · 不必学</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
