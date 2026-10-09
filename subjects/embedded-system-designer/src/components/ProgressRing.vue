<script setup lang="ts">
// SVG 进度环:掌握率可视化,成绩必须有出口(ADR 0052)。
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    value: number; // 0–1
    size?: number;
    stroke?: number;
    color?: string;
    label?: string;
  }>(),
  { size: 44, stroke: 5, color: undefined, label: undefined },
);

const clamped = computed(() => Math.max(0, Math.min(1, props.value)));
const r = computed(() => (props.size - props.stroke) / 2);
const c = computed(() => 2 * Math.PI * r.value);
const offset = computed(() => c.value * (1 - clamped.value));
const fallback = computed(() => (clamped.value > 0 ? `${Math.round(clamped.value * 100)}%` : ""));
</script>

<template>
  <span
    class="relative inline-flex items-center justify-center"
    :style="{ width: `${size}px`, height: `${size}px` }"
  >
    <svg :width="size" :height="size" class="-rotate-90">
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="r"
        fill="none"
        stroke="rgba(0,0,0,0.07)"
        :stroke-width="stroke"
      />
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="r"
        fill="none"
        :stroke="color ?? 'var(--tk-accent)'"
        :stroke-width="stroke"
        stroke-linecap="round"
        :stroke-dasharray="c"
        :stroke-dashoffset="offset"
        style="transition: stroke-dashoffset 0.6s cubic-bezier(0.22, 1, 0.36, 1)"
      />
    </svg>
    <span class="absolute inset-0 flex items-center justify-center text-[10px] font-bold" style="color: var(--tk-muted)">
      <slot>{{ label ?? fallback }}</slot>
    </span>
  </span>
</template>
