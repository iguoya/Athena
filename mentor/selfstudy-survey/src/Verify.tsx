import { pending, provinces } from "./data";
import type { Go } from "./nav";
import type { PendingItem } from "./types";
import { Empty, Link, Section } from "./ui";

const PRIORITY_LABEL: Record<string, string> = { high: "高", medium: "中", low: "低" };
const provName = (pid: string) => provinces.find((p) => p.id === pid)?.name ?? pid;

// 把文本里的 http(s) 链接拆成可点的（核实建议里多为裸 URL）。
function withLinks(text: string) {
  const parts = text.split(/(https?:\/\/[^\s，。；)」】]+)/g);
  return parts.map((p, i) =>
    /^https?:\/\//.test(p) ? <Link key={i} url={p}>{p}</Link> : p,
  );
}

function ItemCard({ item, go }: { item: PendingItem; go: Go }) {
  const provs = item.provinces ?? (item.province ? [item.province] : []);
  return (
    <li className="plain">
      <p>
        {item.priority ? <span className="chip">优先级 {PRIORITY_LABEL[item.priority]}</span> : null}{" "}
        <b>{item.title}</b>
      </p>
      {provs.length > 0 && (
        <p className="muted">
          省份：
          {provs.map((pid, i) => (
            <span key={pid}>
              {i > 0 ? "、" : ""}
              <button className="link" onClick={() => go({ view: "provinces", province: pid })}>
                {provName(pid)}
              </button>
            </span>
          ))}
        </p>
      )}
      {item.scope ? (
        <p className="muted">
          涉及：<code>{item.scope}</code>
        </p>
      ) : null}
      {item.detail ? <p>{withLinks(item.detail)}</p> : null}
      {item.tried ? (
        <p>
          <b>已尝试：</b>
          {withLinks(item.tried)}
        </p>
      ) : null}
      {item.howto ? (
        <p>
          <b>建议查法：</b>
          {withLinks(item.howto)}
        </p>
      ) : null}
    </li>
  );
}

export function Verify({ go }: { go: Go }) {
  const human = pending.items.filter((i) => i.group === "human");
  const todo = pending.items.filter((i) => i.group !== "human");
  const groupOf = (id: string) => pending.groups.find((g) => g.id === id);
  return (
    <>
      <Section
        title="这份清单是干什么的"
        hint={`整理于 ${pending.updated} 的核实轮`}
      >
        <ul className="plain">
          <li>
            已入库的每条数据都带官方来源与核对日期；这一页列的是<b>反过来的事</b>：
            代理用程序渠道查不到、或还没有取证的信息。每项写明缺什么、试过哪些渠道、建议去哪里查。
          </li>
          <li>
            核实后请把结论与证据（网址、PDF、截图）发给协作舱 zcode（comms/selfstudy-survey）或直接在对话里转告，
            由采集方回写数据并注明来源与核对日期。
          </li>
          <li>
            采集按波次推进：基线 → 开设矩阵 → 课程计划 → 教材；「采集排期中」一节不是查不到，
            是还没轮到，列出只为如实展示缺口。
          </li>
        </ul>
      </Section>
      <Section
        title={groupOf("human")?.label ?? "需要人工核实"}
        hint={groupOf("human")?.desc}
      >
        {human.length === 0 ? (
          <Empty>当前没有需要人工核实的项。</Empty>
        ) : (
          <ul className="plain">
            {human.map((item) => (
              <ItemCard key={item.id} item={item} go={go} />
            ))}
          </ul>
        )}
      </Section>
      <Section
        title={groupOf("todo")?.label ?? "采集排期中"}
        hint={groupOf("todo")?.desc}
      >
        {todo.length === 0 ? (
          <Empty>当前没有排期中的采集项。</Empty>
        ) : (
          <ul className="plain">
            {todo.map((item) => (
              <ItemCard key={item.id} item={item} go={go} />
            ))}
          </ul>
        )}
      </Section>
    </>
  );
}
