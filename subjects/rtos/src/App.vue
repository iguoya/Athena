<script setup lang="ts">
// 骨架定位页：只陈述本应用是什么、承接什么，内容驱动 UI 随内容填充期落地
// （ADR 0058）；定位信息在这里硬编码，前端不读 app.json（ADR 0046）。
const info = {
  title: "实时操作系统（RTOS）",
  letter: "实",
  accent: "#8A125A",
  exam: "软考中级·嵌入式系统设计师",
  chapters: "第 4 章（系统软件·RTOS）",
  parentTitle: "嵌入式系统设计师",
  engine: "FreeRTOS 真板观测 + QEMU 交叉编译 + 线程级调度模拟",
};
</script>

<template>
  <main class="skeleton-page">
    <section class="skeleton-card">
      <header class="skeleton-head">
        <span class="skeleton-badge" :style="{ background: info.accent }">
          {{ info.letter }}
        </span>
        <div>
          <h1>{{ info.title }}</h1>
          <p class="skeleton-sub">
            {{ info.exam }} · 实践课程（挂靠 {{ info.parentTitle }}）
          </p>
        </div>
      </header>
      <dl class="skeleton-facts">
        <div>
          <dt>承接章节</dt>
          <dd>{{ info.chapters }}</dd>
        </div>
        <div>
          <dt>实验引擎</dt>
          <dd>{{ info.engine }}</dd>
        </div>
        <div>
          <dt>状态</dt>
          <dd>骨架阶段（ADR 0106）：工程壳与规范先行，内容待填充。</dd>
        </div>
      </dl>
    </section>
  </main>
</template>
