<script setup lang="ts">
// 首页:考试事实、续读、课程总览与真题/战况入口。
import { onMounted, ref } from "vue";
import { motion } from "motion-v";
import { ArrowRight, ScrollText, Gauge, Target, CalendarClock, BookOpen } from "lucide-vue-next";
import { course, allSections, masteryOf } from "../content";
import { attemptsSummary, loadSetting } from "../db";
import type { KpSummary } from "../types";
import { GradeBadge } from "../components/ui";
import ProgressRing from "../components/ProgressRing.vue";
import type { View } from "./types";

interface LastRead {
  sectionId: string;
  chapterTitle: string;
  sectionTitle: string;
}

const props = defineProps<{ go: (v: View) => void }>();
const go = props.go;

const summary = ref<KpSummary[]>([]);
const last = ref<LastRead | null>(null);
onMounted(() => {
  attemptsSummary().then((s) => (summary.value = s)).catch(() => {});
  loadSetting("last-read")
    .then((v) => {
      if (v) {
        const parsed = JSON.parse(v) as LastRead;
        // 只在节还存在时展示续读(内容重组后旧位置自然失效)
        if (allSections().some((s) => s.section.id === parsed.sectionId)) last.value = parsed;
      }
    })
    .catch(() => {});
});

const sections = course.chapters.flatMap((ch) => ch.sections);
const graded = sections.filter((s) => s.kp);
const avg = graded.length
  ? graded.reduce((acc, s) => acc + masteryOf(s.kp!.id, summary.value), 0) / graded.length
  : 0;
const done = graded.filter((s) => masteryOf(s.kp!.id, summary.value) >= 0.6).length;
</script>

<template>
  <div class="space-y-8">
    <!-- hero -->
    <section class="-mx-5 px-5 pb-10 pt-12">
      <motion.div :initial="{ opacity: 0, y: 14 }" :animate="{ opacity: 1, y: 0 }" :transition="{ duration: 0.5 }">
        <div class="flex flex-wrap items-center gap-2">
          <span class="rounded-full accent-gradient px-3 py-1 text-[12px] font-bold text-white shadow">
            {{ course.exam.subject }}
          </span>
          <span
            class="inline-flex items-center gap-1 rounded-full px-3 py-1 text-[12px] font-medium ring-1"
            style="background: var(--tk-surface); color: var(--tk-muted); border-color: var(--tk-line)"
          >
            <Target :size="12" /> {{ course.exam.score_range }}
          </span>
          <span
            class="inline-flex items-center gap-1 rounded-full px-3 py-1 text-[12px] font-medium ring-1"
            style="background: var(--tk-surface); color: var(--tk-muted); border-color: var(--tk-line)"
          >
            <CalendarClock :size="12" /> 一年一考,2024 年起为 5 月底
          </span>
        </div>
        <h1 class="tk-display mt-4 text-[32px] font-bold leading-snug tracking-tight">
          考纲对齐、分值驱动的
          <span class="text-gradient">嵌入式备考</span>
        </h1>
        <p class="mt-2 max-w-3xl text-[15px] leading-relaxed" style="color: var(--tk-muted)">
          {{ course.exam.note }}
        </p>
      </motion.div>
    </section>

    <!-- 续读 -->
    <motion.button
      v-if="last"
      type="button"
      :initial="{ opacity: 0, y: -8 }"
      :animate="{ opacity: 1, y: 0 }"
      class="tk-card tk-card-hover flex w-full items-center gap-3 px-5 py-3.5 text-left"
      @click="go({ kind: 'topic', sectionId: last.sectionId })"
    >
      <span class="flex h-9 w-9 items-center justify-center rounded-xl accent-gradient text-white shadow">
        <BookOpen :size="17" />
      </span>
      <span class="flex-1 text-[14px]">
        <span class="font-semibold">接着学</span>
        <span class="ml-2" style="color: var(--tk-muted)">{{ last.chapterTitle }} · {{ last.sectionTitle }}</span>
      </span>
      <ArrowRight :size="16" class="accent-fg" />
    </motion.button>

    <!-- 课程卡 -->
    <section>
      <motion.button
        type="button"
        :initial="{ opacity: 0, y: 18 }"
        :animate="{ opacity: 1, y: 0 }"
        :transition="{ delay: 0.08, duration: 0.45 }"
        class="tk-card tk-card-hover group relative w-full overflow-hidden p-6 text-left"
        @click="go({ kind: 'course' })"
      >
        <div
          class="absolute -right-10 -top-10 h-36 w-36 rounded-full opacity-[0.09] transition-transform duration-500 group-hover:scale-150"
          :style="{ background: course.accent }"
        />
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="flex items-center gap-2">
              <GradeBadge :value="course.exam.grade" />
              <span class="text-[12px] font-medium" style="color: var(--tk-muted)">{{ course.exam.subject }}</span>
            </div>
            <h2 class="tk-display mt-2 text-[22px] font-bold" :style="{ color: course.accent }">
              {{ course.title }}
            </h2>
            <p class="mt-1.5 text-[13.5px] leading-relaxed" style="color: var(--tk-muted)">{{ course.tagline }}</p>
            <div class="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12.5px]" style="color: var(--tk-muted)">
              <span>依据《{{ course.textbook.title }}》</span>
              <span>· {{ course.textbook.chapters_total }} 章 {{ sections.length }} 节 · 已拿下 {{ done }} 节</span>
            </div>
          </div>
          <ProgressRing :value="avg" :size="64" :stroke="7" :color="course.accent">
            <span class="text-[13px] font-bold" :style="{ color: course.accent }">
              {{ Math.round(avg * 100) }}%
            </span>
          </ProgressRing>
        </div>
        <div class="mt-4 flex items-center gap-1 text-[13px] font-semibold accent-fg">
          进入学习 <ArrowRight :size="15" class="transition-transform group-hover:translate-x-1" />
        </div>
      </motion.button>
    </section>

    <!-- 真题与战况入口 -->
    <section class="grid gap-5 sm:grid-cols-2">
      <button
        type="button"
        class="tk-card tk-card-hover flex items-center gap-4 p-5 text-left"
        @click="go({ kind: 'past' })"
      >
        <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-lg">
          <ScrollText :size="22" />
        </span>
        <span>
          <span class="block font-bold">历年真题演练</span>
          <span class="block text-[13px]" style="color: var(--tk-muted)">2010–2020 十一卷整卷练习,作答计入掌握度</span>
        </span>
      </button>
      <button
        type="button"
        class="tk-card tk-card-hover flex items-center gap-4 p-5 text-left"
        @click="go({ kind: 'dashboard' })"
      >
        <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg">
          <Gauge :size="22" />
        </span>
        <span>
          <span class="block font-bold">掌握度战况</span>
          <span class="block text-[13px]" style="color: var(--tk-muted)">
            共 {{ allSections().length }} 节 · 全部由作答记录派生
          </span>
        </span>
      </button>
    </section>
  </div>
</template>
