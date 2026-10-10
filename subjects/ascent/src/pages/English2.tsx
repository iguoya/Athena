import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  ArrowLeft,
  ArrowRight,
  BookCheck,
  ClipboardCheck,
  FolderInput,
  PenLine,
  RotateCcw,
  Sparkles,
  Volume2,
} from "lucide-react";
import { Celebration } from "@/components/Celebration";
import {
  importPrivate,
  privateStatus,
  trackItems,
  useEnglish2,
  type DeckItem,
  type English2,
  type Media,
  type Stage,
  type Track,
} from "@/content/english2";
import {
  buildRound,
  checkWriting,
  clozeFor,
  isChoiceTrack,
  isDue,
  PASS_RATE,
  ROUND_SIZE,
  scoreAssessment,
  stagePassed,
  WRITING_ROUND_SIZE,
  type AssessmentResult,
} from "@/content/english2-practice";
import { speak } from "@/lib/speech";
import { cn } from "@/lib/utils";
import { useEnglish2Progress } from "@/store/english2";
import { dateKey } from "@/store/progress";

// 考研英语二（ADR 0025）：服务 22408 考生的独立章节，不并入四章路线。练习即时给解析、答错
// 进错题本；考核用平行题、交卷一次评分（ADR 0024）；一轮有上限、有结束页（主仓库 ADR 0113 P6）。

type Entry = { item: DeckItem; trackId: string };
type View =
  | { kind: "home" }
  | { kind: "round"; title: string; entries: Entry[]; passage?: string; writing: boolean }
  | { kind: "assess"; track: Track }
  | { kind: "mistakes" };

export function English2() {
  const content = useEnglish2();
  const [view, setView] = useState<View>({ kind: "home" });
  const home = () => setView({ kind: "home" });

  if (view.kind === "round")
    return (
      <Round
        key={view.title}
        title={view.title}
        entries={view.entries}
        passage={view.passage ? content.passage(view.passage) : undefined}
        writing={view.writing}
        onBack={home}
      />
    );
  if (view.kind === "assess") return <Assessment content={content} track={view.track} onBack={home} />;
  if (view.kind === "mistakes") return <MistakeReview content={content} onBack={home} />;
  return <Home content={content} onOpen={setView} />;
}

/** 所有练习题按 id 找回题目与所在的轨：错题本、复习都要用。 */
function useIndex(content: English2) {
  return useMemo(() => {
    const map = new Map<string, Entry>();
    for (const stage of content.curriculum.stages)
      for (const track of stage.tracks) for (const item of trackItems(content, track)) map.set(item.id, { item, trackId: track.id });
    return map;
  }, [content]);
}

