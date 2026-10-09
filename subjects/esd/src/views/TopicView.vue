<script setup lang="ts">
// 节学习页:块渲染 + 教材原文 + 上一节/下一节导航 + 随堂考核入口。
import { computed, onMounted, watch } from "vue";
import { ArrowLeft, ArrowRight, Link2, BookOpen } from "lucide-vue-next";
import { course, findSection, lessonOf } from "../content";
import { textbookTextOf } from "../textbook-text";
import { saveSetting } from "../db";
import Blocks from "../components/Blocks.vue";
import { GradeBadge, WeightStars, DifficultyDots, MasteryGoalBadge, KnowledgeTypeBadge } from "../components/ui";
import type { View } from "./types";

const props = defineProps<{ sectionId: string; go: (v: View) => void }>();
const go = props.go;

const current = computed(() => findSection(props.sectionId));
const lesson = computed(() => lessonOf(props.sectionId));

/** 全部有内容的节,按课程顺序平铺:上一节/下一节导航用。 */
const flat = course.chapters.flatMap((ch) =>
  ch.sections.map((s) => ({ sectionId: s.id, title: s.title })),
);
const idx = computed(() => flat.findIndex((s) => s.sectionId === props.sectionId));
const prev = computed(() => (idx.value > 0 ? flat[idx.value - 1] : null));
const next = computed(() => (idx.value < flat.length - 1 ? flat[idx.value + 1] : null));
const requires = computed(() => current.value.section.kp?.requires ?? []);
const textbookText = computed(() => textbookTextOf(props.sectionId));

// 续读:每次进入章节就记下位置,首页据此放「接着学」入口。
function remember() {
  saveSetting(
    "last-read",
    JSON.stringify({
      sectionId: props.sectionId,
      chapterTitle: current.value.chapter.title,
      sectionTitle: current.value.section.title,
    }),
  ).catch(() => {});
}
onMounted(remember);
watch(() => props.sectionId, remember);
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-2 pt-4">
      <button
        type="button"
        class="inline-flex items-center gap-1 text-[13px] transition-colors"
        style="color: var(--tk-muted)"
        @click="go({ kind: 'course' })"
      >
        <ArrowLeft :size="15" /> {{ course.title }}
      </button>
    </div>

    <header class="space-y-3">
      <p class="text-[13px] font-medium" style="color: var(--tk-muted)">
        第 {{ current.chapter.no }} 章 · {{ current.chapter.title }}
      </p>
      <h1 class="tk-display text-[26px] font-bold tracking-tight">{{ current.section.title }}</h1>
      <div class="flex flex-wrap items-center gap-2.5">
        <GradeBadge :value="current.section.grade" />
        <WeightStars :weight="current.section.weight" />
        <template v-if="current.section.kp">
          <DifficultyDots :difficulty="current.section.kp.difficulty" />
          <MasteryGoalBadge :goal="current.section.kp.mastery_goal" />
          <KnowledgeTypeBadge :type="current.section.kp.knowledge_type" />
        </template>
      </div>
      <p
        v-if="requires.length > 0"
        class="flex items-center gap-1.5 text-[12.5px]"
        style="color: var(--tk-muted)"
      >
        <Link2 :size="13" /> 先修:{{ requires.join("、") }}——没学过的先回去过一遍
      </p>
      <p class="flex items-center gap-1.5 text-[12px]" style="color: color-mix(in srgb, var(--tk-muted) 80%, transparent)">
        <BookOpen :size="13" />
        出处:{{ current.chapter.textbook_ref.locator }},《{{ course.textbook.title }}》
      </p>
    </header>

    <article class="tk-card mx-auto max-w-[980px] px-6 py-7 md:px-9 md:py-9">
      <div class="space-y-6">
        <Blocks v-for="(b, i) in lesson.blocks" :key="i" :block="b" />
      </div>
    </article>

    <details v-if="textbookText" class="tk-card px-6 py-4">
      <summary class="cursor-pointer select-none text-[13.5px] font-semibold" style="color: var(--tk-muted)">
        教材原文({{ current.chapter.textbook_ref.locator }},《{{ course.textbook.title }}》忠实转录,OCR 可能有个别识别误差)
      </summary>
      <pre class="mt-4 max-h-[500px] overflow-y-auto whitespace-pre-wrap font-sans text-[13.5px] leading-7" style="color: color-mix(in srgb, var(--tk-fg) 75%, transparent)">{{ textbookText }}</pre>
    </details>

    <div class="mx-auto flex max-w-[980px] items-center justify-between gap-3">
      <button
        v-if="prev"
        type="button"
        class="inline-flex items-center gap-1.5 rounded-full border px-4 py-2 text-[13px] transition-colors"
        style="border-color: var(--tk-line); color: var(--tk-muted)"
        @click="go({ kind: 'topic', sectionId: prev.sectionId })"
      >
        <ArrowLeft :size="14" /> {{ prev.title }}
      </button>
      <span v-else />
      <button
        v-if="next"
        type="button"
        class="inline-flex items-center gap-1.5 rounded-full border px-4 py-2 text-[13px] transition-colors"
        style="border-color: var(--tk-line); color: var(--tk-muted)"
        @click="go({ kind: 'topic', sectionId: next.sectionId })"
      >
        {{ next.title }} <ArrowRight :size="14" />
      </button>
      <span v-else />
    </div>

    <button
      type="button"
      class="mx-auto w-full max-w-[980px] rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 py-4 text-[16px] font-bold text-white shadow-lg shadow-emerald-500/25 transition-transform hover:scale-[1.01] active:scale-[0.99]"
      @click="go({ kind: 'quiz', sectionId: props.sectionId })"
    >
      开始随堂考核({{ current.section.title }})
    </button>
  </div>
</template>
