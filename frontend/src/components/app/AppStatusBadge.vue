<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  type: 'role' | 'user-status' | 'release-status' | 'sync-status';
  value: string;
}>();

const meta = computed(() => {
  const map = {
    role: {
      admin: ['Admin', 'bg-slate-900 text-white'],
      uploader: ['Uploader', 'bg-blue-100 text-blue-700'],
      user: ['User', 'bg-slate-100 text-slate-700'],
    },
    'user-status': {
      active: ['Active', 'bg-green-100 text-green-700'],
      disabled: ['Disabled', 'bg-red-100 text-red-700'],
    },
    'release-status': {
      published: ['Published', 'bg-green-100 text-green-700'],
      draft: ['Draft', 'bg-amber-100 text-amber-700'],
      hidden: ['Hidden', 'bg-slate-200 text-slate-700'],
    },
    'sync-status': {
      success: ['Success', 'bg-green-100 text-green-700'],
      warning: ['Warning', 'bg-amber-100 text-amber-700'],
      failed: ['Failed', 'bg-red-100 text-red-700'],
    },
  } as const;

  const fallback = ['Unknown', 'bg-slate-100 text-slate-700'];
  const current = map[props.type][props.value as keyof typeof map[typeof props.type]] ?? fallback;

  return {
    label: current[0],
    classes: current[1],
  };
});
</script>

<template>
  <span :class="['inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold', meta.classes]">
    {{ meta.label }}
  </span>
</template>

