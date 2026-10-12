import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Check, Compass, Lock, Sparkles } from "lucide-react";
import { grammarChapter, grammarUnits, sentencesForUnit, sources } from "@/content";
import type { GrammarUnit, Segment, SegmentRole, Sentence } from "@/content/types";
import { demoMySentences, unitStates, type UnitState } from "@/data/demo";
import { cn } from "@/lib/utils";

const ROLE_STYLE: Record<SegmentRole, string> = {
  main: "text-accent",
  clause: "text-accent-2",
  phrase: "underline decoration-word/60 decoration-2 underline-offset-[5px]",
  plain: "",
};

const STATE_LABEL: Record<UnitState, string> = {
  lit: "已点亮",
  learning: "学习中",
  locked: "未解锁",
};

/** Soft path layout for 10 units: two columns that zigzag like a journey. */
const NODE_SLOT: { col: number; row: number }[] = [
  { col: 1, row: 1 },
  { col: 2, row: 1 },
  { col: 2, row: 2 },
  { col: 1, row: 2 },
  { col: 1, row: 3 },
  { col: 2, row: 3 },
  { col: 2, row: 4 },
  { col: 1, row: 4 },
  { col: 1, row: 5 },
  { col: 2, row: 5 },
];

function unitState(id: string): UnitState {
  return unitStates[id] ?? "locked";
}

export function MapPage() {
  const [activeId, setActiveId] = useState<string | null>(
    () => grammarUnits.find((u) => unitState(u.id) !== "locked")?.id ?? grammarUnits[0]?.id ?? null,
  );
  const lit = grammarUnits.filter((u) => unitState(u.id) === "lit").length;
  const learning = grammarUnits.filter((u) => unitState(u.id) === "learning").length;
  const active = grammarUnits.find((u) => u.id === activeId) ?? null;
  const progress = lit / Math.max(grammarUnits.length, 1);

  return (
    <div className="mx-auto grid max-w-6xl grid-cols-12 gap-5">
      <header className="col-span-12 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="mb-1 text-xs tracking-widest text-muted">第一章 · {grammarChapter.title}</p>
          <h1 className="font-display text-4xl font-semibold text-balance">
            {grammarChapter.subtitle}
            <span className="text-accent">.</span>
          </h1>
          <p className="mt-2 max-w-2xl text-muted">{grammarChapter.blurb}</p>
        </div>
        <div className="flex items-center gap-4 rounded-skin border border-line bg-surface-strong px-4 py-3 shadow-skin">
          <ProgressRing value={progress} />
          <div className="text-sm">
            <p className="font-display text-2xl font-semibold tabular-nums leading-none">
              {lit}
              <span className="ml-1 font-body text-sm text-muted">/ {grammarUnits.length}</span>
            </p>
            <p className="mt-1 text-muted">
              已点亮 · {learning > 0 ? `${learning} 个学习中` : "点亮整张地图是大里程碑"}
            </p>
          </div>
        </div>
      </header>

      <section className="col-span-12 flex flex-wrap items-center gap-3 rounded-skin border border-dashed border-line bg-surface/70 px-4 py-3 text-sm text-muted">
        <Compass size={18} className="text-accent" />
        <span>
          开章诊断会先摸清你已经会的单元——扎实的直接点亮，只学还没掌握的部分。诊断页在下一里程碑接入。
        </span>
        <span className="ml-auto rounded-full border border-line px-3 py-1 text-xs">诊断 · 即将开放</span>
      </section>

      <section className="relative col-span-12 lg:col-span-7">
        <PathGlow />
        <div
          className="relative grid gap-4"
          style={{ gridTemplateColumns: "1fr 1fr", gridTemplateRows: "repeat(5, minmax(88px, auto))" }}
        >
          {grammarUnits.map((unit, i) => {
            const slot = NODE_SLOT[i] ?? { col: 1, row: i + 1 };
            const state = unitState(unit.id);
            const selected = activeId === unit.id;
            return (
              <motion.button
                key={unit.id}
                type="button"
                onClick={() => setActiveId(unit.id)}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.04 * i, duration: 0.45, ease: "easeOut" }}
                style={{ gridColumn: slot.col, gridRow: slot.row }}
                className={cn(
                  "group relative flex flex-col items-start gap-2 rounded-skin border p-4 text-left shadow-skin transition-transform hover:-translate-y-0.5",
                  state === "lit" && "border-transparent bg-accent text-on-accent",
                  state === "learning" && "border-accent bg-surface-strong text-fg",
                  state === "locked" && "border-line bg-surface text-muted",
                  selected && "ring-2 ring-accent-2 ring-offset-2 ring-offset-bg",
                )}
              >
                <div className="flex w-full items-center justify-between gap-2">
                  <span
                    className={cn(
                      "grid h-8 w-8 place-items-center rounded-full text-sm font-bold tabular-nums",
                      state === "lit" && "bg-on-accent/20",
                      state === "learning" && "bg-accent/15 text-accent",
                      state === "locked" && "bg-bg-2",
                    )}
                  >
                    {unit.order}
                  </span>
                  <StateIcon state={state} />
                </div>
                <span className="font-display text-xl font-semibold leading-tight">{unit.name}</span>
                <span className={cn("text-xs", state === "lit" ? "text-on-accent/80" : "text-muted")}>
                  {STATE_LABEL[state]} · {unit.patterns.length} 个句式
                </span>
                {state === "learning" && (
                  <motion.span
                    aria-hidden
                    className="pointer-events-none absolute inset-0 rounded-skin border-2 border-accent"
                    animate={{ opacity: [0.35, 0.9, 0.35] }}
                    transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
                  />
                )}
              </motion.button>
            );
          })}
        </div>
        <p className="mt-4 text-xs text-muted">单元状态是示例数据；正式进度由诊断和做题结果写入。</p>
      </section>

      <aside className="col-span-12 lg:col-span-5">
        <AnimatePresence mode="wait">
          {active ? (
            <motion.div
              key={active.id}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.28, ease: "easeOut" }}
            >
              <ReviewCard unit={active} state={unitState(active.id)} />
            </motion.div>
          ) : null}
        </AnimatePresence>
      </aside>
    </div>
  );
}

