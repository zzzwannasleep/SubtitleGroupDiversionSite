import { computed, ref, watch } from 'vue';
import { defineStore } from 'pinia';
import { getMyTheme, saveMyTheme } from '@/services/theme';
import type { SiteTheme, ThemeMode } from '@/types/theme';

const STYLE_ID = 'subtitle-group-custom-theme';

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>('system');
  const customCss = ref('');
  const isThemePanelOpen = ref(false);
  const isSaving = ref(false);
  const saveErrorMessage = ref('');
  const systemPrefersDark = ref(false);

  let initialized = false;

  const resolvedMode = computed<'light' | 'dark'>(() => {
    if (mode.value === 'system') {
      return systemPrefersDark.value ? 'dark' : 'light';
    }

    return mode.value;
  });

  function applyMode() {
    if (typeof document === 'undefined') return;
    document.documentElement.dataset.colorMode = resolvedMode.value;
  }

  function applyCustomCss() {
    if (typeof document === 'undefined') return;

    let styleElement = document.getElementById(STYLE_ID) as HTMLStyleElement | null;

    if (!styleElement) {
      styleElement = document.createElement('style');
      styleElement.id = STYLE_ID;
      document.head.appendChild(styleElement);
    }

    styleElement.textContent = customCss.value.trim();
  }

  function applyTheme(theme: SiteTheme) {
    mode.value = theme.mode;
    customCss.value = theme.customCss;
  }

  function resetTheme() {
    applyTheme({
      mode: 'system',
      customCss: '',
    });
  }

  function handleSystemThemeChange(event: MediaQueryListEvent) {
    systemPrefersDark.value = event.matches;
  }

  async function loadTheme() {
    try {
      const theme = await getMyTheme();
      if (theme) {
        applyTheme(theme);
        return;
      }

      resetTheme();
    } catch (error) {
      console.error('Failed to load user theme:', error);
    }
  }

  async function initialize() {
    if (initialized) return;
    initialized = true;

    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      systemPrefersDark.value = mediaQuery.matches;
      mediaQuery.addEventListener('change', handleSystemThemeChange);
    }

    watch(resolvedMode, applyMode, { immediate: true });
    watch(customCss, applyCustomCss, { immediate: true });
  }

  async function saveTheme(payload: SiteTheme) {
    isSaving.value = true;
    saveErrorMessage.value = '';

    try {
      const savedTheme = await saveMyTheme(payload);
      applyTheme(savedTheme);
      closeThemePanel();
    } catch (error) {
      saveErrorMessage.value = error instanceof Error ? error.message : '保存失败';
      throw error;
    } finally {
      isSaving.value = false;
    }
  }

  function openThemePanel() {
    saveErrorMessage.value = '';
    isThemePanelOpen.value = true;
  }

  function closeThemePanel() {
    isThemePanelOpen.value = false;
  }

  return {
    mode,
    customCss,
    isThemePanelOpen,
    isSaving,
    saveErrorMessage,
    resolvedMode,
    initialize,
    loadTheme,
    resetTheme,
    saveTheme,
    openThemePanel,
    closeThemePanel,
  };
});
