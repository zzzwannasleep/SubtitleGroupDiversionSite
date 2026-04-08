<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AnnouncementStrip from '@/components/navigation/AnnouncementStrip.vue';
import SiteFooter from '@/components/navigation/SiteFooter.vue';
import SiteHeader from '@/components/navigation/SiteHeader.vue';
import type { Announcement } from '@/types/admin';
import { listVisibleAnnouncements } from '@/services/admin';

const announcements = ref<Announcement[]>([]);

onMounted(async () => {
  announcements.value = await listVisibleAnnouncements();
});
</script>

<template>
  <div class="min-h-screen bg-slate-100">
    <SiteHeader />
    <AnnouncementStrip :announcements="announcements" />
    <main class="app-container py-6 md:py-8">
      <div class="space-y-6">
        <RouterView />
      </div>
    </main>
    <SiteFooter />
  </div>
</template>

