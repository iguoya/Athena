import { allPlans, CATEGORY_LABEL, courses, majorName, provinces, scope, STATUS_LABEL } from "./data";
import type { Go } from "./nav";
import type { PlanCourse } from "./types";
import { Empty, Section, StatusChip, VerifyBadge } from "./ui";

const CAT_ORDER = ["public", "required", "basic", "core", "elective", "practice", "graduation"];

interface Row {
  code: string;
  name: string;
  category: string;
  // 该行在哪些计划里出现（计划 id → 课程行）
  by: Map<string, PlanCourse>;
}

export function Majors({ major, province, go }: { major?: string; province?: string; go: Go }) {
  const code = major ?? scope.majors[0].code;
  const plans = allPlans.filter((r) => r.plan.major === code);

  // 课程对比矩阵的行：按课程代码取并集；同一代码在不同计划里类别可能不同，取第一次出现的类别排位。
  const rows = new Map<string, Row>();
  for (const { plan } of plans) {
    for (const c of plan.courses) {
      const label = (courses[c.code]?.name ?? c.name) + (c.category === "practice" && c.pair ? "（实践）" : "");
      const r = rows.get(c.code) ?? { code: c.code, name: label, category: c.category, by: new Map() };
      r.by.set(plan.id, c);
      rows.set(c.code, r);
    }
  }
  const sorted = [...rows.values()].sort(
    (a, b) => CAT_ORDER.indexOf(a.category) - CAT_ORDER.indexOf(b.category) || a.code.localeCompare(b.code),
  );

  const offerings = provinces.flatMap((p) =>
    p.offerings.filter((o) => o.major === code).map((o) => ({ p, o })),
  );
  const count = (s: string) => offerings.filter((x) => x.o.status === s).length;
  const hosts = new Set(offerings.filter((x) => x.o.status === "open").flatMap((x) => x.o.hosts));

  return (
    <div className="split">
      <aside className="picker">
        {scope.classes.map((c) => (
          <div key={c.code}>
            <h4>
              {c.name}
              {c.tier === "edge" ? "（对照）" : ""}
            </h4>
            {scope.majors
              .filter((m) => m.class === c.code)
              .map((m) => (
                <button key={m.code} className={m.code === code ? "on" : ""} onClick={() => go({ view: "majors", major: m.code })}>
                  {m.name}
                  <small>{m.code}</small>
                </button>
              ))}
          </div>
        ))}
      </aside>

      <div className="pane">
        <h2>
          {majorName(code)} <small>{code}</small>
        </h2>
        <p className="lead">
          已记录开设信息 {offerings.length} 条：开考 {count("open")}、新计划 {count("upcoming")}、停考 {count("stopped")}、经核实未开设 {count("none")}；
          已入库课程计划 {plans.length} 份；开考主考院校 {hosts.size} 所。
        </p>

        <Section title="各省开设情况" hint="只列已有记录的省；其余省份见总览矩阵的「待查」">
          {offerings.length === 0 ? (
            <Empty>这个专业还没有任何省份的开设记录，等待采集。</Empty>
          ) : (
            <div className="scroll">
              <table className="tbl">
                <thead>
                  <tr>
                    <th>省份</th>
                    <th>状态</th>
                    <th>方向</th>
                    <th>主考院校</th>
                    <th>核对</th>
                  </tr>
                </thead>
                <tbody>
                  {offerings.map(({ p, o }, i) => (
                    <tr key={i} className={p.id === province ? "hl" : ""}>
                      <td>
                        <button className="link" onClick={() => go({ view: "provinces", province: p.id })}>
                          {p.name}
                        </button>
                      </td>
                      <td>
                        <StatusChip s={o.status} />
                      </td>
                      <td>{o.track ?? "—"}</td>
                      <td>{o.hosts.length ? o.hosts.join("、") : "—"}</td>
                      <td>
                        <VerifyBadge v={o.verify} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        <Section title="课程计划对比" hint="行是课程（按课程代码取并集），列是各省各版计划；格内是学分，✎ 表示含实践考核">
          {plans.length === 0 ? (
            <Empty>
              这个专业还没有入库的课程计划。课程表只收省考试院或主考院校的原文来源，第三方转载不算；
              采集进度见「方法与来源」。
            </Empty>
          ) : (
            <div className="scroll">
              <table className="tbl compare">
                <thead>
                  <tr>
                    <th className="stick">课程</th>
                    {plans.map(({ province: p, plan }) => (
                      <th key={plan.id} className={p.id === province ? "hl" : ""}>
                        {p.name.slice(0, 2)}
                        <small>
                          {plan.host}
                          {plan.track ? `·${plan.track}` : ""}
                          <br />
                          {plan.version}
                        </small>
                      </th>
                    ))}
                    <th>覆盖</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="sum">
                    <td className="stick">总学分 / 门数</td>
                    {plans.map(({ plan }) => (
                      <td key={plan.id}>
                        {plan.total_credits ?? "?"} / {plan.courses.length}
                      </td>
                    ))}
                    <td />
                  </tr>
                  {sorted.map((r) => (
                    <tr key={r.code} className={r.by.size === plans.length && plans.length > 1 ? "all" : ""}>
                      <td className="stick">
                        <button className="link" onClick={() => go({ view: "courses", course: r.code })}>
                          {r.name}
                        </button>
                        <small>
                          {r.code} · {CATEGORY_LABEL[r.category]}
                        </small>
                      </td>
                      {plans.map(({ plan }) => {
                        const c = r.by.get(plan.id);
                        return (
                          <td key={plan.id} className={c ? `cat-${c.category}` : "none"}>
                            {c ? (
                              <>
                                {c.credits}
                                {c.practice || c.category === "practice" ? " ✎" : ""}
                              </>
                            ) : (
                              ""
                            )}
                          </td>
                        );
                      })}
                      <td className="num">
                        {r.by.size}/{plans.length}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        {plans.length > 0 && (
          <Section title="计划出处">
            <ul className="plain">
              {plans.map(({ province: p, plan }) => (
                <li key={plan.id}>
                  {p.name} · {plan.host} · {plan.version}（{plan.state === "current" ? "现行" : plan.state === "upcoming" ? "待生效" : "旧版"}）{" "}
                  <VerifyBadge v={plan.verify} />
                </li>
              ))}
            </ul>
          </Section>
        )}
        <p className="fine">状态图例：{Object.values(STATUS_LABEL).join(" / ")}。</p>
      </div>
    </div>
  );
}
