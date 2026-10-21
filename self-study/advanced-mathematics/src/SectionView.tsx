import { figures } from "./App";
import { Tex } from "./math";
import { Exercise } from "./Exercise";
import { SourceBadge } from "./ui";
import type {
  Block,
  Curriculum,
  ExerciseBlock,
  KnowledgePoint,
  RetrievalBlock,
  SectionContent,
} from "./types";

function Blocks({
  block,
  onAnswered,
}: {
  block: Block;
  onAnswered: (ids: string[], correct: boolean) => void;
}) {
  switch (block.kind) {
    case "retrieval":
      return <Exercise block={block as RetrievalBlock} onAnswered={onAnswered} retrieval />;
    case "prose":
      return (
        <div className="prose">
          <Tex text={block.text} />
        </div>
      );
    case "example":
      return (
        <details className="example">
          <summary>
            <Tex text={block.title} />
          </summary>
          <div className="example-problem">
            <Tex text={block.problem} />
          </div>
          <p className="hint">先自己动笔算完，再看分步解答。</p>
          <ol className="steps">
            {block.steps.map((s, i) => (
              <li key={i}>
                <Tex text={s.text} />
                {s.why && (
                  <span className="why">
                    为什么：<Tex text={s.why} />
                  </span>
                )}
              </li>
            ))}
          </ol>
          <SourceBadge refs={block.source_refs ?? []} />
        </details>
      );
    case "pitfall":
      return (
        <div className="pitfall">
          <div className="wrong">
            <div className="tag">别按这个来</div>
            <Tex text={block.wrong} />
            <p className="why-wrong">
              <Tex text={block.why_wrong} />
            </p>
          </div>
          <div className="right">
            <div className="tag">该这样</div>
            <Tex text={block.right} />
          </div>
        </div>
      );
    case "figure": {
      const raw = figures[`../content/sections/assets/${block.file}`];
      return (
        <figure className="figure">
          {raw ? (
            <div className="figure-svg" dangerouslySetInnerHTML={{ __html: raw }} />
          ) : (
            <div className="figure-missing">缺图：{block.file}</div>
          )}
          <figcaption>
            <Tex text={block.caption} />
          </figcaption>
        </figure>
      );
    }
    case "exercise":
      return <Exercise block={block as ExerciseBlock} onAnswered={onAnswered} />;
  }
}

export function SectionView({
  content,
  curriculum,
  knowledgeMap,
  onAnswered,
}: {
  content: SectionContent;
  curriculum: Curriculum;
  knowledgeMap: Record<string, KnowledgePoint>;
  onAnswered: (ids: string[], correct: boolean) => void;
}) {
  const meta = curriculum.chapters
    .flatMap((c) => c.sections.map((s) => ({ ...s, chapter: c })))
    .find((s) => s.id === content.id);
  const points = (meta?.knowledge ?? [])
    .map((id) => knowledgeMap[id])
    .filter((k): k is KnowledgePoint => Boolean(k));

  return (
    <article className="section">
      <header>
        <p className="crumb">
          {meta?.chapter.no} {meta?.chapter.title}
        </p>
        <h2>
          {meta?.no} {meta?.title}
        </h2>
        {points.length > 0 && (
          <ul className="knowledge-list">
            {points.map((k) => (
              <li key={k.id} className={`k k-${k.type}`}>
                <strong>{k.title}</strong>
                <span className="k-meta">
                  {k.type} · 难度 {k.difficulty} · {k.target} · 教材 {k.textbook_ref} · 考纲{" "}
                  {k.syllabus_ref}
                </span>
                {k.requires.length > 0 && (
                  <span className="k-req">
                    先修：
                    {k.requires
                      .map((r) => knowledgeMap[r]?.title ?? r)
                      .join("、")}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </header>
      {content.blocks.map((b: Block, i: number) => (
        <Blocks key={i} block={b} onAnswered={onAnswered} />
      ))}
    </article>
  );
}
