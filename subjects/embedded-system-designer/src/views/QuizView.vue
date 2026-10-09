<script setup lang="ts">
// 随堂考核入口:配置了 past_exam_knowledge 的节直接用该知识点历年真题精选
// (verbatim 整卷形态),否则用本节考核题(单题聚焦式)。
import { computed } from "vue";
import { course, findSection, pastExamQuestions, quizOf } from "../content";
import QuizRunner from "../components/QuizRunner.vue";
import PaperRunner from "../components/PaperRunner.vue";
import type { View } from "./types";

const props = defineProps<{ sectionId: string; go: (v: View) => void }>();
const go = props.go;

const section = computed(() => findSection(props.sectionId).section);
const pattern = computed(() => section.value.past_exam_knowledge);
const pastQuestions = computed(() =>
  pattern.value ? pastExamQuestions(pattern.value) : [],
);
const localQuiz = computed(() =>
  pastQuestions.value.length === 0 ? quizOf(props.sectionId) : null,
);
</script>

<template>
  <PaperRunner
    v-if="pastQuestions.length > 0"
    :title="`${section.title} · 历年真题精选(${pastQuestions.length} 题)`"
    :questions="pastQuestions"
    mode="chapter"
    :course="course.id"
    :chapter-id="section.id"
    :kp-id="section.kp?.id ?? section.id"
    @exit="go({ kind: 'topic', sectionId: section.id })"
  />
  <QuizRunner
    v-else-if="localQuiz"
    :title="`${section.title} · 随堂考核`"
    :questions="localQuiz.questions"
    mode="chapter"
    :course="course.id"
    :chapter-id="section.id"
    :kp-id="section.kp?.id ?? section.id"
    @exit="go({ kind: 'topic', sectionId: section.id })"
  />
</template>
