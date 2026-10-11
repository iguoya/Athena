import { useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { create, all } from 'mathjs'
import { Play, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'

const math = create(all, { number: 'number' })

type Op = 'det' | 'trace' | 'inv' | 'transpose' | 'rank' | 'square' | 'eig'
type Result = { id: number; label: string; value: string }

const ops: { id: Op; label: string; main?: boolean }[] = [
  { id: 'det', label: '行列式' },
  { id: 'trace', label: '迹' },
  { id: 'inv', label: '逆' },
  { id: 'transpose', label: '转置' },
  { id: 'rank', label: '秩' },
  { id: 'square', label: 'A²' },
  { id: 'eig', label: '特征值', main: true },
]

// 输入格保留原始文本(如正在键入的 "1."),点算子时才转成数字。
const INITIAL_CELLS = [
  ['2', '1', '0'],
  ['1', '3', '0'],
  ['0', '0', '1'],
]

/** 数值秩:行阶梯消元 + 容差判零 */
function rank(m: number[][]): number {
  const a = m.map((r) => [...r])
  const rows = a.length
  const cols = a[0].length
  let r = 0
  for (let c = 0; c < cols && r < rows; c++) {
    let p = r
    for (let i = r + 1; i < rows; i++) if (Math.abs(a[i][c]) > Math.abs(a[p][c])) p = i
    if (Math.abs(a[p][c]) < 1e-10) continue
    ;[a[r], a[p]] = [a[p], a[r]]
    for (let i = r + 1; i < rows; i++) {
      const f = a[i][c] / a[r][c]
      for (let j = c; j < cols; j++) a[i][j] -= f * a[r][j]
    }
    r++
  }
  return r
}

function fmt(v: unknown): string {
  if (typeof v === 'number') {
    if (Math.abs(v) < 1e-12) return '0'
    return String(Number(v.toPrecision(6)))
  }
  if (Array.isArray(v)) return `[${v.map(fmt).join(', ')}]`
  return String(v)
}

function fmtMatrix(m: number[][]): string {
  return m.map((r) => `[${r.map(fmt).join(', ')}]`).join('\n')
}

export default function MatrixView() {
  const [size, setSize] = useState<2 | 3>(2)
  const [cells, setCells] = useState<string[][]>(INITIAL_CELLS)
  const [results, setResults] = useState<Result[]>([])
  const [error, setError] = useState('')
  const nextId = useRef(0)

  function changeSize(n: 2 | 3) {
    setSize(n)
    setResults([])
    setError('')
  }

  function reset() {
    const d = size === 2 ? [2, 1, 1, 3] : [2, 1, 0, 1, 3, 0, 0, 0, 1]
    setCells((prev) =>
      prev.map((row, i) =>
        row.map((cell, j) => (i < size && j < size ? String(d[i * size + j]) : cell)),
      ),
    )
    setResults([])
    setError('')
  }

  function setCell(i: number, j: number, value: string) {
    setCells((prev) => prev.map((row, r) => (r === i ? row.map((c, k) => (k === j ? value : c)) : row)))
  }

  function run(op: Op) {
    setError('')
    const label = ops.find((o) => o.id === op)!.label
    try {
      const m = cells.slice(0, size).map((row) =>
        row.slice(0, size).map((v) => {
          const n = Number(v)
          if (!Number.isFinite(n)) throw new Error('矩阵里有空项或非数项')
          return n
        }),
      )
      let value: string
      switch (op) {
        case 'det':
          value = fmt(math.det(m))
          break
        case 'trace':
          value = fmt(math.trace(m))
          break
        case 'transpose':
          value = fmtMatrix(math.transpose(m) as number[][])
          break
        case 'rank':
          value = String(rank(m))
          break
        case 'square':
          value = fmtMatrix(math.multiply(m, m) as number[][])
          break
        case 'inv':
          value = fmtMatrix(math.inv(m) as number[][])
          break
        case 'eig': {
          const vals = math.eigs(m).values
          value = Array.isArray(vals) ? vals.map(fmt).join(', ') : fmt(vals)
          break
        }
      }
      setResults((prev) => [{ id: nextId.current++, label, value }, ...prev])
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  return (
    <section>
      <h1 className="tk-display text-2xl font-bold">矩阵实验室</h1>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        输入矩阵,点算子即算;最新结果排在最前。
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <div className="flex rounded-xl border border-slate-200 bg-white/70 p-1 text-sm dark:border-white/10 dark:bg-white/5">
          {([2, 3] as const).map((n) => (
            <button
              key={n}
              className={cn(
                'rounded-lg px-4 py-1.5 font-mono transition',
                size === n
                  ? 'accent-gradient text-white shadow'
                  : 'text-slate-500 hover:text-slate-800 dark:text-slate-400',
              )}
              onClick={() => changeSize(n)}
            >
              {n}×{n}
            </button>
          ))}
        </div>
        <button
          className="ml-auto flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-1.5 text-sm text-slate-500 transition hover:border-slate-300 hover:text-slate-700 dark:border-white/10 dark:text-slate-400 dark:hover:bg-white/5"
          onClick={reset}
        >
          <RotateCcw size={14} /> 重置
        </button>
      </div>

      <div className="mt-5 grid grid-cols-[minmax(0,5fr)_minmax(0,4fr)] gap-6">
        {/* 输入 */}
        <div className="card p-6">
          <div
            className="mx-auto grid w-max gap-2"
            style={{ gridTemplateColumns: `repeat(${size}, minmax(0, 1fr))` }}
          >
            {Array.from({ length: size }, (_, i) =>
              Array.from({ length: size }, (_, j) => (
                <input
                  key={`${i}-${j}`}
                  value={cells[i][j]}
                  onChange={(e) => setCell(i, j, e.target.value)}
                  className="field w-20 text-center text-lg"
                  aria-label={`第${i + 1}行第${j + 1}列`}
                />
              )),
            )}
          </div>
          <p className="mt-5 text-center text-xs text-slate-400 dark:text-slate-500">
            支持整数与小数;修改后重新点算子即可。
          </p>
          {error && (
            <p className="mt-3 rounded-lg bg-rose-500/10 px-3 py-2 text-center text-sm text-rose-500">
              {error}
            </p>
          )}
        </div>

        {/* 算子 */}
        <div className="card flex flex-col p-6">
          <p className="mb-4 text-sm font-medium text-slate-500 dark:text-slate-400">算子</p>
          <div className="grid grid-cols-2 gap-2.5">
            {ops.map((op) => (
              <button
                key={op.id}
                className={cn(
                  'flex items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition active:scale-95',
                  op.main
                    ? 'accent-gradient accent-glow col-span-2 text-white hover:brightness-110'
                    : 'hover:accent-fg border border-slate-200 bg-white/60 hover:border-slate-300 dark:border-white/10 dark:bg-white/5 dark:hover:border-white/25',
                )}
                onClick={() => run(op.id)}
              >
                <Play size={13} />
                {op.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 结果 */}
      <div className="mt-6 grid grid-cols-2 gap-4">
        <AnimatePresence initial={false}>
          {results.map((r) => (
            <motion.div
              key={r.id}
              layout
              initial={{ opacity: 0, scale: 0.96, y: 6 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="card p-5"
            >
              <p className="mb-2 flex items-center gap-2 text-xs font-medium tracking-wide text-slate-400">
                <span className="size-1.5 rounded-full bg-emerald-400" />
                {r.label}
              </p>
              <p className="whitespace-pre-wrap font-mono text-[15px] leading-relaxed">{r.value}</p>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </section>
  )
}
