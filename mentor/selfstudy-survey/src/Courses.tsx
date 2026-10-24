import { useMemo, useState } from "react";
import { allPlans, athenaMap, CATEGORY_LABEL, courses, EXAM_LABEL, majorName, textbooks } from "./data";
import type { Go } from "./nav";
import { Empty, Section } from "./ui";

interface Entry {
  code: string;
  name: string;
  plans: number;
}

export function Courses({ course, go }: { course?: string; go: Go }) {
  const [q, setQ] = useState("");
  const entries = useMemo(() => {
    const m = new Map<string, Entry>();
    for (const { plan } of allPlans) {
      for (const c of plan.courses) {
        const e = m.get(c.code) ?? { code: c.code, name: courses[c.code]?.name ?? c.name, plans: 0 };
        e.plans += 1;
        m.set(c.code, e);
      }
    }
    return [...m.values()].sort((a, b) => b.plans - a.plans || a.code.localeCompare(b.code));
  }, []);
  const shown = entries.filter((e) => !q || e.name.includes(q) || e.code.includes(q));
  const sel = course ?? shown[0]?.code;
  const uses = allPlans.flatMap(({ province, plan }) =>
    plan.courses.filter((c) => c.code === sel).map((c) => ({ province, plan, c })),
  );
  const info = sel ? courses[sel] : undefined;

  if (entries.length === 0) {
    return <Empty>课程库还是空的：课程来自各省入库的计划，等待采集。</Empty>;
  }

  return (
    <div className="split">
      <aside className="picker">
        <input className="search" placeholder="搜索课程名或代码" value={q} onChange={(e) => setQ(e.target.value)} />
        {shown.map((e) => (
          <button key={e.code} className={e.code === sel ? "on" : ""} onClick={() => go({ view: "courses", course: e.code })}>
            {e.name}
            <small>
              {e.code} · {e.plans} 份
            </small>
          </button>
        ))}
      </aside>
      <div className="pane">
        {sel ? (
          <>
            <h2>
              {info?.name ?? uses[0]?.c.name} <small>{sel}</small>
            </h2>
            {athenaMap[sel]?.length ? (
              <p className="lead">Athena 里相关的课程：{athenaMap[sel].join("、")}</p>
            ) : null}
            {info?.note ? <p>{info.note}</p> : null}
            <Section title="出现在哪些计划" hint={`共 ${uses.length} 份`}>
              <div className="scroll">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>省份</th>
                      <th>专业</th>
                      <th>主考院校</th>
                      <th>学分</th>
                      <th>类别</th>
                      <th>命题</th>
                      <th>实践考核</th>
                      <th>教材</th>
                    </tr>
                  </thead>
                  <tbody>
                    {uses.map(({ province, plan, c }) => {
                      const tb = c.textbook ? textbooks[c.textbook] : undefined;
                      return (
                        <tr key={plan.id}>
                          <td>{province.name}</td>
                          <td>
                            <button className="link" onClick={() => go({ view: "majors", major: plan.major, province: province.id })}>
                              {majorName(plan.major)}
                            </button>
                          </td>
                          <td>{plan.hosts.join("、")}</td>
                          <td>{c.credits}</td>
                          <td>{CATEGORY_LABEL[c.category]}</td>
                          <td>{c.exam ? EXAM_LABEL[c.exam] : "—"}</td>
                          <td>{c.practice ? `${c.practice.type}${c.practice.credits ? ` ${c.practice.credits}学分` : ""}` : "—"}</td>
                          <td>{tb ? `${tb.title}（${tb.edition}）` : "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Section>
          </>
        ) : (
          <Empty>没有匹配的课程。</Empty>
        )}
      </div>
    </div>
  );
}
