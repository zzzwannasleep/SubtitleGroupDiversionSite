<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
}>();
</script>

<template>
  <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
    <div class="space-y-2">
      <h1 class="app-page-title">{{ title }}</h1>
      <p v-if="description" class="app-page-subtitle">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="flex flex-wrap items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>

