<script setup lang="ts">
import { onMounted, ref } from "vue";

import { getAdminSiteSettings, runTrackerSync, updateAdminSiteSettings, type AdminTrackerSyncResult } from "@/api/admin";
import PageSection from "@/components/PageSection.vue";
import { useI18n } from "@/composables/useI18n";
import { useSiteStore } from "@/stores/site";


const brandingLoading = ref(false);
const brandingSaving = ref(false);
const brandingError = ref("");
const brandingSuccess = ref("");
const siteName = ref("");
const syncing = ref(false);
const syncResult = ref<AdminTrackerSyncResult | null>(null);
const errorMessage = ref("");
const internalAdminHref = import.meta.env.DEV ? "http://localhost:8000/internal-admin" : "/internal-admin";
const { t } = useI18n();
const siteStore = useSiteStore();

async function loadSiteBranding(): Promise<void> {
  brandingLoading.value = true;
  brandingError.value = "";

  try {
    const response = await getAdminSiteSettings();
    siteName.value = response.site_name;
    siteStore.setSiteName(response.site_name);
  } catch (error) {
    brandingError.value = error instanceof Error ? error.message : t("admin.branding.loadError");
  } finally {
    brandingLoading.value = false;
  }
}

async function saveSiteBranding(): Promise<void> {
  brandingSaving.value = true;
  brandingError.value = "";
  brandingSuccess.value = "";

  try {
    const response = await updateAdminSiteSettings(siteName.value);
    siteName.value = response.site_name;
    siteStore.setSiteName(response.site_name);
    brandingSuccess.value = t("admin.branding.saveSuccess");
  } catch (error) {
    brandingError.value = error instanceof Error ? error.message : t("admin.branding.saveError");
  } finally {
    brandingSaving.value = false;
  }
}

async function syncTracker(): Promise<void> {
  syncing.value = true;
  errorMessage.value = "";

  try {
    syncResult.value = await runTrackerSync();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("admin.trackerSync.errorFallback");
  } finally {
    syncing.value = false;
  }
}

onMounted(() => {
  void loadSiteBranding();
});
</script>

<template>
  <div class="grid gap-6 xl:grid-cols-[1fr,1fr]">
    <div class="space-y-6">
      <PageSection :title="t('admin.branding.title')" :subtitle="t('admin.branding.subtitle')">
        <div class="space-y-4">
          <label class="block">
            <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("admin.branding.fieldLabel") }}</span>
            <input
              v-model="siteName"
              class="w-full rounded-xl border border-slate-300 px-4 py-3"
              :placeholder="t('admin.branding.placeholder')"
              :disabled="brandingLoading || brandingSaving"
            />
          </label>

          <p class="text-sm leading-7 text-slate-600">{{ t("admin.branding.description") }}</p>

          <p v-if="brandingError" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ brandingError }}</p>
          <p v-if="brandingSuccess" class="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{{ brandingSuccess }}</p>

          <button
            class="rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="brandingLoading || brandingSaving"
            @click="saveSiteBranding"
          >
            {{ brandingSaving ? t("admin.branding.saveLoading") : t("admin.branding.save") }}
          </button>
        </div>
      </PageSection>

      <PageSection :title="t('admin.trackerSync.title')" :subtitle="t('admin.trackerSync.subtitle')">
        <div class="space-y-4">
          <button
            class="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-blue-600 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="syncing"
            @click="syncTracker"
          >
            {{ syncing ? t("admin.trackerSync.buttonLoading") : t("admin.trackerSync.button") }}
          </button>

          <p v-if="errorMessage" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
            {{ errorMessage }}
          </p>

          <div v-if="syncResult" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-900">{{ syncResult.message }}</p>
            <div class="mt-3 grid gap-3 sm:grid-cols-3">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("admin.trackerSync.userStats") }}</p>
                <p class="mt-1 text-lg font-semibold text-slate-900">{{ syncResult.user_stats_updated }}</p>
              </div>
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("admin.trackerSync.torrentStats") }}</p>
                <p class="mt-1 text-lg font-semibold text-slate-900">{{ syncResult.torrent_stats_updated }}</p>
              </div>
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("admin.trackerSync.skipped") }}</p>
                <p class="mt-1 text-lg font-semibold text-slate-900">{{ syncResult.skipped ? t("common.yes") : t("common.no") }}</p>
              </div>
            </div>
          </div>
        </div>
      </PageSection>
    </div>

    <PageSection :title="t('admin.internalAdmin.title')" :subtitle="t('admin.internalAdmin.subtitle')">
      <div class="space-y-4">
        <p class="text-sm leading-7 text-slate-600">{{ t("admin.internalAdmin.body") }}</p>
        <a
          :href="internalAdminHref"
          class="inline-flex rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          {{ t("admin.internalAdmin.open") }}
        </a>
        <p class="text-xs leading-6 text-slate-500">{{ t("admin.internalAdmin.footnote") }}</p>
      </div>
    </PageSection>
  </div>
</template>
