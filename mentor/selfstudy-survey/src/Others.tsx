import { useState } from "react";
import {
  allPlans,
  coverage,
  courses,
  CATEGORY_LABEL,
  LEVEL_LABEL,
  majorName,
  provinces,
  scope,
  textbooks,
} from "./data";
import type { Go } from "./nav";
import { Empty, Section, VerifyBadge } from "./ui";

const KIND_LABEL: Record<string, string> = { national: "全国统编", host: "主考院校编", provincial: "省编", other: "其他", unknown: "未标明" };

export function Textbooks({ go }: { go: Go }) {
  const [kind, setKind] = useState("all");
  const entries = Object.entries(textbooks).filter(([, t]) => kind === "all" || (t.kind ?? "unknown") === kind);
  if (Object.keys(textbooks).length === 0) {
    return <Empty>教材库还是空的：教材条目随波 D（教材与大纲）采集入库。</Empty>;
  }
  const usedBy = (id: string) =>
    allPlans.flatMap(({ province, plan }) =>
      plan.courses.filter((c) => c.textbook === id).map((c) => ({ province, plan, c })),
    );
  return (
    <>
      <div className="filters">
        {["all", "national", "host", "provincial", "other", "unknown"].map((k) => (
          <button key={k} className={kind === k ? "on" : ""} onClick={() => setKind(k)}>
            {k === "all" ? "全部" : KIND_LABEL[k]}
          </button>
        ))}
      </div>
      <div className="scroll">
        <table className="tbl">
          <thead>
            <tr>
              <th>教材</th>
              <th>作者</th>
              <th>出版社 · 版次</th>
              <th>类型</th>
              <th>用于</th>
              <th>核对</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([id, t]) => {
              const u = usedBy(id);
              return (
                <tr key={id}>
                  <td>{t.title}</td>
                  <td>{t.authors.join("、")}</td>
                  <td>
                    {t.publisher} · {t.edition}
                  </td>
                  <td>{KIND_LABEL[t.kind ?? "unknown"]}</td>
                  <td>
                    {[...new Set(u.map((x) => x.c.name))].map((n) => (
                      <button
                        key={n}
                        className="link"
                        onClick={() => go({ view: "courses", course: u.find((x) => x.c.name === n)!.c.code })}
                      >
                        {n}{" "}
                      </button>
                    ))}
                  </td>
                  <td>
                    <VerifyBadge v={t.verify} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}

export function Practice({ go }: { go: Go }) {
  const rows = allPlans.flatMap(({ province, plan }) =>
    plan.courses
      .filter((c) => c.practice || c.category === "practice")
      .map((c) => ({ province, plan, c })),
  );
  const grads = allPlans.filter(({ plan }) => plan.graduation);
  return (
    <>
      <Section title="含实践的课程" hint="课程内的实践考核（上机、实验、设计）与独立实践课">
        {rows.length === 0 ? (
          <Empty>还没有入库的计划里带实践信息，等待波 C 采集。</Empty>
        ) : (
          <div className="scroll">
            <table className="tbl">
              <thead>
                <tr>
                  <th>省份</th>
                  <th>专业</th>
                  <th>课程</th>
                  <th>形式</th>
                  <th>说明</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(({ province, plan, c }) => (
                  <tr key={`${plan.id}-${c.code}`}>
                    <td>{province.name}</td>
                    <td>
                      <button className="link" onClick={() => go({ view: "majors", major: plan.major, province: province.id })}>
                        {majorName(plan.major)}
                      </button>
                    </td>
                    <td>
                      {c.name}
                      {c.pair ? "（实践）" : ""}
                      <small>{c.code}</small>
                    </td>
                    <td>{c.practice?.type ?? CATEGORY_LABEL[c.category]}</td>
                    <td>{c.practice?.note ?? c.note ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
      <Section title="毕业环节" hint="毕业设计（论文）、答辩与实践考核">
        {grads.length === 0 ? (
          <Empty>还没有入库的毕业环节信息。</Empty>
        ) : (
          <ul className="plain">
            {grads.map(({ province, plan }) => (
              <li key={plan.id}>
                <b>
                  {province.name} · {majorName(plan.major)} · {plan.hosts.join("、")}
                </b>
                ：{plan.graduation!.thesis ? "有毕业设计（论文）" : "无毕业设计（论文）"}
                {plan.graduation!.credits ? `，${plan.graduation!.credits} 学分` : ""}。{plan.graduation!.note ?? ""}
              </li>
            ))}
          </ul>
        )}
      </Section>
    </>
  );
}

export function Events({ go }: { go: Go }) {
  const events = provinces
    .flatMap((p) => p.events.map((e) => ({ p, e })))
    .sort((a, b) => b.e.date.localeCompare(a.e.date));
  if (events.length === 0) return <Empty>还没有记录到变动（新旧计划切换、停考、课程代码更换）。</Empty>;
  const KIND: Record<string, string> = { "new-plan": "新计划", stop: "停考", "code-change": "代码更换", policy: "政策", other: "其他" };
  return (
    <ul className="timeline">
      {events.map(({ p, e }, i) => (
        <li key={i}>
          <time>{e.date}</time>
          <span className="chip">{KIND[e.kind]}</span>
          <button className="link" onClick={() => go({ view: "provinces", province: p.id })}>
            {p.name}
          </button>
          {e.major ? `·${majorName(e.major)}` : ""}：{e.text} <VerifyBadge v={e.verify} />
        </li>
      ))}
    </ul>
  );
}

export function Method({ go }: { go: Go }) {
  const cov = coverage();
  return (
    <>
      <Section title="怎么核对">
        <ul className="plain">
          <li>
            每条事实数据带来源等级与核对日期。<b>{LEVEL_LABEL.official}</b>：省教育考试院或主考院校的原文；
            <b>{LEVEL_LABEL.notice}</b>：教育部考试中心、考试院主管的官方门户；<b>{LEVEL_LABEL.report}</b>
            ：第三方自考网转载，只作线索，课程表不收；<b>{LEVEL_LABEL.pending}</b>：还没查过。
          </li>
          <li>查不到就标待查，绝不凭印象、邻省或往年推断；矩阵里的「待查」不等于「没有」。</li>
          <li>核对超过一年的数据标「可能过期」。每个考期换计划，数据会过时，以每条自己的核对日期为准。</li>
          <li>通过率、难度官方不公布，本应用不采集、不引用第三方估算。</li>
          <li>范围：自考本科（含专科起点本科）的计算机类（0809）、电子信息类（0807）与对照用的自动化类（0808）；电气类以强电为主，不收。</li>
          <li>本应用只供查阅比较，不替人决定报哪个专业；具体以各省考试院当期公告为准。</li>
        </ul>
      </Section>
      <Section title="覆盖进度" hint={`目录核对日期 ${scope.updated}；已有结论 ${cov.known}/${cov.total} 格，课程计划 ${cov.plans} 份`}>
        <div className="scroll">
          <table className="tbl">
            <thead>
              <tr>
                <th>省份</th>
                <th>考试院</th>
                <th>考期</th>
                <th>开设记录</th>
                <th>课程计划</th>
              </tr>
            </thead>
            <tbody>
              {provinces.map((p) => (
                <tr key={p.id}>
                  <td>
                    <button className="link" onClick={() => go({ view: "provinces", province: p.id })}>
                      {p.name}
                    </button>
                  </td>
                  <td>{p.authority.verify.level === "pending" ? "待查" : LEVEL_LABEL[p.authority.verify.level]}</td>
                  <td>{p.calendar.length}</td>
                  <td>{p.offerings.length}</td>
                  <td>{p.plans.length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
      <p className="fine">课程库 {Object.keys(courses).length} 门、教材库 {Object.keys(textbooks).length} 本已登记。</p>
    </>
  );
}
