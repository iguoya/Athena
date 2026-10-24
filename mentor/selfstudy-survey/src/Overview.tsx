import { useState } from "react";
import { cellStatus, coverage, offeringsOf, provinces, scope, STATUS_LABEL } from "./data";
import type { Go } from "./nav";
import { Section } from "./ui";
import type { OfferStatus } from "./types";

const LEGEND: OfferStatus[] = ["open", "upcoming", "stopped", "none", "pending"];
const SYMBOL: Record<OfferStatus, string> = { open: "●", upcoming: "◐", stopped: "▼", none: "—", pending: "·" };

export function Overview({ go }: { go: Go }) {
  const [cls, setCls] = useState<string>("all");
  const cov = coverage();
  const [onlyOpen, setOnlyOpen] = useState(true);
  // 目录里有 50 个专业，绝大多数自考根本没开：默认只列「至少一个省有开考/停考/新计划记录」的专业，免得矩阵全是点。
  const hasRecord = (code: string) =>
    provinces.some((p) => offeringsOf(p, code).some((o) => o.status === "open" || o.status === "upcoming" || o.status === "stopped"));
  const majors = scope.majors.filter((m) => (cls === "all" || m.class === cls) && (!onlyOpen || hasRecord(m.code)));

  return (
    <>
      <div className="stats">
        <div>
          <b>{provinces.length}</b>
          <span>个省级行政区</span>
        </div>
        <div>
          <b>{scope.majors.length}</b>
          <span>个调查专业</span>
        </div>
        <div>
          <b>
            {cov.known}/{cov.total}
          </b>
          <span>格已有结论（其中官方来源 {cov.official}）</span>
        </div>
        <div>
          <b>{cov.plans}</b>
          <span>份课程计划已入库</span>
        </div>
      </div>

      <Section title="省 × 专业开设矩阵" hint="点格子进入该专业的跨省对比；待查不是「没有」，是还没核对">
        <div className="filters">
          <button className={cls === "all" ? "on" : ""} onClick={() => setCls("all")}>
            全部
          </button>
          {scope.classes.map((c) => (
            <button key={c.code} className={cls === c.code ? "on" : ""} onClick={() => setCls(c.code)}>
              {c.name}
              {c.tier === "edge" ? "（对照）" : ""}
            </button>
          ))}
          <label className="toggle">
            <input type="checkbox" checked={onlyOpen} onChange={(e) => setOnlyOpen(e.target.checked)} />
            只看有开考记录的专业（{scope.majors.filter((m) => hasRecord(m.code)).length}/{scope.majors.length}）
          </label>
          <span className="legend">
            {LEGEND.map((s) => (
              <span key={s} className={`chip chip-${s}`}>
                {STATUS_LABEL[s]}
              </span>
            ))}
          </span>
        </div>
        <div className="scroll">
          <table className="matrix">
            <thead>
              <tr>
                <th className="stick">省份</th>
                {majors.map((m) => (
                  <th key={m.code} title={`${m.name}（${m.code}）`}>
                    <button className="link" onClick={() => go({ view: "majors", major: m.code })}>
                      {m.name}
                    </button>
                    <small>{m.code}</small>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {provinces.map((p) => (
                <tr key={p.id}>
                  <th className="stick">
                    <button className="link" onClick={() => go({ view: "provinces", province: p.id })}>
                      {p.name.replace(/(省|市|壮族自治区|回族自治区|维吾尔自治区|自治区)$/, "")}
                    </button>
                  </th>
                  {majors.map((m) => {
                    const s = cellStatus(p, m.code);
                    const n = offeringsOf(p, m.code).length;
                    return (
                      <td key={m.code}>
                        <button
                          className={`cell chip-${s}`}
                          title={`${p.name} · ${m.name}：${STATUS_LABEL[s]}`}
                          onClick={() => go({ view: "majors", major: m.code, province: p.id })}
                        >
                          {n > 1 ? n : SYMBOL[s]}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </>
  );
}
