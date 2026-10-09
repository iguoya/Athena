import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowLeft, ArrowRight, BookmarkCheck, BookmarkPlus, Check, Eye, Languages, Volume2 } from "lucide-react";
import { Celebration } from "@/components/Celebration";
import { sources, todaySet } from "@/content";
import type { Gloss, Segment, SegmentRole, Sentence } from "@/content/types";
import { speak } from "@/lib/speech";
import { useProgress } from "@/store/progress";
import { cn } from "@/lib/utils";

const ROLE_STYLE: Record<SegmentRole, string> = {
  main: "text-accent",
  clause: "text-accent-2",
  phrase: "underline decoration-word/60 decoration-2 underline-offset-[6px]",
  plain: "",
};

const ROLE_LEGEND: { role: SegmentRole; label: string }[] = [
  { role: "main", label: "主干" },
  { role: "clause", label: "从句" },
  { role: "phrase", label: "短语 / 非谓语" },
];

const TOKEN = /([A-Za-z]+(?:['’][A-Za-z]+)*)|([^A-Za-z]+)/g;

type Picked = { seg: number; tok: number; word: string };

function findGloss(sentence: Sentence, word: string): Gloss | undefined {
  const w = word.toLowerCase();
  return sentence.glosses.find((g) => g.words.includes(w));
}

export function Sentences() {
  const set = todaySet();
  const [index, setIndex] = useState(0);
  const [showStructure, setShowStructure] = useState(false);
  const [showCn, setShowCn] = useState(false);
  const [picked, setPicked] = useState<Picked | null>(null);
  const [finished, setFinished] = useState(false);
  const [celebrate, setCelebrate] = useState(false);
  const { words, toggleWord, hasWord, markSetRead } = useProgress();

  const sentence = set.sentences[index];
  const last = index === set.sentences.length - 1;
  const gloss = picked ? findGloss(sentence, picked.word) : undefined;
  const collectedHere = words.filter((w) => set.sentences.some((s) => s.id === w.sentenceId)).length;

  useEffect(() => {
    if (!celebrate) return;
    const timer = setTimeout(() => setCelebrate(false), 2600);
    return () => clearTimeout(timer);
  }, [celebrate]);

  function go(next: number) {
    setIndex(next);
    setPicked(null);
    setShowCn(false);
  }

  function finish() {
    markSetRead(set.id);
    setFinished(true);
    setCelebrate(true);
  }

  function collect() {
    if (!picked) return;
    toggleWord({
      word: gloss?.lemma ?? picked.word,
      simpleEn: gloss?.simpleEn,
      cn: gloss?.cn,
      sentenceId: sentence.id,
      sentence: sentence.en,
    });
  }

  const isCollected = picked ? hasWord(gloss?.lemma ?? picked.word, sentence.id) : false;

  if (finished) {
    return (
      <div className="mx-auto max-w-3xl">
        <Celebration show={celebrate} message="今日句组读完啦！" />
        <div className="glass p-8 text-center">
          <p className="text-xs tracking-widest text-muted">读 · 已完成</p>
          <h1 className="mt-2 font-display text-4xl font-semibold">{set.title}</h1>
          <p className="mt-3 text-muted">
            读了 <b className="text-fg">{set.sentences.length}</b> 个真实句子，收进生词本{" "}
            <b className="text-fg">{collectedHere}</b> 个词。
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <button
              type="button"
              onClick={() => {
                setFinished(false);
                go(0);
              }}
              className="rounded-full border border-line bg-surface-strong px-5 py-2 text-sm"
            >
              再读一遍
            </button>
          </div>
          <p className="mt-6 text-xs text-muted">下一步：写 · 仿写 2 句（后面的里程碑做）</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto grid max-w-4xl gap-5">
      <Celebration show={celebrate} message="今日句组读完啦！" />

      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs tracking-widest text-muted">读 · 今日句组</p>
          <h1 className="font-display text-4xl font-semibold leading-tight">{set.title}</h1>
          <p className="text-muted">{set.subtitle}</p>
        </div>
        <ol className="flex items-center gap-1.5" aria-label="进度">
          {set.sentences.map((s, i) => (
            <li key={s.id}>
              <button
                type="button"
                onClick={() => go(i)}
                aria-label={`第 ${i + 1} 句`}
                aria-current={i === index}
                className={cn(
                  "h-2.5 w-7 rounded-full border border-line transition-all",
                  i < index && "bg-accent",
                  i === index && "w-10 bg-[linear-gradient(90deg,var(--accent),var(--accent-2))]",
                )}
              />
            </li>
          ))}
        </ol>
      </header>

      {set.review === "draft" && set.reviewNote && (
        <p className="rounded-2xl border border-dashed border-line px-4 py-2 text-xs text-muted">{set.reviewNote}</p>
      )}

      <AnimatePresence mode="wait">
        <motion.section
          key={sentence.id}
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -30 }}
          transition={{ duration: 0.25, ease: "easeOut" }}
          className="glass flex min-h-[320px] flex-col p-7"
        >
          <div className="flex flex-wrap gap-1.5 text-xs text-muted">
            <span className="rounded-full border border-line bg-bg-2 px-2.5 py-0.5 text-accent">
              第 {index + 1} / {set.sentences.length} 句
            </span>
            <span className="rounded-full border border-line bg-bg-2 px-2.5 py-0.5">{sentence.scene}</span>
            {showStructure && (
              <span className="rounded-full border border-line bg-bg-2 px-2.5 py-0.5">{sentence.grammarNote}</span>
            )}
          </div>

          <p className="en my-auto py-6 font-sentence text-[28px] leading-[1.6] text-pretty [:root[data-style=journal]_&]:text-[32px]">
            {sentence.segments.map((seg, si) => (
              <SegmentView
                key={si}
                seg={seg}
                index={si}
                colored={showStructure}
                picked={picked}
                onPick={(tok, word) => setPicked({ seg: si, tok, word })}
              />
            ))}
          </p>

          <div className="flex flex-wrap items-center gap-2">
            <Toggle on={showStructure} onClick={() => setShowStructure((v) => !v)} icon={<Eye size={15} />}>
              看句子结构
            </Toggle>
            <Toggle on={showCn} onClick={() => setShowCn((v) => !v)} icon={<Languages size={15} />}>
              看译文
            </Toggle>
            <Toggle on={false} onClick={() => speak(sentence.en)} icon={<Volume2 size={15} />}>
              朗读整句
            </Toggle>
            {showStructure && (
              <span className="ml-1 flex items-center gap-3 text-xs text-muted">
                {ROLE_LEGEND.map((l) => (
                  <span key={l.role} className={cn("font-medium", ROLE_STYLE[l.role])}>
                    {l.label}
                  </span>
                ))}
              </span>
            )}
          </div>

          {showCn && <p className="mt-3 text-lg">{sentence.cn}</p>}

          <p className="mt-4 text-xs text-muted">
            出处：{sources[sentence.source]?.title}，{sources[sentence.source]?.year}
          </p>
        </motion.section>
      </AnimatePresence>

      <section className="glass min-h-[132px] p-5" aria-live="polite">
        {!picked && <p className="text-sm text-muted">遇到不认识的词，点一下它，看解释，再收进生词本。</p>}
        {picked && (
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <p className="flex items-baseline gap-3">
                <span className="font-word text-3xl font-semibold text-word">{gloss?.lemma ?? picked.word}</span>
                {gloss && <span className="text-muted">{gloss.pos}</span>}
              </p>
              {gloss ? (
                <>
                  <p className="en mt-1 font-sentence text-lg">{gloss.simpleEn}</p>
                  <p className="text-lg font-medium">{gloss.cn}</p>
                </>
              ) : (
                <p className="mt-1 text-sm text-muted">这个词的释义还没入库，先收进生词本，原句会一起存下来。</p>
              )}
            </div>
            <button
              type="button"
              onClick={collect}
              className={cn(
                "flex items-center gap-2 rounded-full px-4 py-2 text-sm shadow-skin transition-transform hover:-translate-y-0.5",
                isCollected ? "border border-accent text-accent" : "bg-accent text-on-accent",
              )}
            >
              {isCollected ? <BookmarkCheck size={16} /> : <BookmarkPlus size={16} />}
              {isCollected ? "已收进生词本" : "收进生词本"}
            </button>
          </div>
        )}
      </section>

      <div className="flex justify-between">
        <button
          type="button"
          disabled={index === 0}
          onClick={() => go(index - 1)}
          className="flex items-center gap-2 rounded-full border border-line bg-surface-strong px-5 py-2 text-sm disabled:opacity-40"
        >
          <ArrowLeft size={16} /> 上一句
        </button>
        {last ? (
          <button
            type="button"
            onClick={finish}
            className="flex items-center gap-2 rounded-full bg-[linear-gradient(90deg,var(--accent),var(--accent-2))] px-6 py-2 text-sm font-medium text-on-accent shadow-skin"
          >
            <Check size={16} /> 读完了
          </button>
        ) : (
          <button
            type="button"
            onClick={() => go(index + 1)}
            className="flex items-center gap-2 rounded-full bg-accent px-5 py-2 text-sm text-on-accent shadow-skin"
          >
            下一句 <ArrowRight size={16} />
          </button>
        )}
      </div>
    </div>
  );
}

function SegmentView({
  seg,
  index,
  colored,
  picked,
  onPick,
}: {
  seg: Segment;
  index: number;
  colored: boolean;
  picked: Picked | null;
  onPick: (tok: number, word: string) => void;
}) {
  const parts = [...seg.text.matchAll(TOKEN)];
  return (
    <span className={cn("transition-colors", colored && ROLE_STYLE[seg.role])}>
      {parts.map((m, ti) =>
        m[1] ? (
          <button
            key={ti}
            type="button"
            onClick={() => onPick(ti, m[1])}
            className={cn(
              "rounded-md px-0.5 transition-colors hover:bg-accent/15",
              picked?.seg === index && picked.tok === ti && "bg-accent/25",
            )}
          >
            {m[1]}
          </button>
        ) : (
          <span key={ti} className="whitespace-pre-wrap">
            {m[2]}
          </span>
        ),
      )}
    </span>
  );
}

function Toggle({
  on,
  onClick,
  icon,
  children,
}: {
  on: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={on}
      className={cn(
        "flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm transition-colors",
        on ? "border-accent bg-accent/15 text-accent" : "border-line bg-surface-strong",
      )}
    >
      {icon}
      {children}
    </button>
  );
}
