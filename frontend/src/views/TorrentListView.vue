<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { listCategories } from "@/api/categories";
import { listTorrents } from "@/api/torrents";
import EmptyState from "@/components/EmptyState.vue";
import PageSection from "@/components/PageSection.vue";
import TorrentTable from "@/components/TorrentTable.vue";
import type { Category, TorrentListItem } from "@/types";


const route = useRoute();
const router = useRouter();

const filters = reactive({
  keyword: typeof route.query.keyword === "string" ? route.query.keyword : "",
  category: typeof route.query.category === "string" ? route.query.category : "",
  sort: typeof route.query.sort === "string" ? route.query.sort : "created_at_desc",
});

const items = ref<TorrentListItem[]>([]);
const total = ref(0);
const page = ref(Number(route.query.page ?? 1));
const loading = ref(false);
const errorMessage = ref("");
const categories = ref<Category[]>([]);

const listSummary = computed(() => `${total.value} torrents`);

async function loadCategories(): Promise<void> {
  try {
    categories.value = await listCategories();
  } catch {
    categories.value = [];
  }
}

async function loadTorrents(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";

  try {
    const response = await listTorrents({
      page: page.value,
      page_size: 20,
      keyword: filters.keyword || undefined,
      category: filters.category || undefined,
      sort: filters.sort,
    });
    items.value = response.items;
    total.value = response.total;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Failed to load torrents";
  } finally {
    loading.value = false;
  }
}

async function applyFilters(): Promise<void> {
  await router.push({
    path: "/torrents",
    query: {
      keyword: filters.keyword || undefined,
      category: filters.category || undefined,
      sort: filters.sort || undefined,
      page: 1,
    },
  });
}

watch(
  () => route.query,
  async (query) => {
    filters.keyword = typeof query.keyword === "string" ? query.keyword : "";
    filters.category = typeof query.category === "string" ? query.category : "";
    filters.sort = typeof query.sort === "string" ? query.sort : "created_at_desc";
    page.value = Number(query.page ?? 1);
    await loadTorrents();
  },
  { immediate: true },
);

void loadCategories();
</script>

<template>
  <div class="space-y-6">
    <PageSection title="Torrent Index" subtitle="Browse, filter, and compare available releases.">
      <div class="grid gap-4 lg:grid-cols-[2fr,1fr,1fr,auto]">
        <input
          v-model="filters.keyword"
          type="search"
          placeholder="Search by title or subtitle"
          class="rounded-xl border border-slate-300 px-4 py-3"
          @keyup.enter="applyFilters"
        />
        <select v-model="filters.category" class="rounded-xl border border-slate-300 px-4 py-3">
          <option value="">All categories</option>
          <option v-for="category in categories" :key="category.id" :value="category.slug">
            {{ category.name }}
          </option>
        </select>
        <select v-model="filters.sort" class="rounded-xl border border-slate-300 px-4 py-3">
          <option value="created_at_desc">Newest first</option>
          <option value="created_at_asc">Oldest first</option>
        </select>
        <button class="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white" @click="applyFilters">
          Apply
        </button>
      </div>
    </PageSection>

    <div class="flex items-center justify-between">
      <div>
        <p class="text-sm font-medium text-slate-500">Result</p>
        <h2 class="text-2xl font-semibold text-slate-900">{{ listSummary }}</h2>
      </div>
    </div>

    <p v-if="errorMessage" class="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ errorMessage }}</p>

    <div v-if="loading" class="grid gap-3">
      <div v-for="index in 4" :key="index" class="h-24 animate-pulse rounded-2xl bg-white shadow-sm" />
    </div>

    <EmptyState
      v-else-if="!items.length"
      title="No torrents yet"
      description="The list is empty right now. Once uploads are implemented, new torrents will appear here."
    />

    <TorrentTable v-else :items="items" />
  </div>
</template>

