<script setup lang="ts">
// viz 块的公共外壳:标题 + 控制区插槽。
</script>

<template>
  <div class="p-5">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <span class="text-sm font-bold accent-fg"><slot name="title" /></span>
      <div class="flex flex-wrap items-center gap-3 text-[13px]"><slot name="controls" /></div>
    </div>
    <slot />
  </div>
</template>