function Home({ content, onOpen }: { content: English2; onOpen: (view: View) => void }) {
  const records = useEnglish2Progress((s) => s.records);
  const mistakes = useEnglish2Progress((s) => s.mistakes);
  const assessments = useEnglish2Progress((s) => s.assessments);
  const answered = useEnglish2Progress((s) => s.answered);
  const today = dateKey();
  const passed = (path: string) => assessments[path]?.passed ?? false;
  const { stages } = content.curriculum;
  const current = stages.find((s) => !stagePassed(s, passed)) ?? stages.at(-1)!;

  // 今天这一轮：当前等级里所有选择题轨混在一起（交错），到期的先来。
  const todayEntries = useMemo(() => {
    const entries = current.tracks.filter(isChoiceTrack).flatMap((track) =>
      trackItems(content, track).map((item) => ({ item, trackId: track.id })),
    );
    const round = buildRound(entries.map((e) => e.item), records, today);
    return round.map((item) => entries.find((e) => e.item === item)!);
  }, [content, current, records, today]);
  const dueTotal = stages
    .flatMap((s) => s.tracks)
    .reduce((n, t) => n + trackItems(content, t).filter((i) => isDue(records[i.id], today)).length, 0);
  const openMistakes = Object.keys(mistakes).length;

  return (
    <div className="mx-auto grid max-h-full max-w-4xl gap-5 overflow-y-auto scroll-soft pb-1">
      <header>
        <p className="text-xs tracking-widest text-muted">22408 · 考研英语二</p>
        <h1 className="mt-1 font-display text-4xl font-semibold leading-tight">考研英语二</h1>
        <p className="mt-1 text-muted">
          先清到期的复习，再往前走一小步。单词、例句、作文三条线各自考核，三条都过了这一级才算过。
        </p>
      </header>

      <PrivateBanner content={content} />

      <section className="glass flex flex-wrap items-center gap-5 p-5">
        <Stat label="今天做了" value={answered[today] ?? 0} unit="题" />
        <Stat label="到期复习" value={dueTotal} unit="题" />
        <Stat label="错题本" value={openMistakes} unit="题" />
        <div className="ml-auto flex flex-wrap gap-2">
          {openMistakes > 0 && (
            <button type="button" onClick={() => onOpen({ kind: "mistakes" })} className={ghostButton}>
              <RotateCcw size={15} /> 清错题
            </button>
          )}
          <button
            type="button"
            disabled={todayEntries.length === 0}
            onClick={() => onOpen({ kind: "round", title: `今天这一轮 · ${current.title}`, entries: todayEntries, writing: false })}
            className={accentButton}
          >
            <Sparkles size={15} /> 今天这一轮（{todayEntries.length} 题）
          </button>
        </div>
      </section>

      {stages.map((stage) => (
        <StageCard key={stage.id} stage={stage} content={content} current={stage === current} onOpen={onOpen} />
      ))}

      {content.curriculum.endpoint && (
        <p className="rounded-2xl border border-dashed border-line px-4 py-3 text-xs leading-relaxed text-muted">
          {content.curriculum.endpoint} 内容迁自磨砚，出处逐条登记在来源目录里（ADR 0025）。
        </p>
      )}
    </div>
  );
}

function Stat({ label, value, unit }: { label: string; value: number; unit: string }) {
  return (
    <div>
      <p className="text-xs text-muted">{label}</p>
      <p className="font-display text-3xl font-semibold tabular-nums text-accent">
        {value}
        <small className="ml-1 font-body text-xs text-muted">{unit}</small>
      </p>
    </div>
  );
}

/** 本机资料缺题时如实说出来，并给出补上的办法（ADR 0025 第 3 节补充）。 */
function PrivateBanner({ content }: { content: English2 }) {
  const [message, setMessage] = useState<string | null>(null);
  if (content.loading || content.missing === 0) return null;
  const onImport = async () => {
    try {
      const status = await privateStatus();
      if (status?.dev) {
        setMessage(`开发版直接读 ${status.root}；在摘星目录运行 pnpm content:english2 <磨砚的 content 目录> 生成本机题目。`);
        return;
      }
      const copied = await importPrivate();
      if (copied !== null) window.location.reload();
    } catch (error) {
      setMessage(String(error));
    }
  };
  return (
    <section className="glass flex flex-wrap items-center gap-3 border border-dashed border-line p-4 text-sm">
      <FolderInput size={18} className="text-accent" />
      <p className="flex-1 text-muted">
        还有 <b className="text-fg">{content.missing}</b> 题引用了不能公开发布的来源，只在本机资料里，这台电脑上还没有。
        {content.error && <span className="block text-rose-500">读取本机资料出错：{content.error}</span>}
        {message && <span className="block">{message}</span>}
      </p>
      <button type="button" onClick={onImport} className={ghostButton}>
        导入本地资料
      </button>
    </section>
  );
}

