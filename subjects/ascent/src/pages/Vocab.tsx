import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  ArrowLeft,
  ArrowRight,
  BookmarkCheck,
  BookmarkPlus,
  Check,
  ChevronRight,
  Sparkles,
  Trophy,
  Turtle,
  Volume2,
} from "lucide-react";
import { Celebration } from "@/components/Celebration";
import { VOCAB_BANKS, bankFreq, bankStages, loadWords } from "@/content/vocab";
import type { VocabStage, VocabWord } from "@/content/types";
import { speak, SLOW_RATE } from "@/lib/speech";
import { allSeenWords, useProgress } from "@/store/progress";
import { cn } from "@/lib/utils";

export function Vocab() {
  const [exam, setExam] = useState<string | null>(null);
  const [stage, setStage] = useState<VocabStage | null>(null);

  const seenWords = useProgress((s) => s.seenWords);
  const seen = useMemo(() => allSeenWords(seenWords), [seenWords]);

  if (stage && exam) return <StageLearner exam={exam} stage={stage} seen={seen} onBack={() => setStage(null)} />;
  if (exam) return <StagesView exam={exam} seen={seen} onBack={() => setExam(null)} onPick={setStage} />;
  return <BanksView seen={seen} onPick={setExam} />;
}

function BanksView({ seen, onPick }: { seen: Set<string>; onPick: (exam: string) => void }) {
  return (
    <div className="mx-auto grid max-w-4xl gap-5">
      <header>
        <p className="text-xs tracking-widest text-muted">词汇 · 拾阶而上</p>
        <h1 className="mt-1 font-display text-4xl font-semibold leading-tight">词库阶梯</h1>
        <p className="mt-1 text-muted">
          高中、四级、六级各成一架梯子，按真实语料里的常用程度先易后难分成小阶段。每天 15 个，一阶大约一个月。
        </p>
      </header>
      <div className="grid gap-4 md:grid-cols-3">
        {VOCAB_BANKS.map((bank) => {
          const file = bankStages(bank.id);
          const total = file?.stages.reduce((n, s) => n + s.words.length, 0) ?? 0;
          const learned = file?.stages.reduce((n, s) => n + s.words.filter((w) => seen.has(w)).length, 0) ?? 0;
          return (
            <button
              key={bank.id}
              type="button"
              onClick={() => onPick(bank.id)}
              className="glass flex flex-col gap-2 p-5 text-left transition-transform hover:-translate-y-0.5"
            >
              <span className="font-display text-2xl font-semibold">{bank.name}</span>
              <span className="text-xs text-muted">{bank.blurb}</span>
              <span className="font-display text-3xl font-semibold tabular-nums text-accent">
                {learned}
                <small className="ml-1 font-body text-xs text-muted">/ {total} 学过</small>
              </span>
              <span className="mt-1 h-2 overflow-hidden rounded-full bg-bg-2">
                <span
                  className="block h-full rounded-full bg-[linear-gradient(90deg,var(--accent),var(--accent-2))]"
                  style={{ width: `${total ? Math.round((learned / total) * 100) : 0}%` }}
                />
              </span>
              <span className="mt-1 flex items-center gap-1 text-xs text-accent">
                {file?.stages.length ?? 0} 个阶段，进入 <ChevronRight size={13} />
              </span>
            </button>
          );
        })}
      </div>
      <p className="rounded-2xl border border-dashed border-line px-4 py-3 text-xs leading-relaxed text-muted">
        阶段怎么排的：全部词按 ECDICT 真实语料词频、Collins 星级、Oxford 3000 和四级真题词频排序（ADR 0022），
        最常见的词在第一阶。词的释义是 ECDICT 草稿，例句和真题原句会随后面的里程碑进来。
      </p>
    </div>
  );
}

