<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { downloadTorrentFile, getTorrentDetail } from "@/api/torrents";
import EmptyState from "@/components/EmptyState.vue";
import PageSection from "@/components/PageSection.vue";
import TorrentStatBadge from "@/components/TorrentStatBadge.vue";
import type { TorrentDetail } from "@/types";
import { formatBytes, formatDate } from "@/utils/format";


const route = useRoute();
const loading = ref(false);
const downloading = ref(false);
const loadErrorMessage = ref("");
const actionErrorMessage = ref("");
const torrent = ref<TorrentDetail | null>(null);

async function loadTorrent(): Promise<void> {
  loading.value = true;
  loadErrorMessage.value = "";
  actionErrorMessage.value = "";
  torrent.value = null;

  try {
    torrent.value = await getTorrentDetail(Number(route.params.id));
  } catch (error) {
    loadErrorMessage.value = error instanceof Error ? error.message : "Failed to load torrent";
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
  } catch (error) {
    actionErrorMessage.value = error instanceof Error ? error.message : "Download failed";
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
    <EmptyState title="Torrent unavailable" :description="loadErrorMessage" />
  </div>

  <div v-else-if="torrent" class="space-y-6">
    <p v-if="actionErrorMessage" class="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ actionErrorMessage }}
    </p>
    <PageSection :title="torrent.name" :subtitle="torrent.subtitle ?? 'Torrent metadata and tracker-backed stats'">
      <div class="flex flex-wrap gap-3">
        <TorrentStatBadge label="Seeders" :value="torrent.stats.seeders" tone="success" />
        <TorrentStatBadge label="Leechers" :value="torrent.stats.leechers" />
        <TorrentStatBadge label="Snatches" :value="torrent.stats.snatches" tone="warn" />
        <span
          v-if="torrent.is_free"
          class="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-700"
        >
          Freeleech
        </span>
      </div>
      <div class="mt-6 grid gap-4 lg:grid-cols-[2fr,1fr]">
        <div class="rounded-2xl bg-slate-50 p-4">
          <h3 class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Description</h3>
          <p class="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">
            {{ torrent.description || "No description provided yet." }}
          </p>
        </div>
        <div class="rounded-2xl bg-slate-50 p-4">
          <h3 class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Overview</h3>
          <dl class="mt-3 space-y-3 text-sm text-slate-700">
            <div class="flex justify-between gap-3">
              <dt>Category</dt>
              <dd>{{ torrent.category.name }}</dd>
            </div>
            <div class="flex justify-between gap-3">
              <dt>Uploader</dt>
              <dd>{{ torrent.owner.username }}</dd>
            </div>
            <div class="flex justify-between gap-3">
              <dt>Size</dt>
              <dd>{{ formatBytes(torrent.size_bytes) }}</dd>
            </div>
            <div class="flex justify-between gap-3">
              <dt>Created</dt>
              <dd>{{ formatDate(torrent.created_at) }}</dd>
            </div>
          </dl>
          <button
            class="mt-6 w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white"
            :disabled="downloading"
            @click="download"
          >
            {{ downloading ? "Preparing..." : "Download torrent" }}
          </button>
        </div>
      </div>
    </PageSection>

    <PageSection title="Files" subtitle="Parsed file list from the torrent metadata.">
      <div v-if="torrent.files.length" class="divide-y divide-slate-200 rounded-2xl border border-slate-200">
        <div v-for="file in torrent.files" :key="file.file_path" class="flex items-center justify-between gap-3 px-4 py-3 text-sm">
          <span class="truncate text-slate-700">{{ file.file_path }}</span>
          <span class="shrink-0 text-slate-500">{{ formatBytes(file.file_size_bytes) }}</span>
        </div>
      </div>
      <EmptyState v-else title="No file list" description="The file list has not been parsed yet." />
    </PageSection>

    <PageSection title="Media Info" subtitle="Optional metadata blocks shown as plain text in MVP.">
      <pre class="overflow-x-auto rounded-2xl bg-slate-950/95 p-4 text-sm text-slate-100">{{ torrent.media_info || "N/A" }}</pre>
    </PageSection>
  </div>
</template>
