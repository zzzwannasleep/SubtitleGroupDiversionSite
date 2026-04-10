<script setup lang="ts">
import { computed } from 'vue';
import { useSiteSettingsStore } from '@/stores/siteSettings';

const siteSettingsStore = useSiteSettingsStore();
const siteSettings = computed(() => siteSettingsStore.settings);
</script>

<template>
  <footer class="border-t border-slate-200 bg-white">
    <div class="app-container flex flex-col gap-2 py-6 text-sm text-slate-500 md:flex-row md:items-center md:justify-between">
      <div class="space-y-1">
        <p class="font-medium text-slate-700">{{ siteSettings.siteName }}</p>
        <p>{{ siteSettings.siteDescription }}</p>
      </div>
      <div class="space-y-1 text-left md:text-right">
        <p>RSS 基础路径：{{ siteSettings.rssBasePath }}</p>
        <p v-if="siteSettings.downloadNotice">{{ siteSettings.downloadNotice }}</p>
      </div>
    </div>
  </footer>
</template>
