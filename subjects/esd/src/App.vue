<script setup lang="ts">
// 应用骨架:顶部指挥台 + 全宽单列内容。
// 与 softcert 的「左侧栏 + 内容区」刻意区分(ADR 0090:两种体验):全局导航
// (视图胶囊 + 皮肤切换)全部收进固定顶栏,不设侧栏;课程导航走课程页的
// 学习路径时间线。
import { computed, ref, watch } from "vue";
import { BookOpen, Gauge, Home, Palette, ScrollText } from "lucide-vue-next";
import { course } from "./content";
import { SKINS, applySkin, currentSkin, type SkinId } from "./theme";
import HomeView from "./views/HomeView.vue";
import CourseView from "./views/CourseView.vue";
import TopicView from "./views/TopicView.vue";
import QuizView from "./views/QuizView.vue";
import PastExamsView from "./views/PastExamsView.vue";
import PaperQuizView from "./views/PaperQuizView.vue";
import DashboardView from "./views/DashboardView.vue";
import type { View } from "./views/types";

const view = ref<View>({ kind: "home" });
function go(v: View) {
  view.value = v;
}

watch(view, () => {
  window.scrollTo({ top: 0 });
});

const activeSectionId = computed(() =>
  view.value.kind === "topic" || view.value.kind === "quiz" ? view.value.sectionId : null,
);

// 顶栏视图胶囊:course 在课程/学习/考核视图下都亮
const NAV = [
  { kind: "home" as const, label: "首页", icon: Home },
  { kind: "course" as const, label: "学习路径", icon: BookOpen },
  { kind: "past" as const, label: "真题演练", icon: ScrollText },
  { kind: "dashboard" as const, label: "战况", icon: Gauge },
];
function navActive(kind: View["kind"]): boolean {
  if (kind === "course") return view.value.kind === "course" || activeSectionId.value !== null;
  if (kind === "past") return view.value.kind === "past" || view.value.kind === "past-quiz";
  return view.value.kind === kind;
}

const skin = ref<SkinId>(currentSkin());
function pickSkin(id: SkinId) {
  skin.value = id;
  applySkin(id);
}
</script>

<template>
  <div class="app-backdrop" />
  <div class="flex min-h-screen flex-col">
    <!-- 顶部指挥台 -->
    <header
      class="sticky top-0 z-20 border-b"
      style="border-color: var(--tk-line); background: var(--tk-surface); backdrop-filter: blur(12px)"
    >
      <div class="mx-auto flex h-14 max-w-[1100px] items-center gap-3 px-6">
        <img src="/icon.svg" alt="" width="30" height="30" class="rounded-lg" />
        <div class="min-w-0">
          <div class="tk-display truncate text-[14px] font-bold leading-tight">嵌入式系统设计师</div>
          <div class="text-[10.5px]" style="color: var(--tk-muted)">软考中级 · 一年一考</div>
        </div>

        <nav class="ml-auto flex items-center gap-1">
          <button
            v-for="item in NAV"
            :key="item.kind"
            type="button"
            class="flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-colors"
            :class="
              navActive(item.kind)
                ? 'accent-gradient text-white shadow-sm'
                : 'hover:bg-[var(--tk-accent-soft)]'
            "
            @click="go({ kind: item.kind } as View)"
          >
            <component :is="item.icon" :size="15" />
            {{ item.label }}
          </button>
        </nav>

        <!-- 皮肤切换:一套组件、令牌换氛围 -->
        <div class="ml-1 flex items-center gap-1.5 border-l pl-3" style="border-color: var(--tk-line)">
          <button
            v-for="s in SKINS"
            :key="s.id"
            type="button"
            :title="`${s.name} · ${s.hint}`"
            class="h-6 w-6 rounded-full border-2 transition-transform hover:scale-110"
            :class="skin === s.id ? 'border-[var(--tk-accent)]' : 'border-transparent'"
            :style="{ background: s.dot }"
            @click="pickSkin(s.id)"
          />
          <Palette :size="13" class="ml-0.5" style="color: var(--tk-muted)" />
        </div>
      </div>
    </header>

    <!-- 主视图:全宽单列居中 -->
    <main class="mx-auto w-full max-w-[1100px] flex-1 px-6 pb-12 pt-6">
      <HomeView v-if="view.kind === 'home'" :go="go" />
      <CourseView v-else-if="view.kind === 'course'" :go="go" />
      <TopicView
        v-else-if="view.kind === 'topic'"
        :key="view.sectionId"
        :section-id="view.sectionId"
        :go="go"
      />
      <QuizView
        v-else-if="view.kind === 'quiz'"
        :key="view.sectionId"
        :section-id="view.sectionId"
        :go="go"
      />
      <PastExamsView v-else-if="view.kind === 'past'" :go="go" />
      <PaperQuizView
        v-else-if="view.kind === 'past-quiz'"
        :key="view.paperId"
        :paper-id="view.paperId"
        :go="go"
      />
      <DashboardView v-else-if="view.kind === 'dashboard'" />
    </main>

    <footer
      class="border-t py-4 text-center text-[11.5px]"
      style="border-color: var(--tk-line); color: color-mix(in srgb, var(--tk-muted) 70%, transparent)"
    >
      软考中级·嵌入式系统设计师 · {{ course.exam.score_range }} ·
      菜单目录对齐官方教材,出处在 content/sources.json
    </footer>
  </div>
</template>
