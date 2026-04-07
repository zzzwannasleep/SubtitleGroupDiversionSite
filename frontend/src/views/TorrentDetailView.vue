<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { downloadTorrentFile, getTorrentDetail } from "@/api/torrents";
import EmptyState from "@/components/EmptyState.vue";
import PageSection from "@/components/PageSection.vue";
import TorrentStatBadge from "@/components/TorrentStatBadge.vue";
import { useI18n } from "@/composables/useI18n";
import { useToastStore } from "@/stores/toast";
import type { TorrentDetail } from "@/types";
import { formatBytes, formatDate } from "@/utils/format";


const route = useRoute();
const loading = ref(false);
const downloading = ref(false);
const loadErrorMessage = ref("");
const actionErrorMessage = ref("");
const torrent = ref<TorrentDetail | null>(null);
const { locale, t } = useI18n();
const toastStore = useToastStore();

async function loadTorrent(): Promise<void> {
  loading.value = true;
  loadErrorMessage.value = "";
  actionErrorMessage.value = "";
  torrent.value = null;

  try {
    torrent.value = await getTorrentDetail(Number(route.params.id));
  } catch (error) {
    loadErrorMessage.value = error instanceof Error ? error.message : t("torrentDetail.loadError");
  } finally {
    loading.value = false;
  }
}

async function download(): Promise<void> {
  if (!torrent.value) {
    return;
  }

  downloading.value = true;
  actionErrorMessage.value = "";
  try {
    const blob = await downloadTorrentFile(torrent.value.id);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${torrent.value.info_hash}.torrent`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    toastStore.success(t("toasts.downloadStarted"));
  } catch (error) {
    actionErrorMessage.value = error instanceof Error ? error.message : t("torrentDetail.downloadError");
  } finally {
    downloading.value = false;
  }
}

onMounted(loadTorrent);
watch(() => route.params.id, loadTorrent);
</script>

<template>
  <div v-if="loading" class="space-y-4">
    <div class="h-32 animate-pulse rounded-2xl bg-white shadow-sm" />
    <div class="h-80 animate-pulse rounded-2xl bg-white shadow-sm" />
  </div>

  <div v-else-if="loadErrorMessage">
    <EmptyState :title="t('torrentDetail.unavailable')" :description="loadErrorMessage" />
  </div>

  <div v-else-if="torrent" class="space-y-6">
    <p v-if="actionErrorMessage" class="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ actionErrorMessage }}
    </p>
    <PageSection :title="torrent.name" :subtitle="torrent.subtitle ?? t('torrentDetail.defaultSubtitle')">
      <div class="flex flex-wrap gap-3">
        <TorrentStatBadge :label="t('torrentDetail.seeders')" :value="torrent.stats.seeders" tone="success" />
        <TorrentStatBadge :label="t('torrentDetail.leechers')" :value="torrent.stats.leechers" />
        <TorrentStatBadge :label="t('torrentDetail.snatches')" :value="torrent.stats.snatches" tone="warn" />
        <span
          v-if="torrent.is_free"
          class="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-700"
        >
          {{ t("torrentDetail.freeleech") }}
        </span>
      </div>
      <div class="mt-6 grid gap-4 lg:grid-cols-[2fr,1fr]">
        <div class="rounded-2xl bg-slate-50 p-4">
          <h3 class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("torrentDetail.description") }}</h3>
          <p class="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">
            {{ torrent.description || t("torrentDetail.noDescription") }}
          </p>
        </div>
        <div class="rounded-2xl bg-slate-50 p-4">
          <h3 class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("torrentDetail.overview") }}</h3>
          <dl class="mt-3 space-y-3 text-sm text-slate-700">
            <div class="flex justify-between gap-3">
              <dt>{{ t("torrentDetail.category") }}</dt>
              <dd>{{ torrent.category.name }}</dd>
            </div>
            <div class="flex justify-between gap-3">
              <dt>{{ t("torrentDetail.uploader") }}</dt>
              <dd>{{ torrent.owner.username }}</dd>
            </div>
            <div class="flex justify-between gap-3">
              <dt>{{ t("torrentDetail.size") }}</dt>
              <dd>{{ formatBytes(torrent.size_bytes) }}</dd>
            </div>
            <div class="flex justify-between gap-3">
              <dt>{{ t("torrentDetail.created") }}</dt>
              <dd>{{ formatDate(torrent.created_at, locale) }}</dd>
            </div>
          </dl>
          <button
            class="mt-6 w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white"
            :disabled="downloading"
            @click="download"
          >
            {{ downloading ? t("torrentDetail.preparing") : t("torrentDetail.download") }}
          </button>
        </div>
      </div>
    </PageSection>

    <PageSection :title="t('torrentDetail.files')" :subtitle="t('torrentDetail.filesSubtitle')">
      <div v-if="torrent.files.length" class="divide-y divide-slate-200 rounded-2xl border border-slate-200">
        <div v-for="file in torrent.files" :key="file.file_path" class="flex items-center justify-between gap-3 px-4 py-3 text-sm">
          <span class="truncate text-slate-700">{{ file.file_path }}</span>
          <span class="shrink-0 text-slate-500">{{ formatBytes(file.file_size_bytes) }}</span>
        </div>
      </div>
      <EmptyState v-else :title="t('torrentDetail.noFiles')" :description="t('torrentDetail.noFilesDescription')" />
    </PageSection>

    <PageSection :title="t('torrentDetail.mediaInfo')" :subtitle="t('torrentDetail.mediaInfoSubtitle')">
      <pre class="overflow-x-auto rounded-2xl bg-slate-950/95 p-4 text-sm text-slate-100">{{
        torrent.media_info || t("torrentDetail.mediaInfoEmpty")
      }}</pre>
    </PageSection>

    <PageSection :title="t('torrentDetail.nfo')" :subtitle="t('torrentDetail.nfoSubtitle')">
      <pre class="overflow-x-auto rounded-2xl bg-slate-950/95 p-4 text-sm text-slate-100">{{
        torrent.nfo_text || t("torrentDetail.nfoEmpty")
      }}</pre>
    </PageSection>
  </div>
</template>
