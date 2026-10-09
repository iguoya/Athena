<script setup lang="ts">
// 节学习页 = 阅读器:与 softcert 的「大卡片包内容」刻意区分——内容块直接
// 铺在学习流上,列宽收窄,标题区紧凑,节末内联考核入口。块自身的视觉
// (表格卡/公式卡/callout)是内容元素,不是容器。
import { computed, onMounted, watch } from "vue";
import { ArrowLeft, ArrowRight, Link2, BookOpen, PenLine } from "lucide-vue-next";
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

/** 全部节,按课程顺序平铺:上一节/下一节导航用。 */
const flat = course.chapters.flatMap((ch) =>
  ch.sections.map((s) => ({ sectionId: s.id, title: s.title })),
);
const idx = computed(() => flat.findIndex((s) => s.sectionId === props.sectionId));
const prev = computed(() => (idx.value > 0 ? flat[idx.value - 1] : null));
const next = computed(() => (idx.value < flat.length - 1 ? flat[idx.value + 1] : null));
const requires = computed(() => current.value.section.kp?.requires ?? []);
const textbookText = computed(() => textbookTextOf(props.sectionId));

// 续读:每次进入章节就记下位置,首页行动卡据此放「接着学」。
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
  <div class="mx-auto max-w-[820px]">
    <!-- 面包屑行 -->
    <div class="flex items-center justify-between gap-3 pt-2">
      <button
        type="button"
        class="inline-flex items-center gap-1 text-[13px] transition-colors"
        style="color: var(--tk-muted)"
        @click="go({ kind: 'course' })"
      >
        <ArrowLeft :size="14" /> 学习路径
      </button>
      <span class="text-[12px]" style="color: color-mix(in srgb, var(--tk-muted) 75%, transparent)">
        第 {{ current.chapter.no }} 章 · {{ current.chapter.title }}
      </span>
    </div>

    <!-- 标题区:紧凑 -->
    <header class="mt-6 space-y-3">
      <h1 class="tk-display text-[30px] font-bold leading-tight tracking-tight">
        {{ current.section.title }}
      </h1>
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

    <!-- 内容块直接铺在学习流上(无容器卡) -->
    <article class="space-y-7 border-t py-8" style="border-color: var(--tk-line)">
      <Blocks v-for="(b, i) in lesson.blocks" :key="i" :block="b" />
    </article>

    <details v-if="textbookText" class="tk-card px-6 py-4">
      <summary class="cursor-pointer select-none text-[13.5px] font-semibold" style="color: var(--tk-muted)">
        教材原文({{ current.chapter.textbook_ref.locator }},《{{ course.textbook.title }}》忠实转录,OCR 可能有个别识别误差)
      </summary>
      <pre class="mt-4 max-h-[500px] overflow-y-auto whitespace-pre-wrap font-sans text-[13.5px] leading-7" style="color: color-mix(in srgb, var(--tk-fg) 75%, transparent)">{{ textbookText }}</pre>
    </details>

    <!-- 节末:内联考核入口 + 上下节导航 -->
    <div class="mt-8 space-y-4">
      <button
        type="button"
        class="flex w-full items-center justify-center gap-2 rounded-full py-3 text-[14.5px] font-semibold text-white shadow-md transition-transform hover:scale-[1.01] active:scale-[0.99] accent-gradient"
        @click="go({ kind: 'quiz', sectionId: props.sectionId })"
      >
        <PenLine :size="16" /> 学完了,来一趟随堂考核
      </button>

      <div class="grid gap-3 sm:grid-cols-2">
        <button
          v-if="prev"
          type="button"
          class="tk-card tk-card-hover flex items-center gap-2.5 p-3.5 text-left"
          @click="go({ kind: 'topic', sectionId: prev.sectionId })"
        >
          <ArrowLeft :size="15" class="shrink-0" style="color: var(--tk-muted)" />
          <span class="min-w-0">
            <span class="block text-[11px]" style="color: var(--tk-muted)">上一节</span>
            <span class="block truncate text-[13.5px] font-semibold">{{ prev.title }}</span>
          </span>
        </button>
        <span v-else />
        <button
          v-if="next"
          type="button"
          class="tk-card tk-card-hover flex items-center justify-end gap-2.5 p-3.5 text-right"
          @click="go({ kind: 'topic', sectionId: next.sectionId })"
        >
          <span class="min-w-0">
            <span class="block text-[11px]" style="color: var(--tk-muted)">下一节</span>
            <span class="block truncate text-[13.5px] font-semibold">{{ next.title }}</span>
          </span>
          <ArrowRight :size="15" class="shrink-0 accent-fg" />
        </button>
        <span v-else />
      </div>
    </div>
  </div>
</template>
