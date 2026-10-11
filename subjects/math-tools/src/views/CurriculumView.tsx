import { useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { chapters, type Tool } from '../data/curriculum'
import { ChevronDown, Circle, CheckCircle2, Target, ListChecks } from 'lucide-react'
import { cn } from '@/lib/utils'

const KEY = 'mt-curriculum-done'

function loadDone(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '{}')
  } catch {
    return {}
  }
}

function key(chapterId: string, index: number): string {
  return `${chapterId}-${index}`
}

const toolStyle: Record<Tool, string> = {
  GeoGebra: 'bg-violet-500/10 text-violet-600 dark:text-violet-300 ring-violet-400/30',
  Octave: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-300 ring-cyan-400/30',
  SymPy: 'bg-amber-500/10 text-amber-600 dark:text-amber-300 ring-amber-400/30',
  'Math Tools': 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 ring-emerald-400/30',
  理论: 'bg-slate-500/10 text-slate-500 dark:text-slate-300 ring-slate-400/30',
}

const total = chapters.reduce((n, c) => n + c.items.length, 0)

export default function CurriculumView() {
  const [done, setDone] = useState<Record<string, boolean>>(loadDone)
  const [opened, setOpened] = useState<string | null>(chapters[0]?.id ?? null)

  function toggle(chapterId: string, index: number) {
    const k = key(chapterId, index)
    const next = { ...done, [k]: !done[k] }
    setDone(next)
    localStorage.setItem(KEY, JSON.stringify(next))
  }

  function chapterProgress(chapterId: string, count: number): number {
    let n = 0
    for (let i = 0; i < count; i++) if (done[key(chapterId, i)]) n++
    return n
  }

  const doneCount = chapters.reduce((n, c) => n + chapterProgress(c.id, c.items.length), 0)
  const pct = Math.round((doneCount / total) * 100)

  return (
    <section>
      {/* 头部:定位语 + 总进度 */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <p className="accent-fg mb-2 flex items-center gap-2 text-xs font-medium tracking-widest">
          <ListChecks size={14} /> CURRICULUM
        </p>
        <h1 className="tk-display text-2xl font-bold">练习纲要</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500 dark:text-slate-400">
          每个概念走三遍:
          <span className="font-medium text-slate-700 dark:text-slate-200">
            看一遍直觉、拖一遍图形、算一遍数值
          </span>
          。 勾选存本机浏览器,进度只对自己负责。
        </p>

        <div className="card mt-5 flex items-center gap-4 p-4">
          <div className="accent-gradient accent-glow grid size-11 shrink-0 place-items-center rounded-xl text-white">
            <Target size={20} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="mb-1.5 flex items-baseline justify-between">
              <p className="text-sm font-medium">总进度</p>
              <p className="font-mono text-xs text-slate-400">
                {doneCount} / {total} · {pct}%
              </p>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-200/70 dark:bg-white/10">
              <div
                className="accent-gradient h-full rounded-full transition-all duration-500 ease-out"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        </div>
      </motion.div>

      {/* 章节 */}
      <div className="mt-6 flex flex-col gap-3.5">
        {chapters.map((c, ci) => {
          const progress = chapterProgress(c.id, c.items.length)
          const isOpen = opened === c.id
          return (
            <motion.div
              key={c.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.08 + ci * 0.06, ease: 'easeOut' }}
              className="card tape overflow-hidden"
            >
              {/* 章头 */}
              <button
                className="flex w-full items-center gap-4 p-5 text-left transition hover:bg-slate-50/60 dark:hover:bg-white/[0.03]"
                onClick={() => setOpened(isOpen ? null : c.id)}
              >
                <span className="accent-gradient accent-glow grid size-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br font-mono text-sm font-bold text-white shadow">
                  {ci}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-baseline gap-2">
                    <span className="tk-display text-base font-semibold">{c.title}</span>
                    <span className="font-mono text-[11px] tracking-wide text-slate-400">
                      {c.en}
                    </span>
                  </span>
                  <span className="mt-0.5 block truncate text-xs text-slate-500 dark:text-slate-400">
                    {c.goal}
                  </span>
                </span>
                <span
                  className={cn(
                    'shrink-0 font-mono text-[11px]',
                    progress === c.items.length ? 'text-emerald-500' : 'text-slate-400',
                  )}
                >
                  {progress}/{c.items.length}
                </span>
                <ChevronDown
                  size={17}
                  className={cn(
                    'shrink-0 text-slate-400 transition-transform duration-300',
                    isOpen && 'rotate-180',
                  )}
                />
              </button>

              {/* 展开的练习项 */}
              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    key="body"
                    initial={{ opacity: 0, scale: 0.96, y: 6 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="border-t border-slate-200/70 px-5 pb-5 pt-4 dark:border-white/10"
                  >
                    <p className="accent-soft mb-4 flex items-start gap-2 rounded-xl px-3.5 py-2.5 text-xs leading-relaxed text-slate-600 dark:text-slate-300">
                      <Target size={13} className="accent-fg mt-0.5 shrink-0" />
                      本章目标:{c.goal}
                    </p>
                    <ol className="flex flex-col gap-4">
                      {c.items.map((it, ii) => {
                        const checked = !!done[key(c.id, ii)]
                        return (
                          <li key={ii} className={cn('flex gap-3', checked && 'opacity-55')}>
                            <button
                              className="mt-0.5 shrink-0 transition hover:scale-110 active:scale-90"
                              title={checked ? '取消完成' : '标记完成'}
                              onClick={() => toggle(c.id, ii)}
                            >
                              <AnimatePresence mode="wait" initial={false}>
                                <motion.span
                                  key={checked ? 'on' : 'off'}
                                  className="block"
                                  initial={{ opacity: 0, scale: 0.96 }}
                                  animate={{ opacity: 1, scale: 1 }}
                                  exit={{ opacity: 0 }}
                                  transition={{ duration: 0.15 }}
                                >
                                  {checked ? (
                                    <CheckCircle2 size={19} className="text-emerald-500" />
                                  ) : (
                                    <Circle size={19} className="text-slate-300 dark:text-slate-600" />
                                  )}
                                </motion.span>
                              </AnimatePresence>
                            </button>
                            <div className="min-w-0 flex-1">
                              <p
                                className={cn(
                                  'text-sm leading-relaxed',
                                  checked && 'line-through decoration-slate-400',
                                )}
                              >
                                {it.point}
                              </p>
                              <p className="mt-1.5 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                                <span className="mr-1 font-medium text-emerald-600 dark:text-emerald-400">
                                  验收
                                </span>
                                {it.req}
                              </p>
                              <p className="mt-2 flex flex-wrap gap-1.5">
                                {it.tools.map((t) => (
                                  <span
                                    key={t}
                                    className={cn(
                                      'rounded-full px-2 py-0.5 font-mono text-[10px] ring-1',
                                      toolStyle[t],
                                    )}
                                  >
                                    {t}
                                  </span>
                                ))}
                              </p>
                            </div>
                          </li>
                        )
                      })}
                    </ol>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )
        })}
      </div>
    </section>
  )
}
