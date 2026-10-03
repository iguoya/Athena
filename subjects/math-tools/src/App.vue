<script setup lang="ts">
import { ref } from 'vue'
import { Home, Grid3x3, LineChart, BookOpen, Sigma } from 'lucide-vue-next'
import HomeView from './views/HomeView.vue'
import MatrixView from './views/MatrixView.vue'
import PlotView from './views/PlotView.vue'
import CurriculumView from './views/CurriculumView.vue'
import { SKINS, applySkin, currentSkin, type SkinId } from './theme'

type TabId = 'home' | 'curriculum' | 'matrix' | 'plot'

const tabs: { id: TabId; label: string; icon: typeof Home }[] = [
  { id: 'home', label: '首页', icon: Home },
  { id: 'curriculum', label: '练习纲要', icon: BookOpen },
  { id: 'matrix', label: '矩阵实验室', icon: Grid3x3 },
  { id: 'plot', label: '函数绘图', icon: LineChart },
]

const active = ref<TabId>('home')
const skin = ref<SkinId>(currentSkin())

function setSkin(id: SkinId) {
  skin.value = id
  applySkin(id)
}
</script>

<template>
  <div class="flex h-full">
    <!-- 侧栏 -->
    <aside class="relative z-10 flex w-60 shrink-0 flex-col border-r px-4 py-5 backdrop-blur-xl" style="border-color: var(--tk-line); background: color-mix(in oklab, var(--tk-surface) 60%, transparent)">
      <div class="mb-8 flex items-center gap-3 px-2">
        <div class="accent-gradient accent-glow grid size-10 place-items-center rounded-xl text-white">
          <Sigma :size="22" :stroke-width="2.5" />
        </div>
        <div>
          <p class="tk-display text-sm font-semibold tracking-wide">数学工具</p>
          <p class="text-xs" style="color: var(--tk-muted)">Math Tools</p>
        </div>
      </div>

      <nav class="flex flex-col gap-1">
        <button
          v-for="t in tabs"
          :key="t.id"
          class="group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors"
          :class="active === t.id
            ? 'text-slate-900 dark:text-white'
            : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200'"
          @click="active = t.id"
        >
          <Transition name="pop">
            <span v-if="active === t.id" class="accent-soft absolute inset-0 -z-10 rounded-xl" />
          </Transition>
          <component
            :is="t.icon"
            :size="18"
            :class="active === t.id ? 'accent-fg' : 'group-hover:text-violet-400'"
          />
          {{ t.label }}
        </button>
      </nav>

      <div class="mt-auto flex items-center justify-between px-2">
        <span class="text-xs text-slate-400 dark:text-slate-500">practice · math-tools</span>
        <!-- 皮肤切换:三个色点 -->
        <div class="flex items-center gap-1.5">
          <button
            v-for="s in SKINS"
            :key="s.id"
            class="size-5 rounded-full p-[3px] transition hover:scale-110"
            :class="skin === s.id ? 'ring-1 ring-slate-400/60 dark:ring-white/40' : ''"
            :title="`${s.name} · ${s.hint}`"
            @click="setSkin(s.id)"
          >
            <span class="block size-full rounded-full" :style="{ background: s.dot }" />
          </button>
        </div>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="bg-scene relative h-full flex-1 overflow-y-auto">
      <Transition name="page" mode="out-in">
        <div v-if="active === 'home'" key="home" class="mx-auto max-w-5xl px-10 py-10">
          <HomeView @open="active = $event" />
        </div>
        <CurriculumView v-else-if="active === 'curriculum'" key="curriculum" class="mx-auto max-w-4xl px-10 py-10" />
        <MatrixView v-else-if="active === 'matrix'" key="matrix" class="mx-auto max-w-5xl px-10 py-10" />
        <PlotView v-else key="plot" class="h-full" />
      </Transition>
    </main>
  </div>
</template>
