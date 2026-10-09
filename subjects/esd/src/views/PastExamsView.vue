<script setup lang="ts">
// 历年真题列表:按年份成卷,点开即练(verbatim,作答计入掌握度)。
import { Play, ScrollText } from "lucide-vue-next";
import { pastPaperFiles } from "../content";
import type { View } from "./types";

const props = defineProps<{ go: (v: View) => void }>();
const go = props.go;
</script>

<template>
  <div class="space-y-6 pt-8">
    <header>
      <h1 class="tk-display text-[26px] font-bold tracking-tight">历年真题演练</h1>
      <p class="mt-1.5 text-[14px]" style="color: var(--tk-muted)">
        真题是判分内容的最高出处(verbatim)。按年份成卷练习,作答同样计入掌握度。
      </p>
    </header>

    <section class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <button
        v-for="p in pastPaperFiles"
        :key="p.id"
        type="button"
        class="tk-card tk-card-hover p-5 text-left"
        @click="go({ kind: 'past-quiz', paperId: p.id })"
      >
        <div class="text-[12px] font-medium accent-fg">{{ p.subject }} · {{ p.session }}</div>
        <div class="tk-display mt-1 text-[17px] font-bold">{{ p.title }}</div>
        <div class="mt-2 flex items-center justify-between">
          <span class="text-[12px]" style="color: var(--tk-muted)">{{ p.questions.length }} 题 · 点开即练</span>
          <Play :size="16" class="text-emerald-500" />
        </div>
      </button>
    </section>

    <section class="tk-card mx-auto max-w-2xl p-5">
      <div class="flex items-center gap-2 text-[13.5px] font-bold">
        <ScrollText :size="15" class="accent-fg" /> 继续扩卷
      </div>
      <p class="mt-2 text-[13px] leading-relaxed" style="color: var(--tk-muted)">
        用
        <code class="rounded px-1.5 py-0.5 font-mono text-[12px] accent-soft accent-fg">scripts/import-past-exam.py</code>
        从 qicoder 电子书导入更多年份(--list 看可导入的卷);导入格式与出处要求见
        content/past-exams/README.md。
      </p>
    </section>
  </div>
</template>
