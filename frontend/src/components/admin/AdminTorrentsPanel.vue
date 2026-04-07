<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";

import {
  listAdminCategories,
  listAdminTorrents,
  updateAdminTorrent,
  type AdminCategoryItem,
  type AdminTorrentItem,
} from "@/api/admin";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import { useI18n } from "@/composables/useI18n";
import { useToastStore } from "@/stores/toast";
import { formatDate } from "@/utils/format";


interface TorrentDraft {
  category_id: number;
  is_visible: boolean;
  is_free: boolean;
}


const categories = ref<AdminCategoryItem[]>([]);
const torrents = ref<AdminTorrentItem[]>([]);
const drafts = reactive<Record<number, TorrentDraft>>({});
const filters = reactive({
  keyword: "",
  category_id: "",
  is_visible: "",
});
const loading = ref(false);
const savingTorrentId = ref<number | null>(null);
const errorMessage = ref("");
const confirmOpen = ref(false);
const pendingTorrent = ref<AdminTorrentItem | null>(null);
const { locale, t } = useI18n();
const toastStore = useToastStore();

const pendingDraft = computed(() => (pendingTorrent.value ? drafts[pendingTorrent.value.id] : null));
const confirmTone = computed(() => {
  if (!pendingTorrent.value || !pendingDraft.value) {
    return "default";
  }
  return pendingTorrent.value.is_visible && !pendingDraft.value.is_visible ? "danger" : "default";
});

function syncDraft(torrent: AdminTorrentItem): void {
  drafts[torrent.id] = {
    category_id: torrent.category_id,
    is_visible: torrent.is_visible,
    is_free: torrent.is_free,
  };
}

function hasChanges(torrent: AdminTorrentItem): boolean {
  const draft = drafts[torrent.id];
  return Boolean(
    draft
      && (
        draft.category_id !== torrent.category_id
        || draft.is_visible !== torrent.is_visible
        || draft.is_free !== torrent.is_free
      ),
  );
}

async function loadCategories(): Promise<void> {
  try {
    categories.value = await listAdminCategories();
  } catch {
    categories.value = [];
  }
}

