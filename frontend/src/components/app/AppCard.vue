<script setup lang="ts">
import UiCard from '@/components/ui/UiCard.vue';

defineProps<{
  title?: string;
  description?: string;
}>();
</script>

<template>
  <UiCard>
    <header v-if="title || description || $slots.header" class="app-card-header">
      <div class="space-y-1">
        <h2 v-if="title" class="text-lg font-semibold text-slate-900">{{ title }}</h2>
        <p v-if="description" class="text-sm text-slate-500">{{ description }}</p>
      </div>
      <div v-if="$slots.header" class="flex items-center gap-2">
        <slot name="header" />
      </div>
    </header>
    <div class="app-card-body">
      <slot />
    </div>
    <footer v-if="$slots.footer" class="app-card-footer">
      <slot name="footer" />
    </footer>
  </UiCard>
</template>

