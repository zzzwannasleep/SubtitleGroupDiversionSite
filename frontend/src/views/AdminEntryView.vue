<script setup lang="ts">
import { ref } from "vue";

import { runTrackerSync, type AdminTrackerSyncResult } from "@/api/admin";
import PageSection from "@/components/PageSection.vue";


const syncing = ref(false);
const syncResult = ref<AdminTrackerSyncResult | null>(null);
const errorMessage = ref("");
const internalAdminHref = import.meta.env.DEV ? "http://localhost:8000/internal-admin" : "/internal-admin";

async function syncTracker(): Promise<void> {
  syncing.value = true;
  errorMessage.value = "";

  try {
    syncResult.value = await runTrackerSync();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Failed to sync tracker stats";
  } finally {
    syncing.value = false;
  }
}
</script>

<template>
  <div class="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
    <PageSection title="Internal Admin" subtitle="SQLAdmin handles category, torrent, and user operations for MVP.">
      <div class="space-y-4">
        <p class="text-sm leading-7 text-slate-600">
          The internal admin panel runs on the backend and uses the same admin username or email plus password.
        </p>
        <a
          :href="internalAdminHref"
          class="inline-flex rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          Open internal admin
        </a>
        <p class="text-xs leading-6 text-slate-500">
          Use this panel for quick CRUD work. Uploading new torrents should still go through the dedicated upload page.
        </p>
      </div>
    </PageSection>

    <PageSection title="Tracker Sync" subtitle="Manual pull sync for tracker stats cache until the XBT/Torrust PoC is finalized.">
      <div class="space-y-4">
        <button
          class="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-blue-600 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="syncing"
          @click="syncTracker"
        >
          {{ syncing ? "Syncing..." : "Run tracker sync" }}
        </button>

        <p v-if="errorMessage" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          {{ errorMessage }}
        </p>

        <div v-if="syncResult" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p class="text-sm font-semibold text-slate-900">{{ syncResult.message }}</p>
          <div class="mt-3 grid gap-3 sm:grid-cols-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">User stats</p>
              <p class="mt-1 text-lg font-semibold text-slate-900">{{ syncResult.user_stats_updated }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Torrent stats</p>
              <p class="mt-1 text-lg font-semibold text-slate-900">{{ syncResult.torrent_stats_updated }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Skipped</p>
              <p class="mt-1 text-lg font-semibold text-slate-900">{{ syncResult.skipped ? "Yes" : "No" }}</p>
            </div>
          </div>
        </div>
      </div>
    </PageSection>
  </div>
</template>
