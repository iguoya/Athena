<script setup lang="ts">
import { motion } from 'motion-v'
import { Grid3x3, LineChart, BookOpen, ArrowRight, Sparkles } from 'lucide-vue-next'

const emit = defineEmits<{ open: [tab: 'curriculum' | 'matrix' | 'plot'] }>()

const tools = [
  {
    id: 'curriculum' as const,
    name: '练习纲要',
    en: 'Curriculum',
    desc: '七章二十八条练习:看一遍直觉、拖一遍图形、算一遍数值,勾选打卡自己的进度。',
    icon: BookOpen,
    accent: 'from-amber-400 to-orange-500',
    glow: 'shadow-orange-400/25',
    wide: true,
  },
  {
    id: 'matrix' as const,
    name: '矩阵实验室',
    en: 'Matrix Lab',
    desc: '行列式、迹、逆、转置、秩、幂与特征值,输入即算,结果逐项呈现。',
    icon: Grid3x3,
    accent: 'from-violet-500 to-fuchsia-400',
    glow: 'shadow-violet-500/25',
    wide: false,
  },
  {
    id: 'plot' as const,
    name: '函数绘图',
    en: 'Function Plot',
    desc: '输入 f(x) 立即成图,渐变描边;拖拽平移,滚轮缩放,坐标自适应网格。',
    icon: LineChart,
    accent: 'from-cyan-400 to-emerald-400',
    glow: 'shadow-cyan-400/25',
    wide: false,
  },
]
</script>

<template>
  <section>
    <!-- Hero -->
    <motion.div
      :initial="{ opacity: 0, y: 18 }"
      :animate="{ opacity: 1, y: 0 }"
      :transition="{ duration: 0.55, ease: 'easeOut' }"
    >
      <p class="mb-3 flex items-center gap-2 text-xs font-medium tracking-widest accent-fg">
        <Sparkles :size="14" /> PRACTICE · MATH TOOLS
      </p>
      <h1 class="tk-display text-4xl font-bold leading-tight tracking-tight">
        把<span class="text-gradient">数学</span>握在手里的练习本
      </h1>
      <p class="mt-3 max-w-xl text-sm leading-relaxed text-slate-500 dark:text-slate-400">
        从纲要出发,每个工具都即刻可算、所见即所得——先有能跑的东西,再谈别的。
      </p>
    </motion.div>

    <!-- 工具卡片 -->
    <div class="mt-10 grid grid-cols-2 gap-5">
      <motion.button
        v-for="(t, i) in tools"
        :key="t.id"
        :initial="{ opacity: 0, y: 28 }"
        :animate="{ opacity: 1, y: 0 }"
        :transition="{ duration: 0.5, delay: 0.12 + i * 0.1, ease: 'easeOut' }"
        class="card tool-card tape group relative overflow-hidden p-6 text-left transition-all duration-300
          hover:-translate-y-1.5 hover:shadow-xl dark:hover:bg-white/[0.06]"
        :class="[`hover:shadow-2xl ${t.glow}`, t.wide ? 'col-span-2' : '']"
        @click="emit('open', t.id)"
      >
        <!-- hover 光斑 -->
        <span class="pointer-events-none absolute -right-16 -top-16 size-40 rounded-full bg-gradient-to-br opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-25" :class="t.accent" />
        <div class="flex items-start gap-5">
          <div class="grid size-12 shrink-0 place-items-center rounded-xl bg-gradient-to-br text-white shadow-lg transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-3" :class="[t.accent, t.glow]">
            <component :is="t.icon" :size="24" />
          </div>
          <div class="min-w-0">
            <p class="tk-display text-lg font-semibold">{{ t.name }}
              <span class="ml-1.5 font-mono text-[11px] font-normal tracking-wider text-slate-400">{{ t.en }}</span>
            </p>
            <p class="mt-1.5 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{{ t.desc }}</p>
            <p class="mt-3 flex items-center gap-1.5 text-sm font-medium accent-fg opacity-0 transition-all duration-300 group-hover:translate-x-1 group-hover:opacity-100">
              打开 <ArrowRight :size="15" />
            </p>
          </div>
        </div>
      </motion.button>
    </div>

    <!-- 装饰公式行 -->
    <motion.p
      :initial="{ opacity: 0 }"
      :animate="{ opacity: 1 }"
      :transition="{ delay: 0.5, duration: 0.8 }"
      class="formula mt-12 font-mono text-xs tracking-wide text-slate-400 dark:text-slate-600"
    >
      e<sup>iπ</sup> + 1 = 0 &nbsp;·&nbsp; ∇·B = 0 &nbsp;·&nbsp; A = PDP⁻¹ &nbsp;·&nbsp; ∫<sub>a</sub><sup>b</sup> f′(x)dx = f(b) − f(a)
    </motion.p>
  </section>
</template>
