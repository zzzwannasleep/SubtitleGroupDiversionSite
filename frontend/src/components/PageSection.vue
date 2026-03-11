<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white/90 p-5 shadow-sm">
    <div class="mb-4">
      <h2 class="text-lg font-semibold text-slate-900">{{ title }}</h2>
      <p v-if="subtitle" class="mt-1 text-sm text-slate-500">{{ subtitle }}</p>
    </div>
    <slot />
  </section>
</template>

