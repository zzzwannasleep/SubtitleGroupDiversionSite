<script setup lang="ts">
import { Megaphone } from 'lucide-vue-next';
import type { Announcement } from '@/types/admin';

defineProps<{
  announcements: Announcement[];
}>();
</script>

<template>
  <div v-if="announcements.length" class="border-b border-blue-100 bg-blue-50">
    <div class="app-container flex flex-col gap-2 py-3 text-sm text-blue-900 md:flex-row md:items-center md:gap-4">
      <span class="inline-flex items-center gap-1.5 rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-blue-700">
        <Megaphone class="h-3.5 w-3.5" />
        站点公告
      </span>
      <div class="flex flex-wrap gap-3">
        <span v-for="item in announcements" :key="item.id">{{ item.title }}：{{ item.content }}</span>
      </div>
    </div>
  </div>
</template>
