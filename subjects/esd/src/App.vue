<script setup lang="ts">
// 应用骨架:左侧菜单(全局导航 + 章树)+ 视图切换。单课程应用,视图不带 courseId。
import { computed, ref, watch } from "vue";
import { BookOpen, ChevronDown, Gauge, Home, ScrollText, Palette } from "lucide-vue-next";
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

const skin = ref<SkinId>(currentSkin());
function pickSkin(id: SkinId) {
  skin.value = id;
  applySkin(id);
}

function navCls(active: boolean) {
  return `flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-[13.5px] font-medium transition-colors ${
    active ? "accent-gradient text-white shadow-sm" : "hover:bg-[var(--tk-accent-soft)]"
  }`;
}
</script>

<template>
  <div class="app-backdrop" />
  <div class="flex min-h-screen">
    <!-- 左侧菜单 -->
    <aside
      class="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r"
      style="border-color: var(--tk-line); background: var(--tk-surface); backdrop-filter: blur(12px)"
    >
      <div class="flex items-center gap-2.5 px-4 pb-2 pt-4">
        <img src="/icon.svg" alt="" width="34" height="34" class="rounded-xl" />
        <div class="min-w-0">
          <div class="tk-display truncate text-[14.5px] font-bold leading-tight">嵌入式系统设计师</div>
          <div class="text-[11px]" style="color: var(--tk-muted)">软考中级 · 一年一考</div>
        </div>
      </div>

      <nav class="flex-1 overflow-y-auto px-3 pb-6">
        <button type="button" :class="navCls(view.kind === 'home')" @click="go({ kind: 'home' })">
          <Home :size="16" /> 首页
        </button>

        <div class="mt-1">
          <button
            type="button"
            :class="`flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-[13.5px] font-semibold transition-colors ${
              view.kind === 'course' || activeSectionId
                ? 'accent-soft'
                : 'hover:bg-[var(--tk-accent-soft)]'
            }`"
            @click="go({ kind: 'course' })"
          >
            <BookOpen :size="16" class="accent-fg" />
            <span class="flex-1 text-left">{{ course.title }}</span>
            <ChevronDown :size="14" />
          </button>
          <div v-if="view.kind === 'course' || activeSectionId" class="mb-1 ml-4 border-l pl-2" style="border-color: var(--tk-line)">
            <div v-for="ch in course.chapters" :key="ch.id" class="mt-1.5">
              <div class="px-2 py-1 text-[11.5px] font-semibold" style="color: var(--tk-muted)">
                第 {{ ch.no }} 章 · {{ ch.title }}
              </div>
              <div v-if="ch.sections.length === 0" class="px-2 py-0.5 text-[11.5px] opacity-40">待建</div>
              <button
                v-for="sec in ch.sections"
                :key="sec.id"
                type="button"
                class="block w-full rounded-lg px-2 py-1 text-left text-[12.5px] transition-colors"
                :class="
                  activeSectionId === sec.id
                    ? 'accent-gradient font-semibold text-white'
                    : 'hover:bg-[var(--tk-accent-soft)]'
                "
                @click="go({ kind: 'topic', sectionId: sec.id })"
              >
                {{ sec.title }}
              </button>
            </div>
          </div>
        </div>

        <div class="mt-1 border-t pt-2" style="border-color: var(--tk-line)">
          <button type="button" :class="navCls(view.kind === 'past' || view.kind === 'past-quiz')" @click="go({ kind: 'past' })">
            <ScrollText :size="16" /> 真题演练
          </button>
          <button type="button" :class="navCls(view.kind === 'dashboard')" @click="go({ kind: 'dashboard' })">
            <Gauge :size="16" /> 战况
          </button>
        </div>

        <!-- 皮肤切换:一套组件、令牌换氛围 -->
        <div class="mt-3 border-t pt-3" style="border-color: var(--tk-line)">
          <div class="mb-2 flex items-center gap-1.5 px-3 text-[11.5px] font-semibold" style="color: var(--tk-muted)">
            <Palette :size="12" /> 皮肤
          </div>
          <div class="flex items-center gap-2 px-3">
            <button
              v-for="s in SKINS"
              :key="s.id"
              type="button"
              :title="`${s.name} · ${s.hint}`"
              class="h-7 w-7 rounded-full border-2 transition-transform hover:scale-110"
              :class="skin === s.id ? 'border-[var(--tk-accent)]' : 'border-transparent'"
              :style="{ background: s.dot }"
              @click="pickSkin(s.id)"
            />
          </div>
        </div>
      </nav>
    </aside>

    <!-- 主视图 -->
    <main class="min-w-0 flex-1 px-6 pb-16 pt-4">
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
      class="fixed bottom-0 left-64 right-0 border-t py-3 text-center text-[11.5px] backdrop-blur"
      style="border-color: var(--tk-line); background: color-mix(in srgb, var(--tk-bg) 70%, transparent); color: color-mix(in srgb, var(--tk-muted) 70%, transparent)"
    >
      软考中级·嵌入式系统设计师 · {{ course.exam.score_range }} ·
      菜单目录对齐官方教材,出处在 content/sources.json
    </footer>
  </div>
</template>
