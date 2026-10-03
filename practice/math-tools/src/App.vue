<script setup lang="ts">
import { ref } from 'vue'
import { Home, Grid3x3, LineChart, Sun, Moon, Sigma } from 'lucide-vue-next'
import HomeView from './views/HomeView.vue'
import MatrixView from './views/MatrixView.vue'
import PlotView from './views/PlotView.vue'

type TabId = 'home' | 'matrix' | 'plot'

const tabs: { id: TabId; label: string; icon: typeof Home }[] = [
  { id: 'home', label: '首页', icon: Home },
  { id: 'matrix', label: '矩阵实验室', icon: Grid3x3 },
  { id: 'plot', label: '函数绘图', icon: LineChart },
]

const active = ref<TabId>('home')
const dark = ref(document.documentElement.classList.contains('dark'))

function toggleTheme() {
  dark.value = !dark.value
  document.documentElement.classList.toggle('dark', dark.value)
  localStorage.setItem('mt-theme', dark.value ? 'dark' : 'light')
}
</script>

<template>
  <div class="flex h-full">
    <!-- 侧栏 -->
    <aside class="relative z-10 flex w-60 shrink-0 flex-col border-r border-slate-200/70 bg-white/60 px-4 py-5 backdrop-blur-xl dark:border-white/10 dark:bg-white/[0.03]">
      <div class="mb-8 flex items-center gap-3 px-2">
        <div class="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-400 text-white shadow-lg shadow-violet-500/30">
          <Sigma :size="22" :stroke-width="2.5" />
        </div>
        <div>
          <p class="font-display text-sm font-semibold tracking-wide">数学工具</p>
          <p class="text-xs text-slate-500 dark:text-slate-400">Math Tools</p>
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
            <span
              v-if="active === t.id"
              class="absolute inset-0 -z-10 rounded-xl bg-gradient-to-r from-violet-500/15 to-cyan-400/10 ring-1 ring-violet-400/30"
            />
          </Transition>
          <component
            :is="t.icon"
            :size="18"
            :class="active === t.id ? 'text-violet-500 dark:text-violet-300' : 'group-hover:text-violet-400'"
          />
          {{ t.label }}
        </button>
      </nav>

      <div class="mt-auto flex items-center justify-between px-2">
        <span class="text-xs text-slate-400 dark:text-slate-500">practice · math-tools</span>
        <button
          class="grid size-9 place-items-center rounded-full text-slate-500 transition hover:rotate-12 hover:bg-slate-100 hover:text-violet-500 dark:text-slate-400 dark:hover:bg-white/10 dark:hover:text-cyan-300"
          title="切换亮/暗主题"
          @click="toggleTheme"
        >
          <Transition name="pop" mode="out-in">
            <Moon v-if="dark" :size="18" key="moon" />
            <Sun v-else :size="18" key="sun" />
          </Transition>
        </button>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="bg-scene relative h-full flex-1 overflow-y-auto">
      <Transition name="page" mode="out-in">
        <div v-if="active === 'home'" key="home" class="mx-auto max-w-5xl px-10 py-10">
          <HomeView @open="active = $event" />
        </div>
        <MatrixView v-else-if="active === 'matrix'" key="matrix" class="mx-auto max-w-5xl px-10 py-10" />
        <PlotView v-else key="plot" class="h-full" />
      </Transition>
    </main>
  </div>
</template>
