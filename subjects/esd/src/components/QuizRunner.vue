<script setup lang="ts">
// 单题聚焦式作答器:每答一题即写进度库(ADR 0052:作答先入库)。
// 章节随堂考核用;整卷形态见 PaperRunner。
import { computed, ref } from "vue";
import { CheckCircle2, XCircle, ArrowRight, Award } from "lucide-vue-next";
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

const idx = ref(0);
const picked = ref<number | null>(null);
const answers = ref<{ question: Question; picked: number }[]>([]);

const question = computed(() => props.questions[idx.value]);
const judged = computed(() => picked.value !== null);
const correct = computed(() => judged.value && picked.value === question.value.answer);
const finished = computed(() => answers.value.length === props.questions.length);
const score = computed(
  () => answers.value.filter((a) => a.picked === a.question.answer).length,
);

function submit(choice: number) {
  if (judged.value) return;
  picked.value = choice;
  answers.value = [...answers.value, { question: question.value, picked: choice }];
  recordAttempt({
    course: props.course,
    chapterId: props.chapterId,
    kpId: props.kpId,
    questionId: question.value.id,
    correct: choice === question.value.answer,
    mode: props.mode,
  }).catch(() => {});
}

function advance() {
  if (idx.value + 1 < props.questions.length) {
    idx.value += 1;
    picked.value = null;
  } else {
    idx.value = props.questions.length; // 触发 finished
  }
}

const ratio = computed(() => score.value / props.questions.length);
</script>

<template>
  <!-- 结果页 -->
  <div v-if="finished" class="mx-auto max-w-2xl space-y-5 pt-8">
    <div class="tk-card p-8 text-center">
      <Award :size="44" :class="ratio >= 0.6 ? 'mx-auto text-emerald-500' : 'mx-auto text-amber-500'" />
      <h2 class="mt-3 text-[22px] font-bold tk-display">
        {{ ratio >= 0.8 ? "稳了" : ratio >= 0.6 ? "过线水平" : "回炉再战" }}
      </h2>
      <p class="mt-1 text-[14px]" style="color: var(--tk-muted)">
        {{ score }} / {{ questions.length }} 正确(及格线 60%:{{ ratio >= 0.6 ? "已过" : "未过" }})
      </p>
      <div class="mx-auto mt-4 h-2.5 w-64 overflow-hidden rounded-full" style="background: rgba(0,0,0,0.06)">
        <div
          class="h-full rounded-full transition-all duration-700 ease-out"
          :class="ratio >= 0.6 ? 'bg-gradient-to-r from-emerald-400 to-teal-500' : 'bg-gradient-to-r from-amber-400 to-orange-500'"
          :style="{ width: `${ratio * 100}%` }"
        />
      </div>
      <p class="mt-4 text-[12.5px]" style="color: color-mix(in srgb, var(--tk-muted) 80%, transparent)">
        作答已写入进度库,战况页可见派生的掌握度。
      </p>
      <button
        type="button"
        class="mt-5 inline-flex items-center gap-1.5 rounded-full accent-gradient px-5 py-2.5 text-[14px] font-semibold text-white shadow-md hover:opacity-90"
        @click="emit('exit')"
      >
        <ArrowRight :size="15" /> 返回
      </button>
    </div>
    <div class="space-y-3">
      <div v-for="(a, i) in answers" :key="i" class="tk-card p-4">
        <div class="flex items-start gap-2.5">
          <CheckCircle2 v-if="a.picked === a.question.answer" :size="17" class="mt-0.5 shrink-0 text-emerald-500" />
          <XCircle v-else :size="17" class="mt-0.5 shrink-0 text-rose-400" />
          <div class="min-w-0">
            <p class="prose-lesson text-[13.5px] font-medium">
              {{ i + 1 }}. <InlineText :text="a.question.stem" />
            </p>
            <p class="mt-1 text-[12.5px]" style="color: var(--tk-muted)">
              你的答案:{{ LETTERS[a.picked] }}
              <template v-if="a.picked !== a.question.answer">
                · 正确:{{ LETTERS[a.question.answer] }}
              </template>
            </p>
            <p
              v-if="a.picked !== a.question.answer"
              class="prose-lesson mt-1 text-[12.5px]"
              style="color: var(--tk-muted)"
            >
              <InlineText :text="a.question.explanation" />
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 作答页 -->
  <div v-else class="mx-auto max-w-2xl space-y-5 pt-6">
    <div class="flex items-center justify-between">
      <h1 class="text-[18px] font-bold tk-display">{{ title }}</h1>
      <span class="text-[13px]" style="color: var(--tk-muted)">
        第 {{ idx + 1 }} / {{ questions.length }} 题
      </span>
    </div>
    <div class="h-1.5 overflow-hidden rounded-full" style="background: rgba(0,0,0,0.06)">
      <div
        class="h-full rounded-full accent-gradient transition-all duration-300"
        :style="{ width: `${((idx + (judged ? 1 : 0)) / questions.length) * 100}%` }"
      />
    </div>

    <div class="tk-card p-6">
      <p class="prose-lesson text-[15.5px] font-medium leading-relaxed">
        <InlineText :text="question.stem" />
      </p>
      <div class="mt-5 space-y-2.5">
        <button
          v-for="(opt, i) in question.options"
          :key="i"
          type="button"
          :disabled="judged"
          class="flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-[14px] transition-all"
          :class="[
            !judged && 'border-black/10 hover:border-[var(--tk-accent)] hover:bg-[var(--tk-accent-soft)]',
            judged && i === question.answer && 'border-emerald-400 bg-emerald-50 animate-pop',
            judged && picked === i && i !== question.answer && 'border-rose-300 bg-rose-50 animate-shake',
            judged && picked !== i && i !== question.answer && 'border-black/5 opacity-55',
          ]"
          @click="submit(i)"
        >
          <span
            class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[12.5px] font-bold"
            style="background: rgba(0,0,0,0.05)"
          >
            {{ LETTERS[i] }}
          </span>
          <span class="prose-lesson"><InlineText :text="opt" /></span>
          <CheckCircle2 v-if="judged && i === question.answer" :size="18" class="ml-auto shrink-0 text-emerald-500" />
          <XCircle v-if="judged && picked === i && i !== question.answer" :size="18" class="ml-auto shrink-0 text-rose-400" />
        </button>
      </div>

      <div v-if="judged" class="mt-5">
        <div
          class="rounded-xl px-4 py-3.5 text-[13.5px] leading-relaxed"
          :class="correct ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'"
        >
          <b>{{ correct ? "答对了。" : "答错了。" }}</b>
          {{ question.explanation }}
        </div>
        <div class="mt-2.5 flex items-center justify-between">
          <span class="text-[11.5px]" style="color: color-mix(in srgb, var(--tk-muted) 75%, transparent)">
            出处:{{ question.source.relation === "authored" ? "自造考点题" : question.source.relation === "adapted" ? "教材改编" : "真题" }}
            {{ question.source.locator ? ` · ${question.source.locator}` : "" }}
          </span>
          <button
            type="button"
            class="inline-flex items-center gap-1 rounded-full accent-gradient px-4 py-2 text-[13px] font-semibold text-white shadow hover:opacity-90"
            @click="advance"
          >
            {{ idx + 1 < questions.length ? "下一题" : "看结果" }} <ArrowRight :size="14" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
