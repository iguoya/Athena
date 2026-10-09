<script setup lang="ts">
// 整卷作答器:一页铺开全部题目(真实试卷形态),答题卡导航,
// 每题点选即判分写库(ADR 0052),交卷出成绩。随堂考核用单题聚焦式。
import { computed, ref } from "vue";
import { CheckCircle2, XCircle, ArrowLeft, Award } from "lucide-vue-next";
import { recordAttempt } from "../db";
import { InlineText } from "./InlineText";
import type { Question } from "../types";

const LETTERS = ["A", "B", "C", "D"];

const props = defineProps<{
  title: string;
  questions: Question[];
  mode: "chapter" | "past-exam";
  course: string;
  chapterId: string;
  kpId: string;
}>();

const emit = defineEmits<{ exit: [] }>();

const answers = ref<Record<string, { qid: string; picked: number }>>({});

function pick(q: Question, choice: number) {
  if (answers.value[q.id]) return;
  answers.value = { ...answers.value, [q.id]: { qid: q.id, picked: choice } };
  recordAttempt({
    course: props.course,
    chapterId: props.chapterId,
    kpId: props.kpId,
    questionId: q.id,
    correct: choice === q.answer,
    mode: props.mode,
  }).catch(() => {});
}

const answeredCount = computed(() => Object.keys(answers.value).length);
const score = computed(
  () =>
    Object.values(answers.value).filter(
      (a) => a.picked === props.questions.find((q) => q.id === a.qid)?.answer,
    ).length,
);
const allDone = computed(() => answeredCount.value === props.questions.length);

function jump(qid: string) {
  document.getElementById(`pq-${qid}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}
</script>

<template>
  <div class="pt-6">
    <!-- 顶部 sticky 工具条 -->
    <div
      class="sticky top-0 z-10 -mx-6 mb-6 border-b px-6 py-3 backdrop-blur"
      style="border-color: var(--tk-line); background: color-mix(in srgb, var(--tk-bg) 82%, transparent)"
    >
      <div class="mx-auto flex max-w-6xl flex-wrap items-center gap-3">
        <h1 class="text-[16px] font-bold tk-display">{{ title }}</h1>
        <span class="text-[13px]" style="color: var(--tk-muted)">
          已答 {{ answeredCount }} / {{ questions.length }}
        </span>
        <div class="ml-auto flex items-center gap-3">
          <span v-if="answeredCount > 0" class="text-[13px] font-semibold text-emerald-600">
            答对 {{ score }}
          </span>
          <button
            type="button"
            class="inline-flex items-center gap-1 rounded-full border px-3.5 py-1.5 text-[13px] transition-colors"
            style="border-color: var(--tk-line); color: var(--tk-muted)"
            @click="emit('exit')"
          >
            <ArrowLeft :size="13" /> 退出
          </button>
        </div>
      </div>
    </div>

    <div class="flex gap-6">
      <!-- 题目区:整卷铺开 -->
      <div class="min-w-0 flex-1 space-y-5">
        <div v-for="(q, qi) in questions" :id="`pq-${q.id}`" :key="q.id" class="tk-card scroll-mt-28 p-5">
          <div class="flex items-start justify-between gap-3">
            <p class="prose-lesson text-[15px] font-medium leading-relaxed">
              <span class="mr-2 font-bold accent-fg">{{ qi + 1 }}.</span>
              <InlineText :text="q.stem" />
            </p>
            <template v-if="answers[q.id]">
              <CheckCircle2
                v-if="answers[q.id].picked === q.answer"
                :size="18"
                class="mt-1 shrink-0 text-emerald-500"
              />
              <XCircle v-else :size="18" class="mt-1 shrink-0 text-rose-400" />
            </template>
          </div>
          <div class="mt-3.5 grid gap-2 md:grid-cols-2 2xl:grid-cols-3">
            <button
              v-for="(opt, i) in q.options"
              :key="i"
              type="button"
              :disabled="!!answers[q.id]"
              class="flex items-center gap-2.5 rounded-xl border px-3.5 py-2.5 text-left text-[13.5px] transition-all"
              :class="[
                !answers[q.id] && 'border-black/10 hover:border-[var(--tk-accent)] hover:bg-[var(--tk-accent-soft)]',
                answers[q.id] && i === q.answer && 'border-emerald-400 bg-emerald-50',
                answers[q.id] && answers[q.id].picked === i && i !== q.answer && 'border-rose-300 bg-rose-50 animate-shake',
                answers[q.id] && answers[q.id].picked !== i && i !== q.answer && 'border-black/5 opacity-50',
              ]"
              @click="pick(q, i)"
            >
              <span
                class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11.5px] font-bold"
                style="background: rgba(0,0,0,0.05)"
              >
                {{ LETTERS[i] }}
              </span>
              <span class="prose-lesson"><InlineText :text="opt" /></span>
            </button>
          </div>
          <div
            v-if="answers[q.id]"
            class="mt-3 rounded-xl px-4 py-3 text-[13px] leading-relaxed"
            :class="answers[q.id].picked === q.answer ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'"
          >
            <b>正确答案:{{ LETTERS[q.answer] }}。</b>
            {{ q.explanation }}
          </div>
        </div>
      </div>

      <!-- 答题卡 -->
      <aside class="hidden w-44 shrink-0 lg:block 2xl:w-60">
        <div class="tk-card sticky top-32 p-4">
          <div class="mb-3 text-[13px] font-bold">答题卡</div>
          <div class="grid grid-cols-6 gap-1.5">
            <button
              v-for="(q, i) in questions"
              :key="q.id"
              type="button"
              class="h-7 rounded-md text-[11px] font-bold transition-colors"
              :class="
                !answers[q.id]
                  ? 'bg-black/5'
                  : answers[q.id].picked === q.answer
                    ? 'bg-emerald-500 text-white'
                    : 'bg-rose-400 text-white'
              "
              :style="!answers[q.id] ? { color: 'var(--tk-muted)' } : {}"
              @click="jump(q.id)"
            >
              {{ i + 1 }}
            </button>
          </div>
          <div v-if="allDone" class="mt-4 rounded-xl bg-emerald-50 p-3 text-center">
            <Award :size="20" class="mx-auto text-emerald-500" />
            <div class="mt-1 text-[13px] font-bold text-emerald-700">整卷完成</div>
            <div class="text-[12px] text-emerald-600/80">
              {{ score }} / {{ questions.length }} · {{ Math.round((score / questions.length) * 100) }} 分
            </div>
          </div>
          <p v-else class="mt-3 text-[11.5px] leading-relaxed" style="color: color-mix(in srgb, var(--tk-muted) 75%, transparent)">
            白 = 未答,绿 = 答对,红 = 答错;点题号跳转。
          </p>
        </div>
      </aside>
    </div>
  </div>
</template>
