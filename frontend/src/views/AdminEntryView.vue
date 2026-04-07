<script setup lang="ts">
import { onMounted, ref } from "vue";

import {
  getAdminSiteSettings,
  listAdminAuditLogs,
  runTrackerSync,
  updateAdminSiteSettings,
  type AdminAuditLogItem,
  type AdminTrackerSyncResult,
} from "@/api/admin";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import PageSection from "@/components/PageSection.vue";
import { useI18n } from "@/composables/useI18n";
import { useSiteStore } from "@/stores/site";
import { useToastStore } from "@/stores/toast";
import { formatDate } from "@/utils/format";


const brandingLoading = ref(false);
const brandingSaving = ref(false);
const brandingError = ref("");
const brandingSuccess = ref("");
const siteName = ref("");
const syncing = ref(false);
const trackerSyncConfirmOpen = ref(false);
const syncResult = ref<AdminTrackerSyncResult | null>(null);
const errorMessage = ref("");
const auditLogs = ref<AdminAuditLogItem[]>([]);
const auditLoading = ref(false);
const auditError = ref("");
const internalAdminHref = import.meta.env.DEV ? "http://localhost:8000/internal-admin" : "/internal-admin";
const { locale, t } = useI18n();
const siteStore = useSiteStore();
const toastStore = useToastStore();

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatChange(value: unknown): string {
  if (!isRecord(value) || !("from" in value) || !("to" in value)) {
    return String(value);
  }
  return `${String(value.from)} -> ${String(value.to)}`;
}

function formatAuditActor(log: AdminAuditLogItem): string {
  return log.actor?.username ?? t("admin.auditLog.systemActor");
}

function formatAuditTarget(log: AdminAuditLogItem): string {
  return log.target_id === null ? log.target_type : `${log.target_type} #${log.target_id}`;
}

function formatAuditDetails(log: AdminAuditLogItem): string {
  if (!log.details) {
    return t("admin.auditLog.noDetails");
  }

  const changes = log.details.changes;
  if (isRecord(changes)) {
    return Object.entries(changes)
      .map(([field, change]) => `${field}: ${formatChange(change)}`)
      .join("; ");
  }

  const result = log.details.result;
  if (isRecord(result) && typeof result.message === "string") {
    return result.message;
  }

  return JSON.stringify(log.details);
}

async function loadAuditLogs(): Promise<void> {
  auditLoading.value = true;
  auditError.value = "";

  try {
    const response = await listAdminAuditLogs();
    auditLogs.value = response.items;
  } catch (error) {
    auditError.value = error instanceof Error ? error.message : t("admin.auditLog.loadError");
  } finally {
    auditLoading.value = false;
  }
}

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
    toastStore.success(t("toasts.siteNameSaved"));
    await loadAuditLogs();
  } catch (error) {
    brandingError.value = error instanceof Error ? error.message : t("admin.branding.saveError");
  } finally {
    brandingSaving.value = false;
  }
}

async function syncTracker(): Promise<void> {
  trackerSyncConfirmOpen.value = false;
  syncing.value = true;
  errorMessage.value = "";

  try {
    syncResult.value = await runTrackerSync();
    toastStore.success(t("toasts.trackerSyncFinished"));
    await loadAuditLogs();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("admin.trackerSync.errorFallback");
  } finally {
    syncing.value = false;
  }
}

function requestTrackerSync(): void {
  if (syncing.value) {
    return;
  }

  trackerSyncConfirmOpen.value = true;
}

onMounted(() => {
  void loadSiteBranding();
  void loadAuditLogs();
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
            @click="requestTrackerSync"
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

    <div class="space-y-6">
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

      <PageSection :title="t('admin.auditLog.title')" :subtitle="t('admin.auditLog.subtitle')">
        <div class="space-y-4">
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm leading-6 text-slate-600">{{ t("admin.auditLog.description") }}</p>
            <button
              class="shrink-0 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-blue-600 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="auditLoading"
              @click="loadAuditLogs"
            >
              {{ auditLoading ? t("admin.auditLog.refreshing") : t("admin.auditLog.refresh") }}
            </button>
          </div>

          <p v-if="auditError" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ auditError }}</p>
          <p v-else-if="auditLoading && auditLogs.length === 0" class="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
            {{ t("admin.auditLog.loading") }}
          </p>
          <p v-else-if="auditLogs.length === 0" class="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
            {{ t("admin.auditLog.empty") }}
          </p>

          <div v-else class="space-y-3">
            <article v-for="log in auditLogs" :key="log.id" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <p class="text-sm font-semibold text-slate-900">{{ log.action }}</p>
                <p class="text-xs text-slate-500">{{ formatDate(log.created_at, locale) }}</p>
              </div>
              <p class="mt-2 text-sm leading-6 text-slate-600">{{ formatAuditDetails(log) }}</p>
              <p class="mt-3 text-xs leading-6 text-slate-500">
                {{ t("admin.auditLog.actor") }}: {{ formatAuditActor(log) }}
                <span class="mx-1 text-slate-300">/</span>
                {{ t("admin.auditLog.target") }}: {{ formatAuditTarget(log) }}
                <span v-if="log.ip">
                  <span class="mx-1 text-slate-300">/</span>
                  IP: {{ log.ip }}
                </span>
              </p>
            </article>
          </div>
        </div>
      </PageSection>
    </div>

    <ConfirmDialog
      v-model:open="trackerSyncConfirmOpen"
      :title="t('admin.trackerSync.confirmTitle')"
      :description="t('admin.trackerSync.confirmDescription')"
      :confirm-label="t('admin.trackerSync.confirm')"
      :busy="syncing"
      @confirm="syncTracker"
    />
  </div>
</template>
