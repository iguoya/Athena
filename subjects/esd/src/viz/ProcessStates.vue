<script setup lang="ts">
// 进程三态图:点边看触发事件,默认选中「事件发生」这条最易错的边。
// 内容来自 os-rtos 章节的 viz 块(ADR 0056:可视化与交互是内容本身)。
import { computed, ref } from "vue";
import VizShell from "./VizShell.vue";

interface NodeDef {
  id: string;
  label: string;
  x: number;
  y: number;
  color: string;
}

interface EdgeDef {
  from: string;
  to: string;
  label: string;
  why: string;
  path: string;
  hx: number;
}

const NODES: NodeDef[] = [
  { id: "ready", label: "就绪", x: 300, y: 40, color: "#5b63f5" },
  { id: "running", label: "运行", x: 300, y: 200, color: "#0e8a6d" },
  { id: "blocked", label: "阻塞", x: 80, y: 200, color: "#e05b5b" },
];

const EDGES: EdgeDef[] = [
  {
    from: "ready",
    to: "running",
    label: "调度选中",
    why: "调度程序从就绪队列挑中它,分配 CPU。",
    path: "M 340 70 Q 400 120 340 182",
    hx: 372,
  },
  {
    from: "running",
    to: "ready",
    label: "时间片到 / 被抢占",
    why: "时间片用完(或更高优先级到来),回到就绪队列排队。",
    path: "M 262 182 Q 200 120 262 70",
    hx: 216,
  },
  {
    from: "running",
    to: "blocked",
    label: "等 I/O / P 操作失败",
    why: "主动让出 CPU 等待事件,进入阻塞态。",
    path: "M 262 210 L 150 210",
    hx: 206,
  },
  {
    from: "blocked",
    to: "ready",
    label: "事件发生",
    why: "I/O 完成或 V 操作唤醒——注意:只能回到就绪排队,不能直达运行!",
    path: "M 100 182 Q 80 120 262 52",
    hx: 96,
  },
];

const selected = ref(3);
const edge = computed(() => EDGES[selected.value]);
</script>

<template>
  <VizShell title="进程三态图 · 点边看触发事件">
    <template #controls>
      <span style="color: var(--tk-muted)">阻塞 → 运行这条边不存在</span>
    </template>
    <svg viewBox="0 0 460 250" class="w-full max-w-[560px]">
      <defs>
        <marker id="esd-arrow-on" marker-width="8" marker-height="8" ref-x="6" ref-y="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill="var(--tk-accent)" />
        </marker>
        <marker id="esd-arrow-off" marker-width="8" marker-height="8" ref-x="6" ref-y="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill="rgba(30,60,50,0.3)" />
        </marker>
      </defs>
      <g
        v-for="(e, i) in EDGES"
        :key="`${e.from}-${e.to}`"
        class="cursor-pointer"
        @click="selected = i"
      >
        <path
          :d="e.path"
          fill="none"
          :stroke="i === selected ? 'var(--tk-accent)' : 'rgba(30,60,50,0.22)'"
          :stroke-width="i === selected ? 3 : 2"
          :marker-end="`url(#esd-arrow-${i === selected ? 'on' : 'off'})`"
        />
      </g>
      <g v-for="nd in NODES" :key="nd.id">
        <rect
          :x="nd.x - 62"
          :y="nd.y - 24"
          width="124"
          height="48"
          rx="14"
          :fill="nd.color"
          opacity="0.92"
        />
        <text
          :x="nd.x"
          :y="nd.y + 6"
          text-anchor="middle"
          font-size="17"
          font-weight="bold"
          fill="#fff"
        >
          {{ nd.label }}
        </text>
      </g>
    </svg>
    <div class="mt-2 rounded-xl accent-soft px-4 py-3">
      <span class="font-bold accent-fg">{{ edge.label }}</span>
      <span class="ml-2 text-[13.5px]" style="color: color-mix(in srgb, var(--tk-fg) 75%, transparent)">
        {{ edge.why }}
      </span>
    </div>
  </VizShell>
</template>
