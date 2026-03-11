<script setup lang="ts">
defineProps<{
  label: string;
  value: number | string;
  tone?: "default" | "success" | "warn";
}>();
</script>

<template>
  <div
    class="inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium"
    :class="{
      'bg-slate-100 text-slate-700': tone === 'default' || !tone,
      'bg-emerald-100 text-emerald-700': tone === 'success',
      'bg-amber-100 text-amber-700': tone === 'warn'
    }"
  >
    <span class="text-xs uppercase tracking-wide">{{ label }}</span>
    <span>{{ value }}</span>
  </div>
</template>

