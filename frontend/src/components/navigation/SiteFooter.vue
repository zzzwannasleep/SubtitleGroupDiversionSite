<script setup lang="ts">
import { computed } from 'vue';
import { useSiteSettingsStore } from '@/stores/siteSettings';

const siteSettingsStore = useSiteSettingsStore();
const siteSettings = computed(() => siteSettingsStore.settings);
</script>

<template>
  <footer class="site-footer">
    <div class="app-container">
      <div class="site-footer__panel">
        <div class="space-y-2">
          <p class="site-footer__title">{{ siteSettings.siteName }}</p>
          <p class="site-footer__description">{{ siteSettings.siteDescription }}</p>
        </div>
        <div class="space-y-2 text-left md:text-right">
          <p v-if="siteSettings.downloadNotice" class="site-footer__meta">{{ siteSettings.downloadNotice }}</p>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  position: relative;
  z-index: 1;
  padding-bottom: 1rem;
}

.site-footer__panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border: 1px solid rgb(226 232 240 / 0.9);
  border-radius: 1.6rem;
  background: rgb(255 255 255 / 0.78);
  box-shadow: 0 18px 40px rgb(148 163 184 / 0.1);
  backdrop-filter: blur(16px);
  padding: 1.25rem 1.3rem;
}

.site-footer__title {
  font-size: 1rem;
  font-weight: 700;
  color: rgb(15 23 42);
}

.site-footer__description,
.site-footer__meta {
  font-size: 0.9rem;
  line-height: 1.75;
  color: rgb(100 116 139);
}

@media (min-width: 768px) {
  .site-footer__panel {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}
</style>
