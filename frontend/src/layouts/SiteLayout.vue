<script setup lang="ts">
import { ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import AnnouncementStrip from '@/components/navigation/AnnouncementStrip.vue';
import SiteFooter from '@/components/navigation/SiteFooter.vue';
import SiteHeader from '@/components/navigation/SiteHeader.vue';
import type { Announcement } from '@/types/admin';
import { listVisibleAnnouncements } from '@/services/admin';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const { currentUser } = storeToRefs(authStore);
const announcements = ref<Announcement[]>([]);

watch(
  () => currentUser.value?.role,
  async () => {
    announcements.value = await listVisibleAnnouncements(currentUser.value);
  },
  { immediate: true },
);
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
