<script setup lang="ts">
// 9 种内容块的渲染器(ADR 0058:内容驱动 UI,不按章手写整页)。
import { computed } from "vue";
import katex from "katex";
import { Lightbulb, AlertTriangle, XOctagon } from "lucide-vue-next";
import type { Block } from "../types";
import { resolveViz } from "../viz";
import { InlineText } from "./InlineText";

const props = defineProps<{ block: Block }>();

const formulaHtml = computed(() => {
  if (props.block.type !== "formula") return "";
  return katex.renderToString(props.block.latex ?? "", {
    displayMode: true,
    throwOnError: false,
    output: "html",
  });
});

const callout = computed(() => {
  const kind = props.block.kind ?? "tip";
  return {
    tip: { icon: Lightbulb, cls: "border-emerald-200 bg-emerald-50", iconCls: "text-emerald-600", label: "要点" },
    warn: { icon: AlertTriangle, cls: "border-amber-200 bg-amber-50", iconCls: "text-amber-600", label: "注意" },
    trap: { icon: XOctagon, cls: "border-rose-200 bg-rose-50", iconCls: "text-rose-600", label: "陷阱" },
  }[kind];
});

const vizComp = computed(() =>
  props.block.type === "viz" ? resolveViz(props.block.component ?? "") : null,
);
</script>

<template>
  <!-- lead -->
  <div
    v-if="block.type === 'lead'"
    class="rounded-2xl border-l-4 px-5 py-4"
    style="border-left-color: var(--tk-accent); background: linear-gradient(to right, var(--tk-accent-soft), transparent)"
  >
    <p class="prose-lesson text-[15px]" style="color: color-mix(in srgb, var(--tk-fg) 88%, transparent)">
      <InlineText :text="block.text" />
    </p>
  </div>

  <!-- text -->
  <p v-else-if="block.type === 'text'" class="prose-lesson text-[15px]">
    <InlineText :text="block.text" />
  </p>

  <!-- formula -->
  <figure v-else-if="block.type === 'formula'" class="tk-card px-6 py-5">
    <div class="formula-block overflow-x-auto" v-html="formulaHtml" />
    <figcaption v-if="block.caption" class="mt-3 text-center text-[13px]" style="color: var(--tk-muted)">
      {{ block.caption }}
    </figcaption>
  </figure>

  <!-- compare -->
  <figure v-else-if="block.type === 'compare'">
    <figcaption class="mb-3 text-[15px] font-semibold">{{ block.title }}</figcaption>
    <div class="grid gap-3 md:grid-cols-2">
      <div
        v-for="(side, i) in [block.left, block.right]"
        :key="i"
        class="tk-card p-5 border-t-[3px]"
        :style="{ borderTopColor: i === 0 ? 'var(--tk-accent)' : '#fb923c' }"
      >
        <div class="mb-2 font-semibold" style="color: color-mix(in srgb, var(--tk-fg) 92%, transparent)">
          {{ side?.title }}
        </div>
        <p class="prose-lesson text-[14px]" style="color: color-mix(in srgb, var(--tk-fg) 76%, transparent)">
          <InlineText :text="side?.body" />
        </p>
      </div>
    </div>
  </figure>

  <!-- steps -->
  <figure v-else-if="block.type === 'steps'" class="tk-card p-5">
    <figcaption class="mb-4 font-semibold">{{ block.title }}</figcaption>
    <ol class="space-y-3">
      <li v-for="(step, i) in block.items ?? []" :key="i" class="flex gap-3">
        <span
          class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white accent-gradient"
        >
          {{ i + 1 }}
        </span>
        <span class="prose-lesson text-[14px]"><InlineText :text="step" /></span>
      </li>
    </ol>
  </figure>

  <!-- table -->
  <figure v-else-if="block.type === 'table'" class="tk-card overflow-hidden">
    <figcaption
      v-if="block.title"
      class="border-b px-5 py-3 font-semibold"
      style="border-color: var(--tk-line)"
    >
      {{ block.title }}
    </figcaption>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-[13.5px]">
        <thead>
          <tr class="accent-soft">
            <th
              v-for="(h, i) in block.headers ?? []"
              :key="i"
              class="px-4 py-2.5 font-semibold"
              style="color: var(--tk-accent-deep)"
            >
              {{ h }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, ri) in block.rows ?? []"
            :key="ri"
            :style="{ background: ri % 2 === 0 ? 'transparent' : 'color-mix(in srgb, var(--tk-bg) 55%, transparent)' }"
          >
            <td
              v-for="(cell, ci) in row"
              :key="ci"
              class="prose-lesson px-4 py-2.5 align-top"
              style="color: color-mix(in srgb, var(--tk-fg) 80%, transparent)"
            >
              <InlineText :text="cell" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </figure>

  <!-- code -->
  <figure v-else-if="block.type === 'code'" class="overflow-hidden rounded-2xl" style="background: #1d3129">
    <pre class="overflow-x-auto p-5 font-mono text-[13px] leading-relaxed text-[#d9f2e6]"><code>{{ block.code }}</code></pre>
  </figure>

  <!-- callout -->
  <div v-else-if="block.type === 'callout'" class="rounded-2xl border px-5 py-4" :class="callout.cls">
    <div class="mb-1.5 flex items-center gap-2 text-sm font-bold" :class="callout.iconCls">
      <component :is="callout.icon" :size="16" />
      {{ callout.label }}:{{ block.title }}
    </div>
    <p class="prose-lesson text-[14px]" style="color: color-mix(in srgb, var(--tk-fg) 82%, transparent)">
      <InlineText :text="block.text" />
    </p>
  </div>

  <!-- viz -->
  <figure v-else-if="block.type === 'viz'">
    <div class="tk-card overflow-hidden">
      <component :is="vizComp" v-if="vizComp" :params="block.params ?? {}" />
      <div v-else class="p-4 text-sm text-rose-600">未注册的可视化组件:{{ block.component }}</div>
    </div>
    <figcaption v-if="block.caption" class="mt-2 text-center text-[13px]" style="color: var(--tk-muted)">
      {{ block.caption }}
    </figcaption>
  </figure>
</template>
