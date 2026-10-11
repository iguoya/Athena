import { useCallback, useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { create, all, type EvalFunction } from 'mathjs'
import { FunctionSquare, MousePointer2, ZoomIn } from 'lucide-react'
import { cn } from '@/lib/utils'

const math = create(all, { number: 'number' })

const samples = ['sin(x)', 'x^2', 'exp(-x^2)', 'sin(x)/x', 'x * sin(x)', 'abs(x) - 2']

function niceStep(scale: number): number {
  const target = 90 / scale // 目标:每格约 90px
  const p = Math.pow(10, Math.floor(Math.log10(target)))
  for (const m of [1, 2, 5, 10]) {
    if (p * m >= target) return p * m
  }
  return p * 10
}

export default function PlotView() {
  const [expr, setExpr] = useState('sin(x) * x')
  const [drawn, setDrawn] = useState('sin(x) * x')
  const [parseError, setParseError] = useState('')
  const wrap = useRef<HTMLDivElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)

  // 画布状态都放 ref:拖拽与缩放每帧改它们,不该触发 React 重渲染。
  const compiled = useRef<EvalFunction | null>(null)
  const raf = useRef(0)
  // 视图状态:中心(数学坐标)与比例(px / 单位)
  const view = useRef({ cx: 0, cy: 0, scale: 64 })
  const drag = useRef({ on: false, x: 0, y: 0 })

  const render = useCallback(() => {
    const cv = canvas.current
    const ctx = cv?.getContext('2d')
    if (!cv || !ctx) return
    const v = view.current
    const w = cv.width / devicePixelRatio
    const h = cv.height / devicePixelRatio
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0)
    ctx.clearRect(0, 0, w, h)

    const x0 = v.cx - w / 2 / v.scale
    const x1 = v.cx + w / 2 / v.scale
    const y0 = v.cy - h / 2 / v.scale
    const y1 = v.cy + h / 2 / v.scale

    const sx = (mx: number) => (mx - v.cx) * v.scale + w / 2
    const sy = (my: number) => h / 2 - (my - v.cy) * v.scale

    // 网格
    const step = niceStep(v.scale)
    const isDark = document.documentElement.classList.contains('dark')
    ctx.strokeStyle = isDark ? 'rgba(148,163,184,0.10)' : 'rgba(100,116,139,0.12)'
    ctx.lineWidth = 1
    ctx.beginPath()
    for (let gx = Math.ceil(x0 / step) * step; gx <= x1; gx += step) {
      ctx.moveTo(sx(gx), 0)
      ctx.lineTo(sx(gx), h)
    }
    for (let gy = Math.ceil(y0 / step) * step; gy <= y1; gy += step) {
      ctx.moveTo(0, sy(gy))
      ctx.lineTo(w, sy(gy))
    }
    ctx.stroke()

    // 坐标轴 + 刻度
    ctx.strokeStyle = isDark ? 'rgba(148,163,184,0.45)' : 'rgba(71,85,105,0.5)'
    ctx.lineWidth = 1.4
    ctx.beginPath()
    ctx.moveTo(sx(0), 0)
    ctx.lineTo(sx(0), h)
    ctx.moveTo(0, sy(0))
    ctx.lineTo(w, sy(0))
    ctx.stroke()

    ctx.fillStyle = isDark ? 'rgba(148,163,184,0.7)' : 'rgba(71,85,105,0.75)'
    ctx.font = '11px "JetBrains Mono Variable", monospace'
    for (let gx = Math.ceil(x0 / step) * step; gx <= x1; gx += step) {
      if (Math.abs(gx) < 1e-12) continue
      ctx.fillText(String(Number(gx.toPrecision(4))), sx(gx) + 3, sy(0) + 14)
    }
    for (let gy = Math.ceil(y0 / step) * step; gy <= y1; gy += step) {
      if (Math.abs(gy) < 1e-12) continue
      ctx.fillText(String(Number(gy.toPrecision(4))), sx(0) + 5, sy(gy) - 4)
    }

    // 曲线(渐变描边)
    const fn = compiled.current
    if (!fn) return
    const grad = ctx.createLinearGradient(0, 0, w, 0)
    grad.addColorStop(0, '#8b5cf6')
    grad.addColorStop(0.5, '#d946ef')
    grad.addColorStop(1, '#22d3ee')
    ctx.strokeStyle = grad
    ctx.lineWidth = 2.4
    ctx.lineJoin = 'round'
    ctx.beginPath()
    let pen = false
    for (let px = 0; px <= w; px += 2) {
      const mx = x0 + (px / w) * (x1 - x0)
      let my: number
      try {
        my = fn.evaluate({ x: mx }) as number
      } catch {
        pen = false
        continue
      }
      if (typeof my !== 'number' || !Number.isFinite(my) || Math.abs(my) > 1e8) {
        pen = false
        continue
      }
      const py = sy(my)
      if (!pen) {
        ctx.moveTo(px, py)
        pen = true
      } else {
        ctx.lineTo(px, py)
      }
    }
    ctx.stroke()
  }, [])

  const requestRender = useCallback(() => {
    cancelAnimationFrame(raf.current)
    raf.current = requestAnimationFrame(render)
  }, [render])

  const compileExpr = useCallback(
    (source: string) => {
      setParseError('')
      compiled.current = null
      const e = source.trim()
      if (!e) return
      try {
        const fn = math.compile(e)
        fn.evaluate({ x: 1 }) // 立即试算一次,暴露语法错误
        compiled.current = fn
        setDrawn(e)
        requestRender()
      } catch (err) {
        setParseError(err instanceof Error ? err.message : String(err))
      }
    },
    [requestRender],
  )

  // 挂载:建立尺寸观察、滚轮监听,并画出初始表达式。
  useEffect(() => {
    const cv = canvas.current
    const el = wrap.current
    if (!cv || !el) return

    const resize = () => {
      const rect = el.getBoundingClientRect()
      cv.width = Math.max(1, Math.floor(rect.width * devicePixelRatio))
      cv.height = Math.max(1, Math.floor(rect.height * devicePixelRatio))
      cv.style.width = `${rect.width}px`
      cv.style.height = `${rect.height}px`
      requestRender()
    }
    const ro = new ResizeObserver(resize)
    ro.observe(el)
    resize()

    // React 的 onWheel 是被动监听,拿不到 preventDefault(页面会跟着滚),所以直接挂原生非被动监听。
    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      const v = view.current
      const rect = cv.getBoundingClientRect()
      // 缩放时保持鼠标下的数学点不动
      const mx = v.cx + (e.clientX - rect.left - rect.width / 2) / v.scale
      const my = v.cy - (e.clientY - rect.top - rect.height / 2) / v.scale
      const factor = Math.exp(-e.deltaY * 0.0012)
      const next = Math.min(4096, Math.max(4, v.scale * factor))
      v.cx = mx - (mx - v.cx) * (next / v.scale)
      v.cy = my - (my - v.cy) * (next / v.scale)
      v.scale = next
      requestRender()
    }
    cv.addEventListener('wheel', onWheel, { passive: false })

    compileExpr('sin(x) * x')

    return () => {
      ro.disconnect()
      cancelAnimationFrame(raf.current)
      cv.removeEventListener('wheel', onWheel)
    }
  }, [compileExpr, requestRender])

  function onPointerDown(e: React.PointerEvent<HTMLCanvasElement>) {
    drag.current = { on: true, x: e.clientX, y: e.clientY }
    e.currentTarget.setPointerCapture(e.pointerId)
  }

  function onPointerMove(e: React.PointerEvent<HTMLCanvasElement>) {
    const d = drag.current
    if (!d.on) return
    const v = view.current
    v.cx -= (e.clientX - d.x) / v.scale
    v.cy += (e.clientY - d.y) / v.scale
    d.x = e.clientX
    d.y = e.clientY
    requestRender()
  }

  function onPointerUp() {
    drag.current.on = false
  }

  return (
    <section className="relative flex h-full flex-col">
      {/* 顶部工具条 */}
      <div className="z-10 mx-auto mt-6 w-full max-w-3xl px-8">
        <div className="card flex items-center gap-2 p-2.5 pl-4">
          <FunctionSquare size={17} className="accent-fg shrink-0" />
          <input
            value={expr}
            onChange={(e) => setExpr(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && compileExpr(expr)}
            className="w-full bg-transparent font-mono text-[15px] outline-none placeholder:text-slate-400"
            placeholder="输入 f(x),如 sin(x)/x,回车绘制"
            spellCheck={false}
          />
          <button
            className="accent-gradient accent-glow shrink-0 rounded-lg px-4 py-1.5 text-sm font-medium text-white transition hover:brightness-110 active:scale-95"
            onClick={() => compileExpr(expr)}
          >
            绘制
          </button>
        </div>
        <div className="mt-2.5 flex flex-wrap items-center gap-2">
          {samples.map((s) => (
            <button
              key={s}
              className={cn(
                'rounded-full border px-3 py-1 font-mono text-xs transition hover:-translate-y-0.5',
                drawn === s
                  ? 'accent-soft accent-fg'
                  : 'border-slate-200 text-slate-500 hover:border-slate-300 dark:border-white/10 dark:text-slate-400',
              )}
              onClick={() => {
                setExpr(s)
                compileExpr(s)
              }}
            >
              {s}
            </button>
          ))}
          <span className="ml-auto flex items-center gap-3 text-[11px] text-slate-400 dark:text-slate-500">
            <span className="flex items-center gap-1">
              <MousePointer2 size={12} /> 拖拽平移
            </span>
            <span className="flex items-center gap-1">
              <ZoomIn size={12} /> 滚轮缩放
            </span>
          </span>
        </div>
        {parseError && (
          <p className="mt-2 rounded-lg bg-rose-500/10 px-3 py-1.5 text-sm text-rose-500">
            {parseError}
          </p>
        )}
      </div>

      {/* 画布 */}
      <div ref={wrap} className="relative mt-4 min-h-0 flex-1">
        <canvas
          ref={canvas}
          className="absolute inset-0 touch-none"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        />
        {/* 当前函数角标 */}
        <AnimatePresence>
          {drawn && !parseError && (
            <motion.p
              key={drawn}
              initial={{ opacity: 0, scale: 0.96, y: 6 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="absolute left-6 top-4 rounded-lg border border-slate-200/60 bg-white/70 px-3 py-1.5 font-mono text-sm backdrop-blur dark:border-white/10 dark:bg-black/30"
            >
              f(x) = <span className="text-gradient font-semibold">{drawn}</span>
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </section>
  )
}
