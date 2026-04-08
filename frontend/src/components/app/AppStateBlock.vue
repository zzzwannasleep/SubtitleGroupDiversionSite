<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    tone?: 'default' | 'info' | 'success' | 'warning' | 'danger';
  }>(),
  {
    description: '',
    tone: 'default',
  },
);

const iconClasses = computed(() => {
  const map = {
    default: 'bg-slate-100 text-slate-500',
    info: 'bg-blue-50 text-blue-600',
    success: 'bg-green-50 text-green-600',
    warning: 'bg-amber-50 text-amber-600',
    danger: 'bg-red-50 text-red-600',
  } as const;

  return map[props.tone];
});
</script>

<template>
  <div class="app-surface px-6 py-10 text-center sm:px-8">
    <div :class="['mx-auto flex h-14 w-14 items-center justify-center rounded-2xl', iconClasses]">
      <slot name="icon" />
    </div>
    <p class="mt-4 text-lg font-semibold text-slate-900">{{ title }}</p>
    <p v-if="description" class="mt-2 text-sm leading-6 text-slate-500">
      {{ description }}
    </p>
    <div v-if="$slots.actions" class="mt-6 flex flex-wrap justify-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>
