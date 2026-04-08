<script setup lang="ts">
defineProps<{
  title?: string;
  description?: string;
}>();
</script>

<template>
  <div class="app-surface px-6 py-10 text-center">
    <p class="text-lg font-semibold text-slate-900">{{ title ?? '暂无内容' }}</p>
    <p class="mt-2 text-sm text-slate-500">{{ description ?? '当前条件下还没有可展示的数据。' }}</p>
    <div v-if="$slots.actions" class="mt-4 flex justify-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>

