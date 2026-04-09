<script setup lang="ts">
import { ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { Palette } from 'lucide-vue-next';
import UiButton from '@/components/ui/UiButton.vue';
import UiDialog from '@/components/ui/UiDialog.vue';
import UiTextarea from '@/components/ui/UiTextarea.vue';
import { useAuthStore } from '@/stores/auth';
import { useThemeStore } from '@/stores/theme';
import type { ThemeMode } from '@/types/theme';

const authStore = useAuthStore();
const themeStore = useThemeStore();

const { currentUser } = storeToRefs(authStore);
const { customCss, isSaving, isThemePanelOpen, mode, saveErrorMessage } = storeToRefs(themeStore);

const draftMode = ref<ThemeMode>('system');
const draftCustomCss = ref('');

const modeOptions: Array<{ value: ThemeMode; label: string }> = [
  { value: 'system', label: '跟随系统' },
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' },
];

watch(
  isThemePanelOpen,
  (open) => {
    if (!open) return;
    draftMode.value = mode.value;
    draftCustomCss.value = customCss.value;
  },
  { immediate: true },
);

async function handleSave() {
  await themeStore.saveTheme({
    mode: draftMode.value,
    customCss: draftCustomCss.value,
  });
}

function handleClear() {
  draftCustomCss.value = '';
}
</script>

<template>
  <template v-if="currentUser">
    <button class="theme-fab" type="button" @click="themeStore.openThemePanel()">
      <Palette class="h-4 w-4" />
      <span>主题</span>
    </button>

    <UiDialog
      :open="isThemePanelOpen"
      title="主题设置"
      width-class="max-w-2xl"
      @close="themeStore.closeThemePanel()"
    >
      <div class="theme-panel">
        <div class="theme-row">
          <span class="theme-label">模式</span>
          <div class="theme-mode-group">
            <button
              v-for="option in modeOptions"
              :key="option.value"
              type="button"
              :class="['theme-mode-button', draftMode === option.value ? 'theme-mode-button-active' : '']"
              @click="draftMode = option.value"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <div class="theme-editor">
          <div class="theme-row">
            <span class="theme-label">CSS</span>
            <UiButton variant="ghost" size="sm" @click="handleClear">清空</UiButton>
          </div>

          <UiTextarea v-model="draftCustomCss" :rows="12" />
        </div>

        <p v-if="saveErrorMessage" class="theme-error">{{ saveErrorMessage }}</p>
      </div>

      <template #footer>
        <div class="theme-actions">
          <UiButton variant="secondary" @click="themeStore.closeThemePanel()">关闭</UiButton>
          <UiButton variant="primary" :disabled="isSaving" @click="handleSave">
            {{ isSaving ? '保存中...' : '保存' }}
          </UiButton>
        </div>
      </template>
    </UiDialog>
  </template>
</template>

<style scoped>
.theme-fab {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 60;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: 999px;
  border: 1px solid rgb(var(--border));
  background: rgb(var(--surface) / 0.94);
  padding: 0.7rem 0.9rem;
  color: rgb(var(--text-primary));
  box-shadow: var(--shadow-xl);
  backdrop-filter: blur(12px);
}

.theme-panel {
  display: grid;
  gap: 1rem;
}

.theme-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.theme-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgb(var(--text-primary));
}

.theme-mode-group {
  display: grid;
  flex: 1;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.5rem;
}

.theme-mode-button {
  border: 1px solid rgb(var(--border));
  border-radius: 0.75rem;
  background: rgb(var(--surface));
  padding: 0.7rem 0.85rem;
  color: rgb(var(--text-primary));
  transition:
    border-color 140ms ease,
    background-color 140ms ease;
}

.theme-mode-button-active {
  border-color: rgb(var(--primary-border));
  background: rgb(var(--primary-soft));
  color: rgb(var(--primary-text));
}

.theme-editor {
  display: grid;
  gap: 0.75rem;
}

.theme-error {
  font-size: 0.875rem;
  color: rgb(var(--danger));
}

.theme-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

@media (max-width: 640px) {
  .theme-fab {
    right: 0.75rem;
    bottom: 0.75rem;
  }

  .theme-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
