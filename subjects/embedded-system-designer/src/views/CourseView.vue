<script setup lang="ts">
// 课程页 = 学习路径时间线:章是轨道上的里程碑,节是路径节点,按教材章序
// 排成一条纵向路径。与 softcert 的章节列表布局刻意区分(ADR 0090)。
import { onMounted, ref } from "vue";
import { motion } from "motion-v";
import { FileQuestion, BookOpen, Hammer } from "lucide-vue-next";
import { course, masteryOf } from "../content";
import { attemptsSummary } from "../db";
import type { KpSummary } from "../types";
import { GradeBadge, WeightStars, DifficultyDots, MasteryGoalBadge, KnowledgeTypeBadge } from "../components/ui";
import ProgressRing from "../components/ProgressRing.vue";
import { textbookTextOfChapter } from "../textbook-text";
import type { View } from "./types";

const props = defineProps<{ go: (v: View) => void }>();
const go = props.go;

const summary = ref<KpSummary[]>([]);
onMounted(() => {
  attemptsSummary().then((s) => (summary.value = s)).catch(() => {});
});
</script>

<template>
  <div class="space-y-6">
    <section class="pb-2 pt-2">
      <div class="flex items-center gap-2 text-[12.5px]" style="color: var(--tk-muted)">
        <GradeBadge :value="course.exam.grade" />
        <span>{{ course.exam.subject }} · {{ course.exam.score_range }}</span>
      </div>
      <h1 class="tk-display mt-2 text-[28px] font-bold" :style="{ color: course.accent }">
        {{ course.title }}
      </h1>
      <p class="mt-1.5 max-w-3xl text-[14px]" style="color: var(--tk-muted)">{{ course.tagline }}</p>
      <p
        class="mt-3 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[12px] font-medium ring-1"
        style="background: var(--tk-surface); color: var(--tk-muted); border-color: var(--tk-line)"
      >
        <BookOpen :size="13" />
        依据《{{ course.textbook.title }}》({{ course.textbook.publisher }} {{ course.textbook.year }})· 全 {{ course.textbook.chapters_total }} 章
      </p>
      <p class="mt-2 max-w-3xl text-[12px]" style="color: color-mix(in srgb, var(--tk-muted) 75%, transparent)">
        {{ course.exam.note }}
      </p>
    </section>

    <!-- 学习路径:纵向时间线 -->
    <section class="relative">
      <div
        class="absolute bottom-6 left-[21px] top-6 w-0.5 rounded-full"
        style="background: var(--tk-line)"
      />

      <motion.div
        v-for="(ch, ci) in course.chapters"
        :key="ch.id"
        class="relative pb-9 last:pb-2"
        :initial="{ opacity: 0, y: 12 }"
        :animate="{ opacity: 1, y: 0 }"
        :transition="{ delay: 0.05 * ci, duration: 0.35 }"
      >
        <!-- 章 = 里程碑 -->
        <div class="flex items-center gap-4">
          <div
            v-if="ch.sections.length > 0"
            class="z-10 flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-[15px] font-bold text-white shadow-md"
            :style="{ background: course.accent }"
          >
            {{ ch.no }}
          </div>
          <div
            v-else
            class="z-10 flex h-11 w-11 shrink-0 items-center justify-center rounded-full border-2 border-dashed text-[15px] font-bold"
            style="border-color: var(--tk-line); background: var(--tk-bg); color: var(--tk-muted)"
          >
            {{ ch.no }}
          </div>
          <div class="min-w-0">
            <div class="flex flex-wrap items-baseline gap-2">
              <h2 class="text-[17px] font-bold">{{ ch.title }}</h2>
              <span
                v-if="ch.sections.length === 0"
                class="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-[11.5px] font-medium text-amber-600 ring-1 ring-amber-200"
              >
                <Hammer :size="11" /> 待建
              </span>
            </div>
            <div class="mt-0.5 text-[11.5px]" style="color: color-mix(in srgb, var(--tk-muted) 75%, transparent)">
              {{ ch.textbook_ref.locator }} · 《{{ course.textbook.title }}》
            </div>
            <p v-if="ch.note" class="mt-1 max-w-3xl text-[12.5px] leading-relaxed" style="color: var(--tk-muted)">
              {{ ch.note }}
            </p>
          </div>
        </div>

        <!-- 节 = 路径节点 -->
        <div v-if="ch.sections.length > 0" class="ml-[60px] mt-3 space-y-2.5">
          <div v-for="sec in ch.sections" :key="sec.id" class="tk-card tk-card-hover flex items-center gap-4 p-4">
            <button type="button" class="min-w-0 flex-1 text-left" @click="go({ kind: 'topic', sectionId: sec.id })">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-[15px] font-bold">{{ sec.title }}</span>
                <GradeBadge :value="sec.grade" />
                <WeightStars :weight="sec.weight" />
              </div>
              <div
                v-if="sec.kp"
                class="mt-1.5 flex flex-wrap items-center gap-2.5 text-[12.5px]"
                style="color: var(--tk-muted)"
              >
                <DifficultyDots :difficulty="sec.kp.difficulty" />
                <MasteryGoalBadge :goal="sec.kp.mastery_goal" />
                <KnowledgeTypeBadge :type="sec.kp.knowledge_type" />
                <span style="color: color-mix(in srgb, var(--tk-muted) 80%, transparent)">{{ sec.kp.guide_line }}</span>
              </div>
            </button>
            <div class="flex shrink-0 items-center gap-3">
              <button
                type="button"
                title="随堂考核"
                class="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200 transition-colors hover:bg-emerald-100"
                @click="go({ kind: 'quiz', sectionId: sec.id })"
              >
                <FileQuestion :size="17" />
              </button>
              <ProgressRing :value="masteryOf(sec.kp?.id, summary)" :color="course.accent" />
            </div>
          </div>
        </div>

        <div v-else class="ml-[60px] mt-3">
          <div
            class="rounded-2xl border border-dashed px-4 py-4 text-center text-[13px]"
            style="border-color: var(--tk-line); color: var(--tk-muted)"
          >
            教学内容建设中——以下可直接阅读本章教材原文
          </div>
          <details v-if="textbookTextOfChapter(ch.id)" class="tk-card mt-2.5 px-4 py-3">
            <summary class="cursor-pointer select-none text-[13px] font-semibold" style="color: var(--tk-muted)">
              教材原文({{ ch.textbook_ref.locator }},《{{ course.textbook.title }}》忠实转录)
            </summary>
            <pre class="mt-3 max-h-[480px] overflow-y-auto whitespace-pre-wrap font-sans text-[13px] leading-7" style="color: color-mix(in srgb, var(--tk-fg) 75%, transparent)">{{ textbookTextOfChapter(ch.id) }}</pre>
          </details>
        </div>
      </motion.div>
    </section>
  </div>
</template>