function ProgressRing({ value }: { value: number }) {
  const C = 2 * Math.PI * 28;
  return (
    <svg viewBox="0 0 68 68" className="h-16 w-16 flex-none" aria-hidden>
      <circle cx="34" cy="34" r="28" fill="none" strokeWidth="7" stroke="var(--line)" />
      <motion.circle
        cx="34"
        cy="34"
        r="28"
        fill="none"
        strokeWidth="7"
        stroke="var(--accent)"
        strokeLinecap="round"
        strokeDasharray={C}
        transform="rotate(-90 34 34)"
        initial={{ strokeDashoffset: C }}
        animate={{ strokeDashoffset: C * (1 - value) }}
        transition={{ duration: 1, ease: "easeOut" }}
      />
    </svg>
  );
}

function PathGlow() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-x-8 top-6 bottom-6 -z-10 rounded-[40%] bg-[radial-gradient(ellipse_at_center,var(--accent)_0%,transparent_70%)] opacity-[0.12] [:root[data-style=night]_&]:opacity-25"
    />
  );
}

function StateIcon({ state }: { state: UnitState }) {
  if (state === "lit") return <Sparkles size={16} />;
  if (state === "locked") return <Lock size={14} />;
  return <span className="text-[11px] font-medium text-accent">进行中</span>;
}

