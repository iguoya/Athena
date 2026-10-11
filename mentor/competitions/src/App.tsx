import { useMemo, useState } from "react";
import { openUrl } from "@tauri-apps/plugin-opener";
import { cn } from "@/lib/utils";
import data from "../content/competitions.json";

type Allow = "yes" | "no" | "per-event" | "pending";
type Level = "official" | "notice" | "report" | "pending";
type Who = "all" | "students" | "public";

interface Competition {
  id: string;
  name: string;
  direction: string;
  organizer: string | null;
  students: Allow;
  public: Allow;
  note: string;
  window: string | null;
  url: string | null;
  courses: string[];
  verify: { level: Level; source: string | null; date: string | null };
}

const directions: { id: string; title: string }[] = data.directions;
const competitions = data.competitions as Competition[];

const ALLOW_TEXT: Record<Allow, string> = {
  yes: "可参加",
  no: "不可参加",
  "per-event": "以单场规则为准",
  pending: "待核对",
};

const ALLOW_STYLE: Record<Allow, string> = {
  yes: "bg-yes-bg text-yes",
  no: "bg-no-bg text-no",
  "per-event": "bg-per-bg text-per",
  pending: "bg-pending-bg text-pending",
};

const LEVEL_TEXT: Record<Level, string> = {
  official: "官方章程",
  notice: "往届/院校通知",
  report: "第三方报道",
  pending: "未核对",
};

const WHO_OPTIONS: { id: Who; label: string }[] = [
  { id: "all", label: "全部" },
  { id: "students", label: "在校生可参" },
  { id: "public", label: "社会人士可参" },
];

// 赛事规则一年一变：核对超过一年就提示重新核对，而不是静默沿用（ADR 0114）。
const STALE_DAYS = 365;

function isStale(date: string | null): boolean {
  if (!date) return false;
  const age = (Date.now() - new Date(date).getTime()) / 86_400_000;
  return age > STALE_DAYS;
}

// 在 Tauri 里交给系统浏览器；在普通浏览器预览时退回新标签页。
function open(url: string) {
  if ("__TAURI_INTERNALS__" in window) {
    void openUrl(url);
  } else {
    window.open(url, "_blank", "noopener");
  }
}

// 「可参」只认 yes 与 per-event：待核对的不算，免得把没查过的当成能报名。
function matches(c: Competition, who: Who, direction: string): boolean {
  if (direction !== "all" && c.direction !== direction) return false;
  if (who === "students") return c.students === "yes" || c.students === "per-event";
  if (who === "public") return c.public === "yes" || c.public === "per-event";
  return true;
}

function Badge({ label, value }: { label: string; value: Allow }) {
  return (
    <span className="inline-flex overflow-hidden rounded-lg text-xs">
      <span className="bg-no-bg px-[7px] py-[3px] text-muted">{label}</span>
      <span className={cn("px-2 py-[3px] font-semibold", ALLOW_STYLE[value])}>
        {ALLOW_TEXT[value]}
      </span>
    </span>
  );
}

const linkButton =
  "cursor-pointer rounded-lg border border-line bg-transparent px-2.5 py-1 text-xs text-ink";

function Card({ c }: { c: Competition }) {
  const v = c.verify;
  const dir = directions.find((d) => d.id === c.direction);
  return (
    <article className="flex flex-col gap-2.5 rounded-[14px] border border-line bg-surface px-[18px] py-4">
      <div className="flex items-start justify-between gap-2.5">
        <h2 className="m-0 text-base leading-snug">{c.name}</h2>
        {dir && (
          <span className="flex-none rounded-full border border-current px-2 py-0.5 text-xs text-accent">
            {dir.title}
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <Badge label="在校生" value={c.students} />
        <Badge label="社会人士" value={c.public} />
      </div>

      <p className="m-0 text-[13px] leading-relaxed">{c.note}</p>

      {(c.organizer || c.window) && (
        <dl className="m-0 grid grid-cols-[auto_1fr] gap-x-2.5 gap-y-0.5 text-[13px]">
          {c.organizer && (
            <>
              <dt className="text-muted">主办</dt>
              <dd className="m-0">{c.organizer}</dd>
            </>
          )}
          {c.window && (
            <>
              <dt className="text-muted">时间</dt>
              <dd className="m-0">{c.window}</dd>
            </>
          )}
        </dl>
      )}

      {c.courses.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-muted">对应课程</span>
          {c.courses.map((name) => (
            <span key={name} className="rounded-md bg-no-bg px-2 py-0.5">
              {name}
            </span>
          ))}
        </div>
      )}

      <footer className="mt-auto flex items-center justify-between gap-2.5 border-t border-line pt-2 text-xs text-muted">
        <span className={cn(v.level === "pending" && "text-pending")}>
          {v.date ? `${LEVEL_TEXT[v.level]} · 核对于 ${v.date}` : LEVEL_TEXT[v.level]}
          {isStale(v.date) && (
            <span className="ml-1.5 rounded-md bg-pending-bg px-1.5 py-px text-pending">
              可能过期
            </span>
          )}
        </span>
        <span className="flex gap-1.5">
          {v.source && (
            <button className={linkButton} onClick={() => open(v.source!)}>
              来源
            </button>
          )}
          {c.url && (
            <button
              className={cn(linkButton, "border-accent text-accent")}
              onClick={() => open(c.url!)}
            >
              官网
            </button>
          )}
        </span>
      </footer>
    </article>
  );
}

export default function App() {
  const [who, setWho] = useState<Who>("all");
  const [direction, setDirection] = useState("all");

  const shown = useMemo(
    () => competitions.filter((c) => matches(c, who, direction)),
    [who, direction],
  );
  const pending = shown.filter((c) => c.verify.level === "pending").length;

  return (
    <>
      <header className="sticky top-0 z-10 flex flex-wrap items-end justify-between gap-4 border-b border-line bg-page px-4 pb-4 pt-5 sm:px-7">
        <div>
          <h1 className="m-0 text-[26px]">赛历</h1>
          <p className="mb-0 mt-1 text-sm text-muted">
            谁能参加、和哪门课对得上。参赛资格每年调整，报名前以当届章程为准。
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div
            className="inline-flex overflow-hidden rounded-[10px] border border-line bg-surface"
            role="group"
            aria-label="参赛身份"
          >
            {WHO_OPTIONS.map((o, i) => (
              <button
                key={o.id}
                onClick={() => setWho(o.id)}
                className={cn(
                  "cursor-pointer border-0 bg-transparent px-3.5 py-[7px] text-sm text-ink",
                  i > 0 && "border-l border-line",
                  who === o.id && "bg-accent text-white",
                )}
              >
                {o.label}
              </button>
            ))}
          </div>
          <select
            aria-label="方向"
            value={direction}
            onChange={(e) => setDirection(e.target.value)}
            className="rounded-[10px] border border-line bg-surface px-2.5 py-[7px] text-sm text-ink"
          >
            <option value="all">全部方向</option>
            {directions.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title}
              </option>
            ))}
          </select>
        </div>
      </header>
      <main className="px-4 pb-10 pt-4 sm:px-7">
        <p className="mb-3 mt-0 text-[13px] text-muted">
          {`${shown.length} 项`}
          {pending ? `，其中 ${pending} 项资格待核对` : ""}
        </p>
        <section className="grid grid-cols-1 gap-4 sm:grid-cols-[repeat(auto-fill,minmax(340px,1fr))]">
          {shown.map((c) => (
            <Card key={c.id} c={c} />
          ))}
        </section>
      </main>
    </>
  );
}
