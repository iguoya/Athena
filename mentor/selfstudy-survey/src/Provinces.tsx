import { cellStatus, EXCLUDED_MAJORS, majorName, provinces, shownMajors } from "./data";
import type { Go } from "./nav";
import type { Province, TextItem } from "./types";
import { Empty, Link, Section, StatusChip, VerifyBadge } from "./ui";

function known(p: Province) {
  return shownMajors.filter((m) => cellStatus(p, m.code) !== "pending").length;
}

const POLICY_LABEL: [keyof Province["policy"], string][] = [
  ["entry", "报考条件"],
  ["graduate", "毕业要求"],
  ["degree", "学位政策"],
  ["exemption", "免考与互认"],
];

function PolicyRow({ label, item, go }: { label: string; item: TextItem | null; go: Go }) {
  return (
    <tr>
      <th>{label}</th>
      <td>
        {item ? (
          item.text
        ) : (
          <span className="muted">
            ? 未取得——
            <button className="link" onClick={() => go({ view: "verify" })}>
              见待人工核实
            </button>
          </span>
        )}
      </td>
      <td>{item ? <VerifyBadge v={item.verify} /> : "?"}</td>
    </tr>
  );
}

export function Provinces({ province, go }: { province?: string; go: Go }) {
  const p = provinces.find((x) => x.id === province) ?? provinces[0];
  // 省份视图的开考专业表：不列「所有省都没开、只有个别省开」的专业的「不开设」「待查」行（使用者 2026-11-03 裁决），
  // 这类专业若在本省真有开考记录（open/upcoming/stopped）仍照列。
  const shownCodes = new Set(shownMajors.map((m) => m.code));
  const rows = p.offerings.filter((o) => !EXCLUDED_MAJORS.includes(o.major) && (shownCodes.has(o.major) || (o.status !== "none" && o.status !== "pending")));
  return (
    <div className="split">
      <aside className="picker">
        {provinces.map((x) => (
          <button key={x.id} className={x.id === p.id ? "on" : ""} onClick={() => go({ view: "provinces", province: x.id })}>
            {x.name.replace(/(省|市|壮族自治区|回族自治区|维吾尔自治区|自治区)$/, "")}
            <small>
              {known(x)}/{shownMajors.length}
            </small>
          </button>
        ))}
      </aside>
      <div className="pane">
        <h2>{p.name}</h2>

        <Section title="主管机构">
          {p.authority.name ? (
            <p>
              {p.authority.name}
              {p.authority.url ? (
                <>
                  {" "}
                  <Link url={p.authority.url}>自考入口</Link>
                </>
              ) : null}{" "}
              <VerifyBadge v={p.authority.verify} />
            </p>
          ) : (
            <Empty>主管机构与入口待采集。</Empty>
          )}
        </Section>

        <Section title="考期（2025–2026）">
          {p.calendar.length === 0 ? (
            <Empty>考期与报名时间待采集。</Empty>
          ) : (
            <table className="tbl">
              <thead>
                <tr>
                  <th>考期</th>
                  <th>考试日期</th>
                  <th>报名</th>
                  <th>核对</th>
                </tr>
              </thead>
              <tbody>
                {p.calendar.map((c) => (
                  <tr key={c.session}>
                    <td>{c.session}</td>
                    <td>{c.exam ?? "—"}</td>
                    <td>{c.register ?? "—"}</td>
                    <td>
                      <VerifyBadge v={c.verify} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Section>

        <Section title="报考、毕业与学位政策">
          <table className="tbl kv">
            <tbody>
              {POLICY_LABEL.map(([k, label]) => (
                <PolicyRow key={k} label={label} item={p.policy[k]} go={go} />
              ))}
            </tbody>
          </table>
        </Section>

        <Section title="开考专业" hint="没有记录的专业见总览矩阵，显示为待查">
          {rows.length === 0 ? (
            <Empty>这个省的开设信息还没有采集。</Empty>
          ) : (
            <table className="tbl">
              <thead>
                <tr>
                  <th>专业</th>
                  <th>状态</th>
                  <th>方向</th>
                  <th>主考院校</th>
                  <th>计划</th>
                  <th>核对</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((o, i) => (
                  <tr key={i}>
                    <td>
                      <button className="link" onClick={() => go({ view: "majors", major: o.major, province: p.id })}>
                        {majorName(o.major)}
                      </button>
                      <small>{o.local_code ?? o.major}</small>
                    </td>
                    <td>
                      <StatusChip s={o.status} />
                    </td>
                    <td>{o.track ?? "—"}</td>
                    <td>{o.hosts.join("、") || "—"}</td>
                    <td>{o.plans?.length ?? 0} 份</td>
                    <td>
                      <VerifyBadge v={o.verify} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Section>

        {p.events.length > 0 && (
          <Section title="变动">
            <ul className="plain">
              {p.events.map((e, i) => (
                <li key={i}>
                  <b>{e.date}</b> {e.major ? `${majorName(e.major)}：` : ""}
                  {e.text} <VerifyBadge v={e.verify} />
                </li>
              ))}
            </ul>
          </Section>
        )}
      </div>
    </div>
  );
}
