<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { create, all, type EvalFunction } from 'mathjs'
import { FunctionSquare, MousePointer2, ZoomIn } from 'lucide-vue-next'

const math = create(all, { number: 'number' })

const expr = ref('sin(x) * x')
const drawn = ref('sin(x) * x')
const parseError = ref('')
const wrap = ref<HTMLElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)

let compiled: EvalFunction | null = null
let ctx: CanvasRenderingContext2D | null = null
let raf = 0

// 视图状态:中心(数学坐标)与比例(px / 单位)
const view = { cx: 0, cy: 0, scale: 64 }
let dragging = false
let lastX = 0
let lastY = 0

const samples = ['sin(x)', 'x^2', 'exp(-x^2)', 'sin(x)/x', 'x * sin(x)', 'abs(x) - 2']

function compileExpr() {
  parseError.value = ''
  compiled = null
  const e = expr.value.trim()
  if (!e) return
  try {
    compiled = math.compile(e)
    compiled.evaluate({ x: 1 }) // 立即试算一次,暴露语法错误
    drawn.value = e
    requestRender()
  } catch (err) {
    parseError.value = err instanceof Error ? err.message : String(err)
  }
}

function niceStep(scale: number): number {
  const target = 90 / scale // 目标:每格约 90px
  const p = Math.pow(10, Math.floor(Math.log10(target)))
  for (const m of [1, 2, 5, 10]) {
    if (p * m >= target) return p * m
  }
  return p * 10
}

function render() {
  if (!ctx || !canvas.value) return
  const cv = canvas.value
  const w = cv.width / devicePixelRatio
  const h = cv.height / devicePixelRatio
  ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0)
  ctx.clearRect(0, 0, w, h)

  const x0 = view.cx - w / 2 / view.scale
  const x1 = view.cx + w / 2 / view.scale
  const y0 = view.cy - h / 2 / view.scale
  const y1 = view.cy + h / 2 / view.scale

  const sx = (mx: number) => (mx - view.cx) * view.scale + w / 2
  const sy = (my: number) => h / 2 - (my - view.cy) * view.scale

  // 网格
  const step = niceStep(view.scale)
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
  const tick = Math.abs(view.cy) < y1 - y0 ? 0 : view.cy
  void tick
  for (let gx = Math.ceil(x0 / step) * step; gx <= x1; gx += step) {
    if (Math.abs(gx) < 1e-12) continue
    ctx.fillText(String(Number(gx.toPrecision(4))), sx(gx) + 3, sy(0) + 14)
  }
  for (let gy = Math.ceil(y0 / step) * step; gy <= y1; gy += step) {
    if (Math.abs(gy) < 1e-12) continue
    ctx.fillText(String(Number(gy.toPrecision(4))), sx(0) + 5, sy(gy) - 4)
  }

  // 曲线(渐变描边)
  if (!compiled) return
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
      my = compiled.evaluate({ x: mx }) as number
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
}

function requestRender() {
  cancelAnimationFrame(raf)
  raf = requestAnimationFrame(render)
}

function resize() {
  const cv = canvas.value
  const el = wrap.value
  if (!cv || !el || !ctx) return
  const rect = el.getBoundingClientRect()
  cv.width = Math.max(1, Math.floor(rect.width * devicePixelRatio))
  cv.height = Math.max(1, Math.floor(rect.height * devicePixelRatio))
  cv.style.width = `${rect.width}px`
  cv.style.height = `${rect.height}px`
  requestRender()
}

function onPointerDown(e: PointerEvent) {
  dragging = true
  lastX = e.clientX
  lastY = e.clientY
  ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  if (!dragging) return
  view.cx -= (e.clientX - lastX) / view.scale
  view.cy += (e.clientY - lastY) / view.scale
  lastX = e.clientX
  lastY = e.clientY
  requestRender()
}

function onPointerUp() {
  dragging = false
}

