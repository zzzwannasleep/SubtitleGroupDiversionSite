<script setup lang="ts">
import { computed } from 'vue';
import { CircleAlert, CircleCheckBig, Info, TriangleAlert } from 'lucide-vue-next';

const props = withDefaults(
  defineProps<{
    variant?: 'success' | 'error' | 'info' | 'warning';
    title: string;
    description?: string;
  }>(),
  {
    variant: 'info',
    description: '',
  },
);

const meta = computed(() => {
  const map = {
    success: {
      icon: CircleCheckBig,
      classes: 'border-green-200 bg-green-50 text-green-800',
      iconClasses: 'bg-green-100 text-green-700',
    },
    error: {
      icon: CircleAlert,
      classes: 'border-red-200 bg-red-50 text-red-800',
      iconClasses: 'bg-red-100 text-red-700',
    },
    info: {
      icon: Info,
      classes: 'border-blue-200 bg-blue-50 text-blue-800',
      iconClasses: 'bg-blue-100 text-blue-700',
    },
    warning: {
      icon: TriangleAlert,
      classes: 'border-amber-200 bg-amber-50 text-amber-800',
      iconClasses: 'bg-amber-100 text-amber-700',
    },
  } as const;

  return map[props.variant];
});
</script>

<template>
  <div :class="['rounded-xl border px-4 py-3', meta.classes]">
    <div class="flex items-start gap-3">
      <div :class="['mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full', meta.iconClasses]">
        <component :is="meta.icon" class="h-4 w-4" />
      </div>
      <div class="min-w-0">
        <p class="text-sm font-semibold">{{ title }}</p>
        <p v-if="description" class="mt-1 text-sm/6 opacity-90">
          {{ description }}
        </p>
      </div>
      <div v-if="$slots.actions" class="ml-auto flex shrink-0 items-center gap-2">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>
