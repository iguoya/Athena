<script setup lang="ts">
// 骨架定位页：只陈述本应用是什么、承接什么，内容驱动 UI 随内容填充期落地
// （ADR 0058）；定位信息在这里硬编码，前端不读 app.json（ADR 0046）。
const info = {
  title: "硬件实验台",
  letter: "板",
  accent: "#4A8A0E",
  exam: "软考中级·嵌入式系统设计师",
  chapters: "第 2、4、5 章（硬件基础、RTOS、设计与开发）",
  parentTitle: "嵌入式系统设计师",
  engine: "serialport 串口 + 白名单烧录 + QEMU",
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
          <dd>骨架阶段（ADR 0103）：工程壳与规范先行，内容待填充。</dd>
        </div>
      </dl>
    </section>
  </main>
</template>
