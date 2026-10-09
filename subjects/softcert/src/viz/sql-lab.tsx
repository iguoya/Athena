import { useState } from "react";
import { runSqlLab, recordAttempt } from "../db";
import { VizShell } from "./common";

type SqlLabParams = {
  /** 实验编号,进 progress 库的 question_id(softcert ADR 0002:通过即作答)。 */
  id: string;
  title: string;
  setup: string[];
  schemaHint?: string;
  task: string;
  answer: string;
  hint?: string;
  course: string;
  chapterId: string;
  kpId: string;
};

type Outcome = { columns: string[]; rows: string[][]; passed: boolean; detail: string };

/** SQL 真跑实验:内存库执行 setup,学习者写查询,结果集与参考查询比对(ADR 0091)。 */
export function SqlLab({ params }: { params: Record<string, unknown> }) {
  const p = params as unknown as SqlLabParams;
  const [sql, setSql] = useState("");
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const result = await runSqlLab(p.setup, sql, p.answer);
      if (!result) {
        setError("纯浏览器开发模式没有 SQL 引擎,请在应用里运行这个实验。");
        setOutcome(null);
        return;
      }
      setOutcome(result);
      if (result.passed) {
        await recordAttempt({
          course: p.course,
          chapterId: p.chapterId,
          kpId: p.kpId,
          questionId: p.id,
          correct: true,
          mode: "chapter",
        });
      }
    } catch (e) {
      setOutcome(null);
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <VizShell title={p.title}>
      <div className="grid gap-3">
        {p.schemaHint && (
          <p className="font-mono text-xs text-slate-500">表结构:{p.schemaHint}</p>
        )}
        <p className="text-sm leading-relaxed">{p.task}</p>
        <textarea
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          spellCheck={false}
          rows={4}
          placeholder="在这里写 SQL…"
          className="w-full rounded-xl border border-slate-200 bg-white p-3 font-mono text-sm shadow-inner focus:border-brand-400 focus:outline-none"
        />
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={run}
            disabled={busy || !sql.trim()}
            className="rounded-full bg-brand-600 px-5 py-2 text-sm font-medium text-white shadow transition hover:bg-brand-700 disabled:opacity-40"
          >
            {busy ? "运行中…" : "运行并检查"}
          </button>
          {outcome?.passed && (
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
              ✓ {outcome.detail}
            </span>
          )}
          {outcome && !outcome.passed && (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-700">
              {outcome.detail}
            </span>
          )}
        </div>
        {error && (
          <p className="rounded-xl bg-rose-50 p-3 font-mono text-xs text-rose-600">{error}</p>
        )}
        {outcome && outcome.rows.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 font-mono text-slate-600">
                <tr>
                  {outcome.columns.map((c) => (
                    <th key={c} className="px-3 py-1.5 font-medium">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="font-mono">
                {outcome.rows.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    {r.map((v, j) => (
                      <td key={j} className="px-3 py-1.5">
                        {v === "" ? <span className="text-slate-300">(空)</span> : v}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!outcome?.passed && p.hint && (
          <p className="text-xs text-slate-400">提示:{p.hint}</p>
        )}
      </div>
    </VizShell>
  );
}
