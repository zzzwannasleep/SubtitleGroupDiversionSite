<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  hint: string;
}>();
</script>

<template>
  <div class="app-surface p-5">
    <p class="text-sm text-slate-500">{{ label }}</p>
    <p class="mt-3 text-3xl font-semibold text-slate-900">{{ value }}</p>
    <p class="mt-2 text-sm text-slate-500">{{ hint }}</p>
  </div>
</template>