async function loadTorrents(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";

  try {
    const response = await listAdminTorrents({
      keyword: filters.keyword.trim() || undefined,
      category_id: filters.category_id ? Number(filters.category_id) : undefined,
      is_visible: filters.is_visible === "" ? undefined : filters.is_visible === "true",
      page_size: 30,
    });
    torrents.value = response.items;
    for (const torrent of response.items) {
      syncDraft(torrent);
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("admin.torrents.loadError");
  } finally {
    loading.value = false;
  }
}

function requestSave(torrent: AdminTorrentItem): void {
  if (!hasChanges(torrent) || savingTorrentId.value !== null) {
    return;
  }
  pendingTorrent.value = torrent;
  confirmOpen.value = true;
}

async function confirmSave(): Promise<void> {
  const torrent = pendingTorrent.value;
  const draft = pendingDraft.value;
  if (!torrent || !draft) {
    confirmOpen.value = false;
    return;
  }

  savingTorrentId.value = torrent.id;
  errorMessage.value = "";

  try {
    const updatedTorrent = await updateAdminTorrent(torrent.id, {
      category_id: draft.category_id,
      is_visible: draft.is_visible,
      is_free: draft.is_free,
    });
    torrents.value = torrents.value.map((item) => (item.id === updatedTorrent.id ? updatedTorrent : item));
    syncDraft(updatedTorrent);
    toastStore.success(t("toasts.adminTorrentUpdated"));
    confirmOpen.value = false;
    pendingTorrent.value = null;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("admin.torrents.updateError");
  } finally {
    savingTorrentId.value = null;
  }
}

onMounted(() => {
  void loadCategories();
  void loadTorrents();
});
</script>

<template>
  <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 class="text-lg font-semibold text-slate-950">{{ t("admin.torrents.title") }}</h2>
        <p class="mt-1 text-sm leading-6 text-slate-600">{{ t("admin.torrents.subtitle") }}</p>
      </div>
      <button
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-blue-600 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        type="button"
        :disabled="loading"
        @click="loadTorrents"
      >
        {{ loading ? t("admin.common.refreshing") : t("admin.common.refresh") }}
      </button>
    </div>

    <div class="mt-5 grid gap-3 lg:grid-cols-[1.4fr,1fr,1fr,auto]">
      <input
        v-model="filters.keyword"
        class="rounded-xl border border-slate-300 px-3 py-2"
        :placeholder="t('admin.torrents.keyword')"
        @keyup.enter="loadTorrents"
      />
      <select v-model="filters.category_id" class="rounded-xl border border-slate-300 px-3 py-2">
        <option value="">{{ t("admin.torrents.allCategories") }}</option>
        <option v-for="category in categories" :key="category.id" :value="String(category.id)">
          {{ category.name }}
        </option>
      </select>
      <select v-model="filters.is_visible" class="rounded-xl border border-slate-300 px-3 py-2">
        <option value="">{{ t("admin.torrents.allVisibility") }}</option>
        <option value="true">{{ t("admin.torrents.visible") }}</option>
        <option value="false">{{ t("admin.torrents.hidden") }}</option>
      </select>
      <button
        class="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
        type="button"
        @click="loadTorrents"
      >
        {{ t("admin.torrents.apply") }}
      </button>
    </div>

    <p v-if="errorMessage" class="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ errorMessage }}</p>
    <p v-else-if="loading && torrents.length === 0" class="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
      {{ t("admin.torrents.loading") }}
    </p>
    <p v-else-if="torrents.length === 0" class="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
      {{ t("admin.torrents.empty") }}
    </p>

    <div v-else class="mt-4 overflow-x-auto">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50 text-left text-slate-500">
          <tr>
            <th class="px-3 py-3 font-medium">{{ t("admin.torrents.name") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.torrents.category") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.torrents.owner") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.torrents.visible") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.torrents.free") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.torrents.created") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.torrents.actions") }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="torrent in torrents" :key="torrent.id" :class="{ 'bg-blue-50/40': hasChanges(torrent) }">
            <template v-if="drafts[torrent.id]">
              <td class="max-w-xs px-3 py-3">
                <RouterLink :to="`/torrents/${torrent.id}`" class="font-semibold text-slate-900 hover:text-blue-700">
                  {{ torrent.name }}
                </RouterLink>
                <p class="mt-1 font-mono text-xs text-slate-500">{{ torrent.info_hash }}</p>
              </td>
              <td class="px-3 py-3">
                <select v-model.number="drafts[torrent.id].category_id" class="rounded-xl border border-slate-300 px-3 py-2">
                  <option v-for="category in categories" :key="category.id" :value="category.id">
                    {{ category.name }}
                  </option>
                </select>
              </td>
              <td class="px-3 py-3 text-slate-600">{{ torrent.owner }}</td>
              <td class="px-3 py-3">
                <input v-model="drafts[torrent.id].is_visible" type="checkbox" class="h-4 w-4" />
              </td>
              <td class="px-3 py-3">
                <input v-model="drafts[torrent.id].is_free" type="checkbox" class="h-4 w-4" />
              </td>
              <td class="px-3 py-3 text-slate-600">{{ formatDate(torrent.created_at, locale) }}</td>
              <td class="px-3 py-3">
                <button
                  class="rounded-xl bg-blue-600 px-3 py-2 text-xs font-semibold text-white transition enabled:hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                  type="button"
                  :disabled="!hasChanges(torrent) || savingTorrentId !== null"
                  @click="requestSave(torrent)"
                >
                  {{ savingTorrentId === torrent.id ? t("admin.common.saving") : t("admin.common.save") }}
                </button>
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmDialog
      v-model:open="confirmOpen"
      :title="t('admin.torrents.confirmTitle')"
      :description="t('admin.torrents.confirmDescription')"
      :confirm-label="t('admin.torrents.confirm')"
      :tone="confirmTone"
      :busy="savingTorrentId !== null"
      @confirm="confirmSave"
    />
  </section>
</template>
