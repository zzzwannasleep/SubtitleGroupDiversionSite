<script setup lang="ts">
defineProps<{
  title?: string;
  description?: string;
}>();
</script>

<template>
  <div class="app-surface border-red-200 px-6 py-10 text-center">
    <p class="text-lg font-semibold text-slate-900">{{ title ?? '加载失败' }}</p>
    <p class="mt-2 text-sm text-slate-500">{{ description ?? '稍后重试，或检查服务端状态。' }}</p>
    <div v-if="$slots.actions" class="mt-4 flex justify-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>