function ReviewCard({ unit, state }: { unit: GrammarUnit; state: UnitState }) {
  const sentences = useMemo(() => sentencesForUnit(unit.id).slice(0, 3), [unit.id]);
  const mine = demoMySentences[unit.id];

  return (
    <div className="glass sticky top-14 flex flex-col gap-4 p-5 [:root[data-style=journal]_&]:rotate-[var(--tilt)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs tracking-widest text-muted">回顾卡</p>
          <h2 className="font-display text-3xl font-semibold">{unit.name}</h2>
          <p className="mt-1 text-sm text-muted">{unit.blurb}</p>
        </div>
        <span
          className={cn(
            "rounded-full px-2.5 py-1 text-xs",
            state === "lit" && "bg-accent text-on-accent",
            state === "learning" && "border border-accent text-accent",
            state === "locked" && "border border-line text-muted",
          )}
        >
          {STATE_LABEL[state]}
        </span>
      </div>

      <div>
        <p className="mb-2 text-xs tracking-widest text-muted">这个单元的句式</p>
        <div className="flex flex-wrap gap-1.5">
          {unit.patterns.map((p) => (
            <span key={p.id} className="rounded-full border border-line bg-bg-2 px-2.5 py-0.5 text-xs text-muted">
              {p.name}
            </span>
          ))}
        </div>
      </div>

      {state === "locked" ? (
        <LockedHint />
      ) : (
        <>
          <div>
            <p className="mb-2 text-xs tracking-widest text-muted">你已掌握的真实句子</p>
            {sentences.length === 0 ? (
              <p className="rounded-2xl border border-dashed border-line bg-bg-2/50 px-3 py-4 text-sm text-muted">
                {state === "lit"
                  ? "诊断已点亮这个单元。学完对应句组后，这里会出现你掌握的 2–3 条真实句子。"
                  : "学完这个单元的句组后，回顾卡会收进你掌握的真实句子。"}
              </p>
            ) : (
              <ul className="grid gap-3">
                {sentences.map((s) => (
                  <li key={s.id}>
                    <MasteredSentence sentence={s} />
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <p className="mb-2 text-xs tracking-widest text-muted">你自己写对的一句</p>
            {mine ? (
              <p className="en rounded-2xl border border-line bg-surface-strong px-3 py-3 font-sentence text-lg leading-snug">
                {mine}
              </p>
            ) : (
              <p className="rounded-2xl border border-dashed border-line bg-bg-2/50 px-3 py-4 text-sm text-muted">
                仿写写对之后，你的句子会出现在这里——不写大段规则，只留你会的句子。
              </p>
            )}
            {mine ? <p className="mt-1 text-[11px] text-muted">示例句子，写作页接通后换成你的真实仿写。</p> : null}
          </div>
        </>
      )}

      {state === "lit" && (
        <p className="flex items-center gap-1.5 text-sm text-accent">
          <Check size={16} strokeWidth={3} />
          这张回顾卡已点亮
        </p>
      )}
    </div>
  );
}

function LockedHint() {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-line bg-bg-2/60 px-3 py-4 text-sm text-muted">
      <Lock size={16} className="mt-0.5 flex-none" />
      <p>
        还没解锁。开章诊断如果发现你已经扎实，会直接点亮；否则学完这个单元的句组后，回顾卡会出现在这里。
      </p>
    </div>
  );
}

function MasteredSentence({ sentence }: { sentence: Sentence }) {
  const source = sources[sentence.source];
  return (
    <figure className="rounded-2xl border border-line bg-surface-strong px-3 py-3">
      <p className="en font-sentence text-[17px] leading-snug text-pretty">
        {sentence.segments.map((seg, i) => (
          <Seg key={`${sentence.id}-${i}`} seg={seg} />
        ))}
      </p>
      <figcaption className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-muted">
        <span className="rounded-full border border-line px-2 py-0.5">{sentence.grammarNote}</span>
        {source ? (
          <span>
            出处：{source.title}
            {source.year ? `，${source.year}` : ""}
          </span>
        ) : null}
      </figcaption>
    </figure>
  );
}

function Seg({ seg }: { seg: Segment }) {
  return <span className={ROLE_STYLE[seg.role]}>{seg.text}</span>;
}
