<script setup lang="ts">
import { computed, onBeforeUnmount, watch } from 'vue';
import ThemePanel from '@/components/theme/ThemePanel.vue';
import { useSiteSettingsStore } from '@/stores/siteSettings';

const SITE_CUSTOM_STYLE_ID = 'subtitle-group-site-custom-css';
const THEME_CUSTOM_STYLE_ID = 'subtitle-group-custom-theme';

const siteSettingsStore = useSiteSettingsStore();
const settings = computed(() => siteSettingsStore.settings);

function applySiteCustomCss(cssText: string) {
  if (typeof document === 'undefined') {
    return;
  }

  const nextCssText = cssText.trim();
  const existingStyleElement = document.getElementById(SITE_CUSTOM_STYLE_ID) as HTMLStyleElement | null;

  if (!nextCssText) {
    existingStyleElement?.remove();
    return;
  }

  const styleElement = existingStyleElement ?? document.createElement('style');
  styleElement.id = SITE_CUSTOM_STYLE_ID;
  styleElement.textContent = nextCssText;

  if (!existingStyleElement) {
    const themeStyleElement = document.getElementById(THEME_CUSTOM_STYLE_ID);
    document.head.insertBefore(styleElement, themeStyleElement ?? null);
  }
}

watch(
  () => settings.value.siteCustomCss,
  (cssText) => {
    applySiteCustomCss(cssText);
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  if (typeof document === 'undefined') {
    return;
  }

  document.getElementById(SITE_CUSTOM_STYLE_ID)?.remove();
});
</script>

<template>
  <RouterView />
  <ThemePanel />
</template>