function StagesView({
  exam,
  seen,
  onBack,
  onPick,
}: {
  exam: string;
  seen: Set<string>;
  onBack: () => void;
  onPick: (stage: VocabStage) => void;
}) {
  const bank = VOCAB_BANKS.find((b) => b.id === exam);
  const file = bankStages(exam);
  const milestones = useProgress((s) => s.milestones);
  if (!file) return <p className="text-muted">词库 {exam} 没有分阶数据。</p>;

  // 推荐第一个还没通关的阶段。
  const doneIds = new Set(milestones.map((m) => m.id));
  const current = file.stages.find((s) => !doneIds.has(`stage:${s.id}`));

  return (
    <div className="mx-auto grid max-w-4xl gap-5">
      <header className="flex items-end justify-between gap-3">
        <div>
          <button
            type="button"
            onClick={onBack}
            className="mb-1 flex items-center gap-1 text-xs text-muted hover:text-fg"
          >
            <ArrowLeft size={13} /> 换一架梯子
          </button>
          <h1 className="font-display text-4xl font-semibold leading-tight">{bank?.name}</h1>
          <p className="mt-1 text-muted">{bank?.blurb}</p>
        </div>
        {current && (
          <button
            type="button"
            onClick={() => onPick(current)}
            className="flex items-center gap-2 rounded-full bg-[linear-gradient(90deg,var(--accent),var(--accent-2))] px-5 py-2.5 text-sm font-medium text-on-accent shadow-skin transition-transform hover:-translate-y-0.5"
          >
            <Sparkles size={15} /> 继续学：第 {file.stages.indexOf(current) + 1} 阶
          </button>
        )}
      </header>

      <ol className="grid gap-3">
        {file.stages.map((s, i) => {
          const learned = s.words.filter((w) => seen.has(w)).length;
          const total = s.words.length;
          const complete = doneIds.has(`stage:${s.id}`);
          const pct = total ? Math.round((learned / total) * 100) : 0;
          return (
            <li key={s.id}>
              <button
                type="button"
                onClick={() => onPick(s)}
                className={cn(
                  "glass flex w-full items-center gap-4 p-4 text-left transition-transform hover:-translate-y-0.5",
                  complete && "border-accent/60",
                )}
              >
                <span
                  className={cn(
                    "grid h-12 w-12 flex-none place-items-center rounded-2xl font-display text-lg font-bold",
                    complete ? "bg-accent text-on-accent" : "bg-bg-2 text-muted",
                  )}
                >
                  {complete ? <Trophy size={20} /> : i + 1}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-baseline gap-2">
                    <span className="font-display text-lg font-semibold">{s.title}</span>
                    <span className="text-xs text-muted">
                      {learned} / {total} 学过
                    </span>
                    {complete && <span className="text-xs font-medium text-accent">已通关</span>}
                  </span>
                  <span className="mt-0.5 block truncate text-xs text-muted">{s.blurb}</span>
                  <span className="mt-1.5 block h-1.5 overflow-hidden rounded-full bg-bg-2">
                    <span
                      className="block h-full rounded-full bg-[linear-gradient(90deg,var(--accent),var(--accent-2))]"
                      style={{ width: `${pct}%` }}
                    />
                  </span>
                </span>
                <ChevronRight size={18} className="flex-none text-muted" />
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function StageLearner({
  exam,
  stage,
  seen,
  onBack,
}: {
  exam: string;
  stage: VocabStage;
  seen: Set<string>;
  onBack: () => void;
}) {
  const [words, setWords] = useState<Record<string, VocabWord> | null>(null);
  const [missing, setMissing] = useState(false);
  const [index, setIndex] = useState(0);
  const [finished, setFinished] = useState(false);
  const [celebrate, setCelebrate] = useState(false);
  const freq = useMemo(() => bankFreq(exam), [exam]);
  const { toggleWord, hasWord, markWordSeen, markStageComplete } = useProgress();

  useEffect(() => {
    let alive = true;
    loadWords(exam)
      .then((m) => alive && setWords(m))
      .catch(() => alive && setMissing(true));
    return () => {
      alive = false;
    };
  }, [exam]);

  useEffect(() => {
    if (!celebrate) return;
    const timer = setTimeout(() => setCelebrate(false), 2600);
    return () => clearTimeout(timer);
  }, [celebrate]);

  const learnedCount = stage.words.filter((w) => seen.has(w.toLowerCase())).length;
  const last = index === stage.words.length - 1;
  const word = stage.words[index];
  const entry = words?.[word];
  const hits = freq[word]?.hits ?? 0;

  function advance() {
    markWordSeen(word);
    if (last) {
      markStageComplete(stage.id);
      setFinished(true);
      setCelebrate(true);
    } else {
      setIndex((i) => i + 1);
    }
  }

  function collect() {
    toggleWord({
      word: entry?.word ?? word,
      simpleEn: entry?.simpleEn ?? undefined,
      cn: entry?.cnDraft ?? undefined,
      sentenceId: `vocab:${stage.id}`,
      sentence: "",
    });
  }

  if (missing) return <p className="text-muted">词库 {exam} 的词条加载失败。</p>;
  if (!words) return <p className="p-8 text-center text-muted">词库加载中……</p>;

  if (finished) {
    return (
      <div className="mx-auto max-w-3xl">
        <Celebration show={celebrate} message="这一阶通关啦！" />
        <div className="glass p-8 text-center">
          <p className="text-xs tracking-widest text-muted">词汇 · 已通关</p>
          <h1 className="mt-2 font-display text-4xl font-semibold">{stage.title}</h1>
          <p className="mt-3 text-muted">
            这一阶 <b className="text-fg">{stage.words.length}</b> 个词你都过了一遍。明天再来翻下一阶，
            换个日子再见它们，记得才牢。
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <button
              type="button"
              onClick={() => {
                setIndex(0);
                setFinished(false);
              }}
              className="rounded-full border border-line bg-surface-strong px-5 py-2 text-sm"
            >
              再过一遍
            </button>
            <button
              type="button"
              onClick={onBack}
              className="rounded-full bg-accent px-5 py-2 text-sm text-on-accent shadow-skin"
            >
              回阶段列表
            </button>
          </div>
        </div>
      </div>
    );
  }

  const collected = hasWord(entry?.word ?? word, `vocab:${stage.id}`);

  return (
    <div className="mx-auto grid max-w-4xl gap-5">
      <Celebration show={celebrate} message="这一阶通关啦！" />
      <header className="flex items-end justify-between gap-3">
        <div>
          <button
            type="button"
            onClick={onBack}
            className="mb-1 flex items-center gap-1 text-xs text-muted hover:text-fg"
          >
            <ArrowLeft size={13} /> {stage.title}
          </button>
          <p className="text-muted">
            学过 <b className="text-fg tabular-nums">{learnedCount}</b> / {stage.words.length} · 第 {index + 1} 个
          </p>
        </div>
        <span className="rounded-full bg-surface-strong px-3 py-1.5 text-xs text-muted shadow-skin">{stage.blurb}</span>
      </header>

      <span className="h-2 overflow-hidden rounded-full bg-bg-2">
        <motion.span
          className="block h-full rounded-full bg-[linear-gradient(90deg,var(--accent),var(--accent-2))]"
          initial={{ width: 0 }}
          animate={{ width: `${Math.round((learnedCount / stage.words.length) * 100)}%` }}
        />
      </span>

      <AnimatePresence mode="wait">
        <motion.section
          key={`${stage.id}-${index}`}
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -30 }}
          transition={{ duration: 0.25, ease: "easeOut" }}
          className="glass flex min-h-[300px] flex-col items-center justify-center gap-3 p-8 text-center"
        >
          <p className="font-word text-6xl font-semibold text-word">{word}</p>
          {entry?.phonetic && <p className="font-sentence text-lg text-muted">/{entry.phonetic}/</p>}
          <div className="flex flex-wrap justify-center gap-1.5 text-xs">
            {!!entry?.collins && (
              <span className="rounded-full border border-line bg-bg-2 px-2.5 py-0.5 text-muted">
                Collins {"★".repeat(entry.collins)}
              </span>
            )}
            {entry?.oxford3000 && (
              <span className="rounded-full border border-line bg-bg-2 px-2.5 py-0.5 text-muted">Oxford 3000</span>
            )}
            {hits > 0 && (
              <span className="rounded-full border border-line bg-bg-2 px-2.5 py-0.5 text-accent">
                四级真题出现 {hits} 次
              </span>
            )}
          </div>
          {entry?.simpleEn && <p className="en mt-2 max-w-xl font-sentence text-lg">{entry.simpleEn}</p>}
          {entry?.cnDraft && <p className="max-w-xl text-xl font-medium">{entry.cnDraft}</p>}
          <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
            <button
              type="button"
              onClick={() => {
                speak(word);
                markWordSeen(word);
              }}
              className="flex items-center gap-2 rounded-full border border-line bg-surface-strong px-4 py-2 text-sm"
            >
              <Volume2 size={16} /> 读一遍
            </button>
            <button
              type="button"
              onClick={() => {
                speak(word, SLOW_RATE);
                markWordSeen(word);
              }}
              className="flex items-center gap-2 rounded-full border border-line bg-surface-strong px-4 py-2 text-sm"
            >
              <Turtle size={16} /> 慢速
            </button>
            <button
              type="button"
              onClick={collect}
              className={cn(
                "flex items-center gap-2 rounded-full px-4 py-2 text-sm",
                collected ? "border border-accent text-accent" : "border border-line bg-surface-strong",
              )}
            >
              {collected ? <BookmarkCheck size={16} /> : <BookmarkPlus size={16} />}
              {collected ? "已在生词本" : "收进生词本"}
            </button>
          </div>
          <p className="mt-1 text-xs text-muted">
            释义：{entry?.source === "ecdict" ? "ECDICT" : (entry?.source ?? "ECDICT")} 草稿 ·
            真实例句在后面的里程碑接入
          </p>
        </motion.section>
      </AnimatePresence>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={advance}
          className="flex items-center gap-2 rounded-full bg-accent px-5 py-2 text-sm text-on-accent shadow-skin"
        >
          {last ? (
            <>
              <Check size={16} /> 这一阶过完了
            </>
          ) : (
            <>
              认识了，下一个 <ArrowRight size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
