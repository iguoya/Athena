<script setup lang="ts">
import { computed, ref } from 'vue'
import { motion } from 'motion-v'
import { chapters, type Tool } from '../data/curriculum'
import { ChevronDown, Circle, CheckCircle2, Target, ListChecks } from 'lucide-vue-next'

const KEY = 'mt-curriculum-done'

const done = ref<Record<string, boolean>>(
  (() => {
    try {
      return JSON.parse(localStorage.getItem(KEY) ?? '{}')
    } catch {
      return {}
    }
  })(),
)

function key(chapterId: string, index: number): string {
  return `${chapterId}-${index}`
}

function toggle(chapterId: string, index: number) {
  const k = key(chapterId, index)
  done.value[k] = !done.value[k]
  localStorage.setItem(KEY, JSON.stringify(done.value))
}

const opened = ref<string | null>(chapters[0]?.id ?? null)

function chapterProgress(chapterId: string, count: number): number {
  let n = 0
  for (let i = 0; i < count; i++) if (done.value[key(chapterId, i)]) n++
  return n
}

const total = chapters.reduce((n, c) => n + c.items.length, 0)
const doneCount = computed(() =>
  chapters.reduce((n, c) => n + chapterProgress(c.id, c.items.length), 0),
)
const pct = computed(() => Math.round((doneCount.value / total) * 100))

const toolStyle: Record<Tool, string> = {
  GeoGebra: 'bg-violet-500/10 text-violet-600 dark:text-violet-300 ring-violet-400/30',
  Octave: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-300 ring-cyan-400/30',
  'Math Tools': 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 ring-emerald-400/30',
  理论: 'bg-slate-500/10 text-slate-500 dark:text-slate-300 ring-slate-400/30',
}
</script>

<template>
  <section>
    <!-- 头部:定位语 + 总进度 -->
    <motion.div
      :initial="{ opacity: 0, y: 16 }"
      :animate="{ opacity: 1, y: 0 }"
      :transition="{ duration: 0.5, ease: 'easeOut' }"
    >
      <p class="mb-2 flex items-center gap-2 text-xs font-medium tracking-widest text-violet-500 dark:text-violet-300/80">
        <ListChecks :size="14" /> CURRICULUM
      </p>
      <h1 class="font-display text-2xl font-bold">练习纲要</h1>
      <p class="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500 dark:text-slate-400">
        每个概念走三遍:<span class="font-medium text-slate-700 dark:text-slate-200">看一遍直觉、拖一遍图形、算一遍数值</span>。
        勾选存本机浏览器,进度只对自己负责。
      </p>

      <div class="card mt-5 flex items-center gap-4 p-4">
        <div class="grid size-11 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-400 text-white shadow-lg shadow-violet-500/25">
          <Target :size="20" />
        </div>
        <div class="min-w-0 flex-1">
          <div class="mb-1.5 flex items-baseline justify-between">
            <p class="text-sm font-medium">总进度</p>
            <p class="font-mono text-xs text-slate-400">{{ doneCount }} / {{ total }} · {{ pct }}%</p>
          </div>
          <div class="h-2 overflow-hidden rounded-full bg-slate-200/70 dark:bg-white/10">
            <div
              class="h-full rounded-full bg-gradient-to-r from-violet-500 via-fuchsia-500 to-cyan-400 transition-all duration-500 ease-out"
              :style="{ width: `${pct}%` }"
            />
          </div>
        </div>
      </div>
    </motion.div>

    <!-- 章节 -->
    <div class="mt-6 flex flex-col gap-3.5">
      <motion.div
        v-for="(c, ci) in chapters"
        :key="c.id"
        :initial="{ opacity: 0, y: 20 }"
        :animate="{ opacity: 1, y: 0 }"
        :transition="{ duration: 0.45, delay: 0.08 + ci * 0.06, ease: 'easeOut' }"
        class="card overflow-hidden"
      >
        <!-- 章头 -->
        <button
          class="flex w-full items-center gap-4 p-5 text-left transition hover:bg-slate-50/60 dark:hover:bg-white/[0.03]"
          @click="opened = opened === c.id ? null : c.id"
        >
          <span
            class="grid size-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br font-mono text-sm font-bold text-white shadow"
            :class="ci % 2 === 0 ? 'from-violet-500 to-fuchsia-400 shadow-violet-500/25' : 'from-cyan-400 to-emerald-400 shadow-cyan-400/25'"
          >{{ ci }}</span>
          <span class="min-w-0 flex-1">
            <span class="flex items-baseline gap-2">
              <span class="font-display text-base font-semibold">{{ c.title }}</span>
              <span class="font-mono text-[11px] tracking-wide text-slate-400">{{ c.en }}</span>
            </span>
            <span class="mt-0.5 block truncate text-xs text-slate-500 dark:text-slate-400">{{ c.goal }}</span>
          </span>
          <span class="shrink-0 font-mono text-[11px]" :class="chapterProgress(c.id, c.items.length) === c.items.length ? 'text-emerald-500' : 'text-slate-400'">
            {{ chapterProgress(c.id, c.items.length) }}/{{ c.items.length }}
          </span>
          <ChevronDown
            :size="17"
            class="shrink-0 text-slate-400 transition-transform duration-300"
            :class="opened === c.id ? 'rotate-180' : ''"
          />
        </button>

        <!-- 展开的练习项 -->
        <Transition name="pop">
          <div v-if="opened === c.id" class="border-t border-slate-200/70 px-5 pb-5 pt-4 dark:border-white/10">
            <p class="mb-4 flex items-start gap-2 rounded-xl bg-violet-500/5 px-3.5 py-2.5 text-xs leading-relaxed text-slate-600 ring-1 ring-violet-400/15 dark:text-slate-300">
              <Target :size="13" class="mt-0.5 shrink-0 text-violet-400" />
              本章目标:{{ c.goal }}
            </p>
            <ol class="flex flex-col gap-4">
              <li
                v-for="(it, ii) in c.items"
                :key="ii"
                class="flex gap-3"
                :class="done[key(c.id, ii)] ? 'opacity-55' : ''"
              >
                <button
                  class="mt-0.5 shrink-0 transition hover:scale-110 active:scale-90"
                  :title="done[key(c.id, ii)] ? '取消完成' : '标记完成'"
                  @click="toggle(c.id, ii)"
                >
                  <Transition name="pop" mode="out-in">
                    <CheckCircle2 v-if="done[key(c.id, ii)]" :size="19" class="text-emerald-500" />
                    <Circle v-else :size="19" class="text-slate-300 dark:text-slate-600" />
                  </Transition>
                </button>
                <div class="min-w-0 flex-1">
                  <p class="text-sm leading-relaxed" :class="done[key(c.id, ii)] ? 'line-through decoration-slate-400' : ''">
                    {{ it.point }}
                  </p>
                  <p class="mt-1.5 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                    <span class="mr-1 font-medium text-emerald-600 dark:text-emerald-400">验收</span>
                    {{ it.req }}
                  </p>
                  <p class="mt-2 flex flex-wrap gap-1.5">
                    <span
                      v-for="t in it.tools"
                      :key="t"
                      class="rounded-full px-2 py-0.5 font-mono text-[10px] ring-1"
                      :class="toolStyle[t]"
                    >{{ t }}</span>
                  </p>
                </div>
              </li>
            </ol>
          </div>
        </Transition>
      </motion.div>
    </div>
  </section>
</template>
