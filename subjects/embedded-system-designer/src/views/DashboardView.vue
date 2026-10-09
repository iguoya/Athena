<script setup lang="ts">
// 战况页:一切数字由作答记录派生(ADR 0052)——没有记录就没有徽章。
import { computed, onMounted, ref } from "vue";
import { Flame, CalendarCheck, TrendingUp } from "lucide-vue-next";
import { course, allSections, masteryOf } from "../content";
import { attemptsSummary, todayStats, type TodayStats } from "../db";
import type { KpSummary } from "../types";
import { DifficultyDots, MasteryGoalBadge } from "../components/ui";
import ProgressRing from "../components/ProgressRing.vue";

const summary = ref<KpSummary[]>([]);
const today = ref<TodayStats | null>(null);
onMounted(() => {
  attemptsSummary().then((s) => (summary.value = s)).catch(() => {});
  todayStats().then((s) => (today.value = s)).catch(() => {});
});

const byKp = computed(() => new Map(summary.value.map((s) => [s.kp_id, s])));
const totalAnswered = computed(() => summary.value.reduce((s, x) => s + x.total, 0));
const totalCorrect = computed(() => summary.value.reduce((s, x) => s + x.correct, 0));
const bestStreak = computed(() => Math.max(0, ...summary.value.map((s) => s.streak)));
</script>

<template>
  <div class="space-y-7 pt-8">
    <header>
      <h1 class="tk-display text-[26px] font-bold tracking-tight">掌握度战况</h1>
      <p class="mt-1.5 text-[14px]" style="color: var(--tk-muted)">
        掌握度只由作答写入:下面每个数字都来自 progress/learning.db 的作答记录。
      </p>
    </header>

    <section class="grid gap-4 sm:grid-cols-3">
      <div class="tk-card p-5">
        <div class="flex items-center gap-3">
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md">
            <CalendarCheck :size="20" />
          </span>
          <span class="text-[13px] font-medium" style="color: var(--tk-muted)">今日作答</span>
        </div>
        <div class="tk-display mt-3 text-[26px] font-bold tracking-tight">{{ today?.answered ?? 0 }} 题</div>
        <div class="mt-0.5 text-[12px]" style="color: var(--tk-muted)">
          {{ today ? `答对 ${today.correct} · ${today.date}` : "还没有作答" }}
        </div>
      </div>
      <div class="tk-card p-5">
        <div class="flex items-center gap-3">
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500 to-rose-500 text-white shadow-md">
            <Flame :size="20" />
          </span>
          <span class="text-[13px] font-medium" style="color: var(--tk-muted)">最高连对</span>
        </div>
        <div class="tk-display mt-3 text-[26px] font-bold tracking-tight">{{ bestStreak }} 题</div>
        <div class="mt-0.5 text-[12px]" style="color: var(--tk-muted)">单个知识点最近连续答对</div>
      </div>
      <div class="tk-card p-5">
        <div class="flex items-center gap-3">
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-md">
            <TrendingUp :size="20" />
          </span>
          <span class="text-[13px] font-medium" style="color: var(--tk-muted)">累计正确率</span>
        </div>
        <div class="tk-display mt-3 text-[26px] font-bold tracking-tight">
          {{ totalAnswered > 0 ? `${Math.round((totalCorrect / totalAnswered) * 100)}%` : "—" }}
        </div>
        <div class="mt-0.5 text-[12px]" style="color: var(--tk-muted)">累计作答 {{ totalAnswered }} 题</div>
      </div>
    </section>

    <section class="tk-card overflow-hidden">
      <div class="border-b px-5 py-3.5 text-[14px] font-bold" style="border-color: var(--tk-line)">
        知识点掌握一览
      </div>
      <div class="divide-y" style="border-color: var(--tk-line)">
        <div
          v-for="{ chapter, section } in allSections()"
          :key="section.id"
          class="flex items-center gap-4 px-5 py-3.5"
          style="border-color: var(--tk-line)"
        >
          <span class="h-8 w-1.5 shrink-0 rounded-full" :style="{ background: course.accent }" />
          <div class="min-w-0 flex-1">
            <div class="text-[14px] font-semibold">
              {{ section.title }}
              <span class="ml-2 text-[11.5px] font-normal" style="color: var(--tk-muted)">
                第 {{ chapter.no }} 章
              </span>
            </div>
            <div class="mt-1 flex flex-wrap items-center gap-2.5 text-[12px]" style="color: var(--tk-muted)">
              <template v-if="section.kp">
                <DifficultyDots :difficulty="section.kp.difficulty" />
                <MasteryGoalBadge :goal="section.kp.mastery_goal" />
                <span v-if="byKp.get(section.kp.id)" class="font-mono">
                  {{ byKp.get(section.kp.id)!.correct }}/{{ byKp.get(section.kp.id)!.total }} 对 · 连对
                  {{ byKp.get(section.kp.id)!.streak }}
                </span>
                <span v-else>还没作答过——先去随堂考核</span>
              </template>
              <span v-else>本章待建</span>
            </div>
          </div>
          <ProgressRing :value="masteryOf(section.kp?.id, summary)" :color="course.accent" />
        </div>
      </div>
    </section>
  </div>
</template>
