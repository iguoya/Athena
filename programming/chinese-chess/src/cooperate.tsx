import type { ReactNode } from "react";

export type RosterItem = { name: string; role: string; with: string };

export type FlowFigure = {
  kind: "flow";
  title: string;
  caption: string;
  steps: { name: string; role: string }[];
};

export type SequenceFigure = {
  kind: "sequence";
  title: string;
  caption: string;
  actors: string[];
  messages: { from: number; to: number; label: string }[];
};

export type DependencyFigure = {
  kind: "dependency";
  title: string;
  caption: string;
  layers: { name: string; role: string }[][];
  links: { from: string; to: string; label: string; style: "call" | "signal" }[];
};

export type Figure = FlowFigure | SequenceFigure | DependencyFigure;

export type Cooperation = {
  intro: string;
  roster: RosterItem[];
  figures: Figure[];
};

function FlowChart({ figure }: { figure: FlowFigure }) {
  const nodes: ReactNode[] = [];
  figure.steps.forEach((step, index) => {
    if (index > 0) {
      nodes.push(<i key={`join-${step.name}`} className="join" aria-hidden="true" />);
    }
    nodes.push(
      <div key={step.name} className="step">
        <strong>{step.name}</strong>
        <span>{step.role}</span>
      </div>,
    );
  });
  return <div className="flow">{nodes}</div>;
}

function SequenceChart({ figure }: { figure: SequenceFigure }) {
  return (
    <div
      className="seq"
      style={{ gridTemplateColumns: `repeat(${figure.actors.length}, minmax(0, 1fr))` }}
    >
      {figure.actors.map((actor) => (
        <div key={actor} className="actor">
          {actor}
        </div>
      ))}
      {figure.messages.map((message, index) => {
        const left = Math.min(message.from, message.to);
        const span = Math.abs(message.to - message.from) + 1;
        const direction =
          message.from === message.to ? "self" : message.from < message.to ? "forward" : "back";
        return (
          <div
            key={`${message.label}-${index}`}
            className={`msg ${direction}`}
            style={{ gridColumn: `${left + 1} / span ${span}` }}
          >
            <span>{message.label}</span>
          </div>
        );
      })}
    </div>
  );
}

function DependencyChart({ figure }: { figure: DependencyFigure }) {
  return (
    <>
      <div className="layers">
        {figure.layers.map((layer) => (
          <div key={layer.map((item) => item.name).join("-")} className="layer">
            {layer.map((item) => (
              <article key={item.name}>
                <h4>{item.name}</h4>
                <p>{item.role}</p>
              </article>
            ))}
          </div>
        ))}
      </div>
      <div className="deps">
        {figure.links.map((link) => (
          <div key={`${link.from}-${link.style}-${link.to}-${link.label}`} className="dep">
            <b>{link.from}</b>
            <i className={link.style} aria-hidden="true" />
            <b>{link.to}</b>
            <span>
              {link.style === "signal" ? "信号" : "调用"} · {link.label}
            </span>
          </div>
        ))}
      </div>
    </>
  );
}

function Chart({ figure }: { figure: Figure }) {
  if (figure.kind === "flow") return <FlowChart figure={figure} />;
  if (figure.kind === "sequence") return <SequenceChart figure={figure} />;
  return <DependencyChart figure={figure} />;
}

export function Cooperate({ data }: { data: Cooperation }) {
  return (
    <section className="panel cooperate">
      <h3>代码怎样组织</h3>
      <p>{data.intro}</p>
      <div className="crc">
        <span className="head">名字</span>
        <span className="head">职责</span>
        <span className="head">协作者</span>
        {data.roster.map((item) => (
          <div key={item.name}>
            <strong>{item.name}</strong>
            <span>{item.role}</span>
            <span>{item.with}</span>
          </div>
        ))}
      </div>
      {data.figures.map((figure) => (
        <figure key={figure.title} className="diagram">
          <figcaption>{figure.title}</figcaption>
          <Chart figure={figure} />
          <p>{figure.caption}</p>
        </figure>
      ))}
    </section>
  );
}