function StageCard({
  stage,
  content,
  current,
  onOpen,
}: {
  stage: Stage;
  content: English2;
  current: boolean;
  onOpen: (view: View) => void;
}) {
  const records = useEnglish2Progress((s) => s.records);
  const assessments = useEnglish2Progress((s) => s.assessments);
  const today = dateKey();
  const done = stagePassed(stage, (p) => assessments[p]?.passed ?? false);
  return (
    <section className={cn("glass grid gap-3 p-5", current && "ring-2 ring-[var(--accent)]")}>
      <header className="flex items-baseline gap-3">
        <h2 className="font-display text-2xl font-semibold">{stage.title}</h2>
        <span className="text-sm text-muted">{stage.subtitle}</span>
        {done && (
          <span className="ml-auto flex items-center gap-1 text-xs text-accent">
            <BookCheck size={14} /> 三条线都通过
          </span>
        )}
        {!done && current && <span className="ml-auto text-xs text-accent">正在这一级</span>}
      </header>
      <p className="text-sm text-muted">{stage.goal}</p>
      <ul className="grid gap-2">
        {stage.tracks.map((track) => {
          const items = trackItems(content, track);
          const seen = items.filter((i) => records[i.id]).length;
          const due = items.filter((i) => isDue(records[i.id], today)).length;
          const result = assessments[track.assessment];
          const writing = !isChoiceTrack(track);
          const size = writing ? WRITING_ROUND_SIZE : ROUND_SIZE;
          const start = () =>
            onOpen({
              kind: "round",
              title: `${stage.title} · ${track.title}`,
              entries: buildRound(items, writing ? {} : records, today, size).map((item) => ({ item, trackId: track.id })),
              passage: track.passage,
              writing,
            });
          return (
            <li key={track.id} className="flex flex-wrap items-center gap-3 rounded-2xl bg-bg-2/60 px-4 py-3">
              <span className="w-12 font-display text-lg font-semibold">{track.title}</span>
              <span className="min-w-40 flex-1 text-xs text-muted">{track.goal}</span>
              <span className="text-xs tabular-nums text-muted">
                {writing ? `${items.length} 篇` : `学过 ${seen}/${items.length}`}
                {due > 0 && <b className="ml-2 text-accent">到期 {due}</b>}
              </span>
              <span className={cn("text-xs", result?.passed ? "text-accent" : "text-muted")}>
                {result ? `考核 ${Math.round(result.best * 100)}%${result.passed ? " · 已通过" : ""}` : "考核未做"}
              </span>
              <button type="button" onClick={start} disabled={items.length === 0} className={ghostButton}>
                {writing ? <PenLine size={14} /> : <Sparkles size={14} />} 练习
              </button>
              <button type="button" onClick={() => onOpen({ kind: "assess", track })} className={ghostButton}>
                <ClipboardCheck size={14} /> 考核
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

// ── 练习一轮 ──

function Round({
  title,
  entries,
  passage,
  writing,
  onBack,
}: {
  title: string;
  entries: Entry[];
  passage?: string;
  writing: boolean;
  onBack: () => void;
}) {
  const [index, setIndex] = useState(0);
  const [right, setRight] = useState(0);
  const finished = index >= entries.length;
  const next = (ok: boolean) => {
    if (ok) setRight((n) => n + 1);
    setIndex((i) => i + 1);
  };
  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col gap-4">
      <header className="flex flex-none items-center gap-3">
        <button type="button" onClick={onBack} className="flex items-center gap-1 text-xs text-muted hover:text-fg">
          <ArrowLeft size={13} /> 回到英语二
        </button>
        <span className="font-display text-lg font-semibold">{title}</span>
        <span className="ml-auto text-xs tabular-nums text-muted">
          {Math.min(index + 1, entries.length)} / {entries.length}
        </span>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto scroll-soft pr-1">
        {passage && !finished && <Passage text={passage} />}
        <AnimatePresence mode="wait">
          <motion.div key={index} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
            {finished ? (
              <RoundEnd entries={entries} right={right} writing={writing} onBack={onBack} />
            ) : writing ? (
              <WritingCard item={entries[index].item} onDone={() => next(true)} />
            ) : (
              <PracticeCard entry={entries[index]} onDone={next} />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

function Passage({ text }: { text: string }) {
  const [open, setOpen] = useState(true);
  const paragraphs = text.split(/\n\s*\n/).filter((p) => p.trim());
  return (
    <section className="glass mb-4 p-5">
      <button type="button" onClick={() => setOpen(!open)} className="text-xs text-accent">
        {open ? "收起短文" : "展开短文"}
      </button>
      {open && (
        <div className="mt-2 grid gap-2 font-sentence leading-relaxed">
          {paragraphs.map((p, i) =>
            p.startsWith("#") ? (
              <h3 key={i} className="font-display text-lg font-semibold">
                {p.replace(/^#+\s*/, "")}
              </h3>
            ) : /^\*[^*][\s\S]*\*$/.test(p.trim()) ? (
              // 整段用 *…* 包起来的是出处说明（摘编自哪里、改了什么），按注释样式显示。
              <p key={i} className="font-body text-xs italic text-muted">
                {p.trim().slice(1, -1)}
              </p>
            ) : (
              <p key={i}>{p}</p>
            ),
          )}
        </div>
      )}
    </section>
  );
}

/** 题面：先给语境（ADR 0025 收下的磨砚做法），可以朗读，带音频的给播放器。 */
function Context({ item }: { item: { sentence?: string; text?: string; media?: Media[] } }) {
  const body = item.sentence ?? item.text;
  const media = item.media;
  if (!body && !media?.length) return null;
  return (
    <div className="grid gap-2">
      {body && (
        <p className="flex items-start gap-2 font-sentence text-xl leading-relaxed">
          <span className="flex-1">{body}</span>
          <button type="button" onClick={() => speak(body)} className="mt-1 text-muted hover:text-accent" aria-label="朗读">
            <Volume2 size={18} />
          </button>
        </p>
      )}
      {media?.map((m) => m.kind === "audio" && <audio key={m.url} controls src={m.url} title={m.title} className="w-full" />)}
    </div>
  );
}

function Choices({
  choices,
  picked,
  reveal,
  onPick,
}: {
  choices: NonNullable<DeckItem["choices"]>;
  picked: number | null;
  reveal: boolean;
  onPick: (i: number) => void;
}) {
  return (
    <ul className="grid gap-2">
      {choices.map((c, i) => (
        <li key={i}>
          <button
            type="button"
            disabled={reveal}
            onClick={() => onPick(i)}
            className={cn(
              "w-full rounded-2xl border border-line px-4 py-3 text-left transition-colors",
              !reveal && "hover:border-[var(--accent)]",
              !reveal && picked === i && "border-[var(--accent)]",
              reveal && c.ok && "border-emerald-500/70 bg-emerald-500/10",
              reveal && !c.ok && picked === i && "border-rose-500/70 bg-rose-500/10",
            )}
          >
            <span>{c.label}</span>
            {reveal && c.why && <span className="mt-1 block text-xs text-muted">{c.why}</span>}
          </button>
        </li>
      ))}
    </ul>
  );
}

/** probe：答对后要不要换句挖空写词形。错题本里关掉——挖空用的正是接下来要考的变式句，会先露底。 */
function PracticeCard({ entry, onDone, probe = true }: { entry: Entry; onDone: (ok: boolean) => void; probe?: boolean }) {
  const { item, trackId } = entry;
  const answer = useEnglish2Progress((s) => s.answer);
  const [picked, setPicked] = useState<number | null>(null);
  const ok = picked !== null && Boolean(item.choices?.[picked]?.ok);
  const pick = (i: number) => {
    setPicked(i);
    answer(item, trackId, Boolean(item.choices?.[i]?.ok));
  };
  return (
    <article className="glass grid gap-4 p-6">
      <Context item={item} />
      <p className="font-medium">{item.prompt}</p>
      <Choices choices={item.choices ?? []} picked={picked} reveal={picked !== null} onPick={pick} />
      {picked !== null && (
        <>
          {item.word && (
            <p className="rounded-2xl bg-bg-2/60 px-4 py-3 text-sm">
              <b className="font-word text-lg text-word">{item.word}</b>
              {item.senses?.map((s, i) => (
                <span key={i} className="ml-3 text-muted">
                  {s.pos}. {s.gloss}
                </span>
              ))}
            </p>
          )}
          {ok && probe && <ClozeProbe item={item} />}
          {!ok && <p className="text-xs text-muted">已进错题本：隔天答对一次、再做对一道变式就会出库。</p>}
          <button type="button" onClick={() => onDone(ok)} className={cn(accentButton, "justify-self-end")}>
            下一题 <ArrowRight size={15} />
          </button>
        </>
      )}
    </article>
  );
}

/** 答对后换一句、挖空写出词形：把认得变成写得出（只练不计分）。 */
function ClozeProbe({ item }: { item: DeckItem }) {
  const cloze = useMemo(() => clozeFor(item), [item]);
  const [value, setValue] = useState("");
  const [checked, setChecked] = useState(false);
  if (!cloze) return null;
  const right = value.trim().toLowerCase() === cloze.answer.toLowerCase();
  return (
    <div className="grid gap-2 rounded-2xl border border-dashed border-line px-4 py-3">
      <p className="text-xs text-muted">换一句，把这个词写回去：</p>
      <p className="font-sentence text-lg">
        {cloze.before}
        <input
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setChecked(false);
          }}
          onKeyDown={(e) => e.key === "Enter" && setChecked(true)}
          className="mx-1 w-32 border-b border-[var(--accent)] bg-transparent text-center outline-none"
          aria-label="写出词形"
        />
        {cloze.after}
      </p>
      {checked && (
        <p className={cn("text-xs", right ? "text-emerald-500" : "text-rose-500")}>
          {right ? "写对了。" : `应为 ${cloze.answer}。`}
        </p>
      )}
    </div>
  );
}

function WritingCard({ item, onDone }: { item: DeckItem; onDone: () => void }) {
  const save = useEnglish2Progress((s) => s.saveWriting);
  const [text, setText] = useState(item.starter ? `${item.starter} ` : "");
  const [checked, setChecked] = useState(false);
  const result = checkWriting(text, item);
  return (
    <article className="glass grid gap-4 p-6">
      <p className="font-medium">{item.prompt}</p>
      <textarea
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setChecked(false);
        }}
        rows={7}
        className="w-full rounded-2xl border border-line bg-transparent p-4 font-sentence text-lg leading-relaxed outline-none focus:border-[var(--accent)]"
      />
      <p className="text-xs text-muted">
        {result.words} 词 · 至少 {item.min_words ?? 0} 词
        {item.required_any?.length ? ` · 用上其中一个：${item.required_any.join(" / ")}` : ""}
      </p>
      {!checked ? (
        <button
          type="button"
          onClick={() => {
            setChecked(true);
            save(item.id, result.words);
          }}
          className={cn(accentButton, "justify-self-end")}
        >
          写好了，对照一下
        </button>
      ) : (
        <>
          <ul className="grid gap-1 text-sm">
            <li className={result.enoughWords ? "text-emerald-500" : "text-rose-500"}>
              字数 {result.enoughWords ? "够了" : "还不够"}
            </li>
            <li className={result.connectorOk ? "text-emerald-500" : "text-rose-500"}>
              {result.connector ? `用上了 ${result.connector}` : result.connectorOk ? "没有指定衔接词" : "还没用上指定的衔接词"}
            </li>
          </ul>
          {item.reference && (
            <div className="rounded-2xl bg-bg-2/60 px-4 py-3">
              <p className="text-xs text-muted">参考写法（不是唯一答案）</p>
              <p className="font-sentence text-lg">{item.reference}</p>
            </div>
          )}
          {item.checklist && (
            <div>
              <p className="text-xs text-muted">自己对照着看：</p>
              <ul className="list-disc pl-5 text-sm">
                {item.checklist.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </div>
          )}
          <p className="text-xs text-muted">作文只机检字数与衔接，组织和用词自己对照，不计入掌握度。</p>
          <button type="button" onClick={onDone} className={cn(accentButton, "justify-self-end")}>
            下一篇 <ArrowRight size={15} />
          </button>
        </>
      )}
    </article>
  );
}

/** 结束页：先凭记忆写下这一轮记住了什么，再看清单对照（主仓库 ADR 0113 P8，可跳过）。 */
function RoundEnd({ entries, right, writing, onBack }: { entries: Entry[]; right: number; writing: boolean; onBack: () => void }) {
  const [recall, setRecall] = useState("");
  const [shown, setShown] = useState(false);
  return (
    <article className="glass grid gap-4 p-6">
      <h2 className="font-display text-2xl font-semibold">这一轮做完了</h2>
      {!writing && (
        <p className="text-muted">
          {entries.length} 题里答对 <b className="text-fg">{right}</b> 题。答错的已进错题本，到期的题会自动排进以后的轮次。
        </p>
      )}
      {entries.length > 0 && (
        <>
          <p className="text-sm text-muted">合上前，凭记忆写下这一轮记住的词和句子（可以跳过）：</p>
          <textarea
            value={recall}
            onChange={(e) => setRecall(e.target.value)}
            rows={4}
            className="w-full rounded-2xl border border-line bg-transparent p-3 outline-none focus:border-[var(--accent)]"
          />
          {!shown ? (
            <button type="button" onClick={() => setShown(true)} className={cn(ghostButton, "justify-self-start")}>
              对照这一轮的题目
            </button>
          ) : (
            <ul className="grid gap-1 text-sm">
              {entries.map(({ item }) => (
                <li key={item.id} className="text-muted">
                  {item.word ? <b className="text-fg">{item.word} </b> : null}
                  {item.sentence ?? item.text ?? item.prompt}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
      <button type="button" onClick={onBack} className={cn(accentButton, "justify-self-end")}>
        回到英语二
      </button>
    </article>
  );
}

// ── 考核 ──

function Assessment({ content, track, onBack }: { content: English2; track: Track; onBack: () => void }) {
  const deck = content.deck(track.assessment);
  const submit = useEnglish2Progress((s) => s.submitAssessment);
  const record = useEnglish2Progress((s) => s.assessments[track.assessment]);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const items = deck?.items ?? [];
  const left = items.filter((i) => answers[i.id] === undefined).length;
  // 缺了本机题的考核只是半套卷：可以做着练手，但不记成绩，免得半套卷考出个「通过」。
  const missing = content.loading ? 0 : content.missingIn(track.assessment);

  const onSubmit = () => {
    const scored = scoreAssessment(items, answers);
    if (missing === 0) submit(track.assessment, scored);
    setResult(scored);
  };

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col gap-4">
      <header className="flex flex-none flex-wrap items-center gap-3">
        <button type="button" onClick={onBack} className="flex items-center gap-1 text-xs text-muted hover:text-fg">
          <ArrowLeft size={13} /> 回到英语二
        </button>
        <span className="font-display text-lg font-semibold">{deck?.title ?? `${track.title}考核`}</span>
        {/* 考核与练习在界面上可见地区分（主仓库 LEARNING-METHODS P4）。 */}
        <span className="rounded-full border border-[var(--accent)] px-2 py-0.5 text-xs text-accent">
          {result ? "已交卷" : "考核中 · 交卷前不给解析"}
        </span>
        {record && <span className="ml-auto text-xs text-muted">最好成绩 {Math.round(record.best * 100)}%</span>}
      </header>
      <Celebration show={(result?.passed ?? false) && missing === 0} message="这条线的考核通过啦！" />
      <div className="min-h-0 flex-1 overflow-y-auto scroll-soft pr-1">
        {missing > 0 && (
          <p className="glass mb-4 border border-dashed border-line p-4 text-sm text-muted">
            这套考核还有 {missing} 题在本机资料里，这台电脑上没有。现在交卷只算练手，不记成绩；导入本地资料后再考才算数。
          </p>
        )}
        {items.length === 0 ? (
          <p className="glass p-6 text-muted">这套考核的题目在本机资料里，这台电脑上还没有。先在英语二首页导入本地资料。</p>
        ) : (
          <div className="grid gap-4">
            {result && (
              <section className="glass p-5">
                <p className="font-display text-3xl font-semibold tabular-nums text-accent">
                  {result.correct} / {result.total}
                  <small className="ml-2 font-body text-sm text-muted">{Math.round(result.rate * 100)}%</small>
                </p>
                <p className="mt-1 text-sm text-muted">
                  {missing > 0
                    ? "缺了本机题的半套卷，这次只算练手，没有记成绩。"
                    : result.passed
                    ? "通过了。通过资格不会因为以后考差而收回。"
                    : `还差一点：达到 ${Math.round(PASS_RATE * 100)}% 才算通过。下面是每题的解析，回去多练几轮再来。`}
                </p>
              </section>
            )}
            {items.map((item, n) => (
              <article key={item.id} className="glass grid gap-3 p-5">
                <p className="text-xs text-muted">第 {n + 1} 题</p>
                <Context item={item} />
                <p className="font-medium">{item.prompt}</p>
                <Choices
                  choices={item.choices ?? []}
                  picked={answers[item.id] ?? null}
                  reveal={result !== null}
                  onPick={(i) => setAnswers((a) => ({ ...a, [item.id]: i }))}
                />
              </article>
            ))}
            {!result && (
              <button type="button" onClick={onSubmit} className={cn(accentButton, "justify-self-end")}>
                交卷{left > 0 ? `（还有 ${left} 题没答，按错算）` : ""}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── 错题本 ──

function MistakeReview({ content, onBack }: { content: English2; onBack: () => void }) {
  const mistakes = useEnglish2Progress((s) => s.mistakes);
  const index = useIndex(content);
  // 打开时定下这一轮要清的题，作答中途错题本变化不打乱顺序。
  const [queue] = useState(() =>
    Object.values(mistakes)
      .sort((a, b) => a.opened.localeCompare(b.opened))
      .slice(0, ROUND_SIZE)
      .map((m) => index.get(m.itemId))
      .filter((e): e is Entry => e !== undefined),
  );
  // 每道错题先做母题，有变式的再做一道变式；没有变式的只做母题（变式条件打开时已记为满足）。
  const steps = useMemo(
    () => queue.flatMap((e) => [{ entry: e, variant: false }, ...(e.item.variants?.length ? [{ entry: e, variant: true }] : [])]),
    [queue],
  );
  const [step, setStep] = useState(0);
  const entry = steps[step]?.entry;
  const onVariant = steps[step]?.variant ?? false;

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col gap-4">
      <header className="flex flex-none items-center gap-3">
        <button type="button" onClick={onBack} className="flex items-center gap-1 text-xs text-muted hover:text-fg">
          <ArrowLeft size={13} /> 回到英语二
        </button>
        <span className="font-display text-lg font-semibold">错题本</span>
        <span className="ml-auto text-xs text-muted">出库条件：隔天答对一次 + 做对一道变式</span>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto scroll-soft pr-1">
        {!entry ? (
          <article className="glass grid gap-3 p-6">
            <h2 className="font-display text-2xl font-semibold">这一轮错题清完了</h2>
            <p className="text-muted">还在错题本里的：{Object.keys(mistakes).length} 题。没满足两个条件的会继续留着。</p>
            <button type="button" onClick={onBack} className={cn(accentButton, "justify-self-end")}>
              回到英语二
            </button>
          </article>
        ) : onVariant ? (
          <VariantCard key={`${entry.item.id}-v`} entry={entry} onDone={() => setStep((s) => s + 1)} />
        ) : (
          <PracticeCard key={entry.item.id} entry={entry} probe={false} onDone={() => setStep((s) => s + 1)} />
        )}
      </div>
    </div>
  );
}

function VariantCard({ entry, onDone }: { entry: Entry; onDone: () => void }) {
  const answerVariant = useEnglish2Progress((s) => s.answerVariant);
  const variant = entry.item.variants![0];
  const [picked, setPicked] = useState<number | null>(null);
  return (
    <article className="glass grid gap-4 p-6">
      <p className="text-xs text-muted">换一句考同一个点：</p>
      <Context item={variant} />
      <p className="font-medium">{variant.prompt}</p>
      <Choices
        choices={variant.choices}
        picked={picked}
        reveal={picked !== null}
        onPick={(i) => {
          setPicked(i);
          answerVariant(entry.item, entry.trackId, Boolean(variant.choices[i]?.ok));
        }}
      />
      {picked !== null && (
        <button type="button" onClick={onDone} className={cn(accentButton, "justify-self-end")}>
          下一题 <ArrowRight size={15} />
        </button>
      )}
    </article>
  );
}

const accentButton =
  "flex items-center gap-2 rounded-full bg-[linear-gradient(90deg,var(--accent),var(--accent-2))] px-5 py-2.5 text-sm font-medium text-on-accent shadow-skin transition-transform hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0";
const ghostButton =
  "flex items-center gap-1.5 rounded-full border border-line px-3.5 py-1.5 text-xs transition-colors hover:border-[var(--accent)] hover:text-accent disabled:opacity-50";

