import { useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Home, Grid3x3, LineChart, BookOpen, Sigma, type LucideIcon } from 'lucide-react'
import HomeView from './views/HomeView'
import MatrixView from './views/MatrixView'
import PlotView from './views/PlotView'
import CurriculumView from './views/CurriculumView'
import { SKINS, applySkin, currentSkin, type SkinId } from './theme'
import { cn } from '@/lib/utils'

export type TabId = 'home' | 'curriculum' | 'matrix' | 'plot'

const tabs: { id: TabId; label: string; icon: LucideIcon }[] = [
  { id: 'home', label: '首页', icon: Home },
  { id: 'curriculum', label: '练习纲要', icon: BookOpen },
  { id: 'matrix', label: '矩阵实验室', icon: Grid3x3 },
  { id: 'plot', label: '函数绘图', icon: LineChart },
]

// 各页外层容器:绘图页要撑满高度,其余页居中限宽。
const pageClass: Record<TabId, string> = {
  home: 'mx-auto max-w-5xl px-10 py-10',
  curriculum: 'mx-auto max-w-4xl px-10 py-10',
  matrix: 'mx-auto max-w-5xl px-10 py-10',
  plot: 'h-full',
}

export default function App() {
  const [active, setActive] = useState<TabId>('home')
  const [skin, setSkinState] = useState<SkinId>(currentSkin())

  function setSkin(id: SkinId) {
    setSkinState(id)
    applySkin(id)
  }

  return (
    <div className="flex h-full">
      {/* 侧栏 */}
      <aside
        className="relative z-10 flex w-60 shrink-0 flex-col border-r px-4 py-5 backdrop-blur-xl"
        style={{
          borderColor: 'var(--tk-line)',
          background: 'color-mix(in oklab, var(--tk-surface) 60%, transparent)',
        }}
      >
        <div className="mb-8 flex items-center gap-3 px-2">
          <div className="accent-gradient accent-glow grid size-10 place-items-center rounded-xl text-white">
            <Sigma size={22} strokeWidth={2.5} />
          </div>
          <div>
            <p className="tk-display text-sm font-semibold tracking-wide">数学工具</p>
            <p className="text-xs" style={{ color: 'var(--tk-muted)' }}>
              Math Tools
            </p>
          </div>
        </div>

        <nav className="flex flex-col gap-1">
          {tabs.map((t) => {
            const on = active === t.id
            return (
              <button
                key={t.id}
                className={cn(
                  'group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors',
                  on
                    ? 'text-slate-900 dark:text-white'
                    : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200',
                )}
                onClick={() => setActive(t.id)}
              >
                <AnimatePresence>
                  {on && (
                    <motion.span
                      key="hl"
                      className="accent-soft absolute inset-0 -z-10 rounded-xl"
                      initial={{ opacity: 0, scale: 0.96, y: 6 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.25 }}
                    />
                  )}
                </AnimatePresence>
                <t.icon size={18} className={on ? 'accent-fg' : 'group-hover:text-violet-400'} />
                {t.label}
              </button>
            )
          })}
        </nav>

        <div className="mt-auto flex items-center justify-between px-2">
          <span className="text-xs text-slate-400 dark:text-slate-500">practice · math-tools</span>
          {/* 皮肤切换:三个色点 */}
          <div className="flex items-center gap-1.5">
            {SKINS.map((s) => (
              <button
                key={s.id}
                className={cn(
                  'size-5 rounded-full p-[3px] transition hover:scale-110',
                  skin === s.id && 'ring-1 ring-slate-400/60 dark:ring-white/40',
                )}
                title={`${s.name} · ${s.hint}`}
                onClick={() => setSkin(s.id)}
              >
                <span className="block size-full rounded-full" style={{ background: s.dot }} />
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* 主内容 */}
      <main className="bg-scene relative h-full flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            className={pageClass[active]}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.22 }}
          >
            {active === 'home' && <HomeView onOpen={setActive} />}
            {active === 'curriculum' && <CurriculumView />}
            {active === 'matrix' && <MatrixView />}
            {active === 'plot' && <PlotView />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  )
}