function onWheel(e: WheelEvent) {
  e.preventDefault()
  const cv = canvas.value
  if (!cv) return
  const rect = cv.getBoundingClientRect()
  // 缩放时保持鼠标下的数学点不动
  const mx = view.cx + (e.clientX - rect.left - rect.width / 2) / view.scale
  const my = view.cy - (e.clientY - rect.top - rect.height / 2) / view.scale
  const factor = Math.exp(-e.deltaY * 0.0012)
  const next = Math.min(4096, Math.max(4, view.scale * factor))
  view.cx = mx - (mx - view.cx) * (next / view.scale)
  view.cy = my - (my - view.cy) * (next / view.scale)
  view.scale = next
  requestRender()
}

let ro: ResizeObserver | null = null

onMounted(() => {
  ctx = canvas.value!.getContext('2d')
  ro = new ResizeObserver(resize)
  if (wrap.value) ro.observe(wrap.value)
  resize()
  compileExpr()
  window.addEventListener('keydown', onKey)
})

function onKey(e: KeyboardEvent) {
  if (e.key === 'Enter' && (e.target as HTMLElement)?.tagName === 'INPUT') compileExpr()
}

onBeforeUnmount(() => {
  ro?.disconnect()
  cancelAnimationFrame(raf)
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <section class="relative flex h-full flex-col">
    <!-- 顶部工具条 -->
    <div class="z-10 mx-auto mt-6 w-full max-w-3xl px-8">
      <div class="card flex items-center gap-2 p-2.5 pl-4">
        <FunctionSquare :size="17" class="accent-fg shrink-0" />
        <input
          v-model="expr"
          class="w-full bg-transparent font-mono text-[15px] outline-none placeholder:text-slate-400"
          placeholder="输入 f(x),如 sin(x)/x,回车绘制"
          spellcheck="false"
          @keydown.enter="compileExpr"
        />
        <button
          class="shrink-0 rounded-lg accent-gradient accent-glow px-4 py-1.5 text-sm font-medium text-white transition hover:brightness-110 active:scale-95"
          @click="compileExpr"
        >绘制</button>
      </div>
      <div class="mt-2.5 flex flex-wrap items-center gap-2">
        <button
          v-for="s in samples"
          :key="s"
          class="rounded-full border px-3 py-1 font-mono text-xs transition hover:-translate-y-0.5"
          :class="drawn === s
            ? 'accent-soft accent-fg'
            : 'border-slate-200 text-slate-500 hover:border-slate-300 dark:border-white/10 dark:text-slate-400'"
          @click="expr = s; compileExpr()"
        >{{ s }}</button>
        <span class="ml-auto flex items-center gap-3 text-[11px] text-slate-400 dark:text-slate-500">
          <span class="flex items-center gap-1"><MousePointer2 :size="12" /> 拖拽平移</span>
          <span class="flex items-center gap-1"><ZoomIn :size="12" /> 滚轮缩放</span>
        </span>
      </div>
      <p v-if="parseError" class="mt-2 rounded-lg bg-rose-500/10 px-3 py-1.5 text-sm text-rose-500">
        {{ parseError }}
      </p>
    </div>

    <!-- 画布 -->
    <div ref="wrap" class="relative mt-4 min-h-0 flex-1">
      <canvas
        ref="canvas"
        class="absolute inset-0 touch-none"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
        @wheel="onWheel"
      />
      <!-- 当前函数角标 -->
      <Transition name="pop">
        <p
          v-if="drawn && !parseError"
          :key="drawn"
          class="absolute left-6 top-4 rounded-lg border border-slate-200/60 bg-white/70 px-3 py-1.5 font-mono text-sm backdrop-blur dark:border-white/10 dark:bg-black/30"
        >
          f(x) =
          <span class="text-gradient font-semibold">
            {{ drawn }}
          </span>
        </p>
      </Transition>
    </div>
  </section>
</template>
