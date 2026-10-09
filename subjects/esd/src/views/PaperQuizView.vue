<script setup lang="ts">
// 整卷作答页:按 paperId 找卷,交给整卷作答器(mode=past-exam)。
import { computed } from "vue";
import { pastPaperFiles } from "../content";
import PaperRunner from "../components/PaperRunner.vue";
import type { View } from "./types";

const props = defineProps<{ paperId: string; go: (v: View) => void }>();
const go = props.go;

const paper = computed(() => pastPaperFiles.find((p) => p.id === props.paperId));
</script>

<template>
  <div v-if="!paper" class="pt-10 text-center text-[14px]" style="color: var(--tk-muted)">
    卷子 {{ paperId }} 不在构建产物里——确认 content/past-exams/papers/ 下有对应文件后重新构建。
  </div>
  <PaperRunner
    v-else
    :title="paper.title"
    :questions="paper.questions"
    mode="past-exam"
    course="past-exam"
    :chapter-id="paper.id"
    :kp-id="paper.id"
    @exit="go({ kind: 'past' })"
  />
</template>
