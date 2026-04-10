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
  <div class="site-layout">
    <div class="site-layout__backdrop site-layout__backdrop--top" />
    <div class="site-layout__backdrop site-layout__backdrop--bottom" />

    <SiteHeader />
    <AnnouncementStrip :announcements="announcements" />

    <main class="site-layout__main">
      <div class="app-container py-6 md:py-8">
        <div class="space-y-6">
          <RouterView />
        </div>
      </div>
    </main>

    <SiteFooter />
  </div>
</template>

<style scoped>
.site-layout {
  position: relative;
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  background:
    linear-gradient(180deg, #f8fbff 0%, #eef4fb 34%, #f8fafc 100%);
}

.site-layout__backdrop {
  pointer-events: none;
  position: absolute;
  inset: auto;
  border-radius: 9999px;
  filter: blur(90px);
  opacity: 0.4;
}

.site-layout__backdrop--top {
  top: 4rem;
  left: 8%;
  height: 14rem;
  width: 14rem;
  background: rgb(191 219 254 / 0.8);
}

.site-layout__backdrop--bottom {
  right: 12%;
  bottom: 12rem;
  height: 18rem;
  width: 18rem;
  background: rgb(226 232 240 / 0.95);
}

.site-layout__main {
  position: relative;
  z-index: 1;
  flex: 1;
}
</style>
