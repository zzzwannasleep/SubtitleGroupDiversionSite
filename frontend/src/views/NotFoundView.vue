<script setup lang="ts">
import { useI18n } from "@/composables/useI18n";


const { t } = useI18n();
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-100 px-4">
    <div class="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm">
      <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("notFound.code") }}</p>
      <h1 class="mt-3 text-3xl font-semibold text-slate-900">{{ t("notFound.title") }}</h1>
      <p class="mt-3 text-sm text-slate-500">{{ t("notFound.description") }}</p>
    </div>
  </div>
</template>
