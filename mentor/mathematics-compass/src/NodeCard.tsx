// 节点详情卡：一个应用的学习目的、掌握要点、取舍、终点标准。是罗盘的内容主体。
import { useState } from "react";
import type { GuideNode } from "./types";
import renderInline from "./Inline";

export default function NodeCard({ node, heading }: { node: GuideNode; heading?: string }) {
  const [copied, setCopied] = useState(false);
  const cmd = node.launch;

  async function copy() {
    try {
      await navigator.clipboard.writeText(cmd);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // 剪贴板不可用就静默放弃：命令本来就直接写在页面上。
    }
  }

  return (
    <article className="node-card" id={`node-${node.id}`}>
      <header>
        <div>
          <h3>{heading ?? node.title}</h3>
          <p className="node-kind">
            {node.kind} · 出处：{renderInline(node.source, `src-${node.id}`)}
          </p>
        </div>
        <button className="launch" onClick={copy} title="复制启动命令">
          <code>{cmd}</code>
          <span className="copied-hint">{copied ? "已复制" : "复制"}</span>
        </button>
      </header>

      <section>
        <h4>为什么学它</h4>
        <p>{renderInline(node.purpose, `purpose-${node.id}`)}</p>
      </section>

      <section>
        <h4>掌握要点</h4>
        <ul className="points">
          {node.points.map((pt) => (
            <li key={pt.point}>
              <strong>{pt.point}</strong>
              <span>{pt.detail}</span>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h4>取舍</h4>
        <p>{renderInline(node.tradeoff, `tradeoff-${node.id}`)}</p>
      </section>

      <section>
        <h4>怎么算学完</h4>
        <ul className="milestones">
          {node.milestones.map((ms, i) => (
            <li key={i}>{renderInline(ms, `ms-${node.id}-${i}`)}</li>
          ))}
        </ul>
        <p className="time-hint">{node.timeHint}</p>
      </section>
    </article>
  );
}
