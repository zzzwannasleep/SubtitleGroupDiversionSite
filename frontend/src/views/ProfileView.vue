<script setup lang="ts">
import { onMounted, ref } from "vue";

import { getProfile, updateProfile } from "@/api/users";
import PageSection from "@/components/PageSection.vue";
import { useI18n } from "@/composables/useI18n";
import { AUTH_THEME_PRESETS } from "@/config/authTheme";
import { useAppearanceStore } from "@/stores/appearance";
import { useLocaleStore } from "@/stores/locale";
import type { UserProfile } from "@/types";
import { formatBytes } from "@/utils/format";


const profile = ref<UserProfile | null>(null);
const errorMessage = ref("");
const successMessage = ref("");
const email = ref("");
const appearanceStore = useAppearanceStore();
const localeStore = useLocaleStore();
const { t } = useI18n();

async function loadProfile(): Promise<void> {
  try {
    profile.value = await getProfile();
    email.value = profile.value.email;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("profile.account.loadError");
  }
}

async function saveProfile(): Promise<void> {
  errorMessage.value = "";
  successMessage.value = "";

  try {
    profile.value = await updateProfile(email.value);
    successMessage.value = t("profile.account.updateSuccess");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("profile.account.updateError");
  }
}

onMounted(() => {
  void loadProfile();
});
</script>

<template>
  <div class="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
    <PageSection :title="t('profile.account.title')" :subtitle="t('profile.account.subtitle')">
      <div v-if="profile" class="space-y-6">
        <div class="grid gap-4 sm:grid-cols-2">
          <div class="rounded-2xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("profile.account.username") }}</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ profile.username }}</p>
          </div>
          <div class="rounded-2xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("profile.account.role") }}</p>
            <p class="mt-2 text-lg font-semibold capitalize text-slate-900">{{ t(`common.roles.${profile.role}`) }}</p>
          </div>
          <div class="rounded-2xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("profile.account.uploaded") }}</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ formatBytes(profile.uploaded_bytes) }}</p>
          </div>
          <div class="rounded-2xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("profile.account.downloaded") }}</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ formatBytes(profile.downloaded_bytes) }}</p>
          </div>
        </div>

        <div class="grid gap-4">
          <label class="block">
            <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.account.email") }}</span>
            <input v-model="email" type="email" class="w-full rounded-xl border border-slate-300 px-4 py-3" />
          </label>
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="rounded-2xl border border-slate-200 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("profile.account.trackerCredential") }}</p>
              <p class="mt-3 break-all font-mono text-sm text-slate-700">{{ profile.tracker_credential }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("profile.account.rssKey") }}</p>
              <p class="mt-3 break-all font-mono text-sm text-slate-700">{{ profile.rss_key }}</p>
            </div>
          </div>
        </div>

        <p v-if="errorMessage" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ errorMessage }}</p>
        <p v-if="successMessage" class="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{{ successMessage }}</p>

        <button class="rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white" @click="saveProfile">
          {{ t("profile.account.save") }}
        </button>
      </div>
    </PageSection>

    <PageSection :title="t('profile.appearance.title')" :subtitle="t('profile.appearance.subtitle')">
      <div class="space-y-4">
        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.locale") }}</span>
          <select v-model="localeStore.locale" class="w-full rounded-xl border border-slate-300 px-4 py-3">
            <option v-for="option in localeStore.options" :key="option.code" :value="option.code">
              {{ option.nativeLabel }}
            </option>
          </select>
          <p class="mt-2 text-sm text-slate-500">{{ t("profile.appearance.localeDescription") }}</p>
        </label>

        <label class="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-3">
          <span class="text-sm font-medium text-slate-700">{{ t("profile.appearance.reducedMotion") }}</span>
          <input v-model="appearanceStore.state.reducedMotion" type="checkbox" class="h-4 w-4" />
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.backgroundMode") }}</span>
          <select v-model="appearanceStore.state.backgroundMode" class="w-full rounded-xl border border-slate-300 px-4 py-3">
            <option value="solid">{{ t("profile.appearance.backgroundModes.solid") }}</option>
            <option value="image">{{ t("profile.appearance.backgroundModes.image") }}</option>
          </select>
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.backgroundImageUrl") }}</span>
          <input
            v-model="appearanceStore.state.backgroundImageUrl"
            class="w-full rounded-xl border border-slate-300 px-4 py-3"
            :placeholder="t('profile.appearance.backgroundImagePlaceholder')"
          />
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.listDensity") }}</span>
          <select v-model="appearanceStore.state.listDensity" class="w-full rounded-xl border border-slate-300 px-4 py-3">
            <option value="comfortable">{{ t("profile.appearance.listDensityOptions.comfortable") }}</option>
            <option value="compact">{{ t("profile.appearance.listDensityOptions.compact") }}</option>
          </select>
        </label>

        <div class="rounded-2xl border border-slate-200 p-4">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="text-sm font-semibold text-slate-900">{{ t("profile.appearance.authThemeTitle") }}</p>
              <p class="mt-1 text-sm text-slate-500">{{ t("profile.appearance.authThemeDescription") }}</p>
            </div>
            <button
              class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700"
              @click="appearanceStore.resetAuthPageStyle"
            >
              {{ t("profile.appearance.resetAuthTheme") }}
            </button>
          </div>

          <div class="mt-4 space-y-4">
            <label class="block">
              <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.themePreset") }}</span>
              <select v-model="appearanceStore.state.authThemePreset" class="w-full rounded-xl border border-slate-300 px-4 py-3">
                <option v-for="preset in AUTH_THEME_PRESETS" :key="preset.id" :value="preset.id">
                  {{ t(preset.labelKey) }}
                </option>
              </select>
            </label>

            <label class="block">
              <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.accentColor") }}</span>
              <input v-model="appearanceStore.state.authAccentColor" type="color" class="h-12 w-20 rounded-xl border border-slate-300 bg-white p-2" />
            </label>

            <label class="block">
              <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.authBackgroundImageUrl") }}</span>
              <input v-model="appearanceStore.state.authBackgroundImageUrl" class="w-full rounded-xl border border-slate-300 px-4 py-3" />
            </label>
          </div>
        </div>
      </div>
    </PageSection>
  </div>
</template>
