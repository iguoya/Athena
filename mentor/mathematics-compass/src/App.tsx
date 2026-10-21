// 数学罗盘：导引正文 + 一张活路径图。全部内容来自 content/guide.json（构建期打包）。
import { useEffect, useMemo, useState } from "react";
import guideData from "../content/guide.json";
import type { Guide } from "./types";
import PathMap from "./PathMap";
import NodeCard from "./NodeCard";
import renderInline from "./Inline";

const guide = guideData as Guide;

function CompassMark() {
  return (
    <svg viewBox="0 0 48 48" className="mark" aria-hidden="true">
      <circle cx="24" cy="24" r="21" className="mark-ring" />
      <circle cx="24" cy="24" r="2.4" className="mark-hub" />
      <polygon points="24,7 28,24 24,41 20,24" className="mark-needle-n" />
      <polygon points="7,24 24,20 41,24 24,28" className="mark-needle-e" />
    </svg>
  );
}

export default function App() {
  const byId = useMemo(() => new Map(guide.nodes.map((n) => [n.id, n])), []);
  const [active, setActive] = useState("overview");

  const nav = useMemo(
    () => [
      { id: "overview", label: "导读" },
      { id: "path", label: "推荐路径" },
      ...guide.stages.map((s) => ({ id: `stage-${s.id}`, label: s.name })),
      { id: "tools", label: "工具线" },
      { id: "books", label: "两本书怎么选" },
      { id: "gap", label: "高数缺口" },
    ],
    [],
  );

  useEffect(() => {
    const sections = nav.map((n) => document.getElementById(n.id)).filter((el): el is HTMLElement => Boolean(el));
    const obs = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActive(visible[0].target.id);
      },
      { rootMargin: "-10% 0px -70% 0px" },
    );
    sections.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, [nav]);

  return (
    <div className="shell">
      <header className="masthead">
        <CompassMark />
        <div>
          <h1>数学罗盘</h1>
          <p>
            数学学习导引 · 主线：{guide.mainline} · 只指路，不教课 · 内容核对于 {guide.updated}
          </p>
        </div>
      </header>

      <div className="body">
        <nav className="toc" aria-label="目录">
          {nav.map((n) => (
            <a key={n.id} href={`#${n.id}`} className={active === n.id ? "on" : ""}>
              {n.label}
            </a>
          ))}
        </nav>

        <main>
          <section id="overview">
            <p className="claim">{renderInline(guide.overview.claim, "ov-claim")}</p>
            {guide.overview.paragraphs.map((p, i) => (
              <p key={i}>{renderInline(p, `ov-${i}`)}</p>
            ))}
            <div className="howto">
              <h3>怎么用这张地图</h3>
              <ul>
                {guide.overview.howto.map((h, i) => (
                  <li key={i}>{renderInline(h, `how-${i}`)}</li>
                ))}
              </ul>
            </div>
          </section>

          <section id="path">
            <h2>推荐路径</h2>
            <p className="section-note">先易后难：先看见，再算熟，后对考纲。工具随时穿插。点击卡片看详情。</p>
            <PathMap guide={guide} />

            {guide.stages.map((stage) => {
              const node = byId.get(stage.node);
              if (!node) return null;
              return (
                <div key={stage.id} id={`stage-${stage.id}`} className="stage">
                  <h2>{stage.name}</h2>
                  <p className="claim">{renderInline(stage.claim, `st-claim-${stage.id}`)}</p>
                  {stage.why.map((w, i) => (
                    <p key={i}>{renderInline(w, `st-${stage.id}-${i}`)}</p>
                  ))}
                  <NodeCard node={node} heading={`${stage.name} · ${node.title}`} />
                </div>
              );
            })}
          </section>

          <section id="tools">
            <h2>工具线</h2>
            <p className="claim">{renderInline(guide.toolTrack.claim, "tt-claim")}</p>
            {guide.toolTrack.essay.map((p, i) => (
              <p key={i}>{renderInline(p, `tt-${i}`)}</p>
            ))}
            {guide.graph.tools.map((id) => {
              const node = byId.get(id);
              return node ? <NodeCard key={id} node={node} /> : null;
            })}
            {guide.companions.map((c) => (
              <aside key={c.id} className="companion-card">
                <h3>{c.title}</h3>
                <p>{c.note}</p>
                <code>{c.launch}</code>
              </aside>
            ))}
          </section>

          <section id="books">
            <h2>两本书怎么选</h2>
            {guide.books.essay.map((p, i) => (
              <p key={i}>{renderInline(p, `bk-${i}`)}</p>
            ))}
            <table className="compare">
              <thead>
                <tr>
                  <th>方面</th>
                  <th>Siefken（先看见）</th>
                  <th>Selinger（再算熟）</th>
                </tr>
              </thead>
              <tbody>
                {guide.books.compare.map((row) => (
                  <tr key={row.aspect}>
                    <th>{row.aspect}</th>
                    <td>{row.siefken}</td>
                    <td>{row.selinger}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="verdict">
              <p>
                <strong>默认走法：</strong>
                {renderInline(guide.books.default, "bk-default")}
              </p>
              <p>
                <strong>只读一本：</strong>
                {renderInline(guide.books.single, "bk-single")}
              </p>
              <p>
                <strong>被排后的那本：</strong>
                {renderInline(guide.books.backtrack, "bk-back")}
              </p>
            </div>
          </section>

          <section id="gap">
            <h2>高数缺口</h2>
            <p className="claim">{renderInline(guide.gap.claim, "gap-claim")}</p>
            {guide.gap.essay.map((p, i) => (
              <p key={i}>{renderInline(p, `gap-${i}`)}</p>
            ))}
          </section>

          <footer>
            罗盘描述的是各应用在 {guide.updated} 的内容现状；数学应用的内容格局变化时这里随之更新。
            路径推荐是编辑判断，依据写在正文里——按自身情形偏离时，各站的「取舍」写了偏离的代价与回头路。
          </footer>
        </main>
      </div>
    </div>
  );
}
