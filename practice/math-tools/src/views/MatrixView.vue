<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { create, all } from 'mathjs'
import { Play, RotateCcw } from 'lucide-vue-next'

const math = create(all, { number: 'number' })

type Op = 'det' | 'trace' | 'inv' | 'transpose' | 'rank' | 'square' | 'eig'
type Result = { label: string; value: string }

const size = ref<2 | 3>(2)
const cells = reactive<(number | string)[][]>([
  [2, 1, 0],
  [1, 3, 0],
  [0, 0, 1],
])
const results = ref<Result[]>([])
const error = ref('')

const activeMatrix = computed<(number | string)[][]>(() =>
  cells.slice(0, size.value).map(row => row.slice(0, size.value)),
)

const ops: { id: Op; label: string; main?: boolean }[] = [
  { id: 'det', label: '行列式' },
  { id: 'trace', label: '迹' },
  { id: 'inv', label: '逆' },
  { id: 'transpose', label: '转置' },
  { id: 'rank', label: '秩' },
  { id: 'square', label: 'A²' },
  { id: 'eig', label: '特征值', main: true },
]

function setSize(n: 2 | 3) {
  size.value = n
  results.value = []
  error.value = ''
}

function reset() {
  const d = size.value === 2 ? [2, 1, 1, 3] : [2, 1, 0, 1, 3, 0, 0, 0, 1]
  for (let i = 0; i < size.value; i++)
    for (let j = 0; j < size.value; j++) cells[i][j] = d[i * size.value + j]
  results.value = []
  error.value = ''
}

/** 数值秩:行阶梯消元 + 容差判零 */
function rank(m: number[][]): number {
  const a = m.map(r => [...r])
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
  return m.map(r => `[${r.map(fmt).join(', ')}]`).join('\n')
}

function run(op: Op) {
  error.value = ''
  const label = ops.find(o => o.id === op)!.label
  try {
    const m = activeMatrix.value.map(row =>
      row.map(v => {
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
    results.value = [{ label, value }, ...results.value]
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}
</script>

<template>
  <section>
    <h1 class="font-display text-2xl font-bold">矩阵实验室</h1>
    <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">输入矩阵,点算子即算;最新结果排在最前。</p>

    <div class="mt-6 flex flex-wrap items-center gap-3">
      <div class="flex rounded-xl border border-slate-200 bg-white/70 p-1 text-sm dark:border-white/10 dark:bg-white/5">
        <button
          v-for="n in ([2, 3] as const)"
          :key="n"
          class="rounded-lg px-4 py-1.5 font-mono transition"
          :class="size === n
            ? 'bg-gradient-to-r from-violet-500 to-fuchsia-400 text-white shadow'
            : 'text-slate-500 hover:text-slate-800 dark:text-slate-400'"
          @click="setSize(n)"
        >{{ n }}×{{ n }}</button>
      </div>
      <button
        class="ml-auto flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-1.5 text-sm text-slate-500 transition hover:border-slate-300 hover:text-slate-700 dark:border-white/10 dark:text-slate-400 dark:hover:bg-white/5"
        @click="reset"
      >
        <RotateCcw :size="14" /> 重置
      </button>
    </div>

    <div class="mt-5 grid grid-cols-[minmax(0,5fr)_minmax(0,4fr)] gap-6">
      <!-- 输入 -->
      <div class="card p-6">
        <div
          class="mx-auto grid w-max gap-2"
          :style="{ gridTemplateColumns: `repeat(${size}, minmax(0, 1fr))` }"
        >
          <template v-for="i in size" :key="`r${i}`">
            <input
              v-for="j in size"
              :key="`c${j}`"
              v-model.number="cells[i - 1][j - 1]"
              class="field w-20 text-center text-lg"
              :aria-label="`第${i}行第${j}列`"
            />
          </template>
        </div>
        <p class="mt-5 text-center text-xs text-slate-400 dark:text-slate-500">
          支持整数与小数;修改后重新点算子即可。
        </p>
        <p v-if="error" class="mt-3 rounded-lg bg-rose-500/10 px-3 py-2 text-center text-sm text-rose-500">
          {{ error }}
        </p>
      </div>

      <!-- 算子 -->
      <div class="card flex flex-col p-6">
        <p class="mb-4 text-sm font-medium text-slate-500 dark:text-slate-400">算子</p>
        <div class="grid grid-cols-2 gap-2.5">
          <button
            v-for="op in ops"
            :key="op.id"
            class="flex items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition active:scale-95"
            :class="op.main
              ? 'col-span-2 bg-gradient-to-r from-violet-500 to-cyan-400 text-white shadow-lg shadow-violet-500/25 hover:brightness-110'
              : 'border border-slate-200 bg-white/60 hover:border-violet-300 hover:text-violet-600 dark:border-white/10 dark:bg-white/5 dark:hover:border-violet-400/40 dark:hover:text-violet-300'"
            @click="run(op.id)"
          >
            <Play :size="13" />
            {{ op.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- 结果 -->
    <TransitionGroup name="pop" tag="div" class="mt-6 grid grid-cols-2 gap-4">
      <div v-for="(r, i) in results" :key="`${r.label}-${i}`" class="card p-5">
        <p class="mb-2 flex items-center gap-2 text-xs font-medium tracking-wide text-slate-400">
          <span class="size-1.5 rounded-full bg-emerald-400" />
          {{ r.label }}
        </p>
        <p class="whitespace-pre-wrap font-mono text-[15px] leading-relaxed">{{ r.value }}</p>
      </div>
    </TransitionGroup>
  </section>
</template>
