<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import ReleaseFiltersPanel from '@/components/release/ReleaseFiltersPanel.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import { downloadRelease, listCategories, listReleases, listTags } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import { useReleaseFiltersStore } from '@/stores/releaseFilters';
import type { Category, Release, Tag } from '@/types/release';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const filters = useReleaseFiltersStore();
const PAGE_SIZE = 5;

const loading = ref(true);
const failed = ref(false);
const releases = ref<Release[]>([]);
const categories = ref<Category[]>([]);
const tags = ref<Tag[]>([]);
const count = ref(0);

const getString = (value: unknown) => (typeof value === 'string' ? value : '');
const sortLabels: Record<'latest' | 'downloads' | 'completions', string> = {
  latest: '最新发布',
  downloads: '下载次数',
  completions: '完成次数',
};

const pageCount = computed(() => Math.max(1, Math.ceil(count.value / PAGE_SIZE)));
const resultSummary = computed(() => `共 ${count.value} 条，当前按${sortLabels[filters.sort]}排序`);
const activeFilters = computed(() => {
  const items: Array<{ key: 'q' | 'category' | 'tag'; label: string }> = [];

  if (filters.q) {
    items.push({ key: 'q', label: `关键词：${filters.q}` });
  }

  if (filters.category) {
    const category = categories.value.find((item) => item.slug === filters.category);
    items.push({ key: 'category', label: `分类：${category?.name ?? filters.category}` });
  }

  if (filters.tag) {
    const tag = tags.value.find((item) => item.slug === filters.tag);
    items.push({ key: 'tag', label: `标签：${tag?.name ?? filters.tag}` });
  }

  return items;
});

const handleSortUpdate = (value: string) => {
  filters.sort = (value as 'latest' | 'downloads' | 'completions') || 'latest';
};

async function loadMeta() {
  [categories.value, tags.value] = await Promise.all([listCategories(), listTags()]);
}

async function loadList() {
  loading.value = true;
  failed.value = false;

  try {
    const data = await listReleases({ ...filters.toQuery(), pageSize: PAGE_SIZE });
    releases.value = data.results;
    count.value = data.count;
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

async function syncFromRoute() {
  filters.hydrate({
    q: getString(route.query.q),
    category: getString(route.query.category),
    tag: getString(route.query.tag),
    sort: (getString(route.query.sort) as 'latest' | 'downloads' | 'completions') || 'latest',
    page: Number(getString(route.query.page) || 1),
  });
  await loadList();
}

async function applyFilters() {
  await router.push({
    name: 'release-list',
    query: {
      q: filters.q || undefined,
      category: filters.category || undefined,
      tag: filters.tag || undefined,
      sort: filters.sort,
      page: filters.page > 1 ? String(filters.page) : undefined,
    },
  });
}

async function submitFilters() {
  filters.page = 1;
  await applyFilters();
}

async function resetFilters() {
  filters.reset();
  await applyFilters();
}

async function clearSingleFilter(key: 'q' | 'category' | 'tag') {
  filters[key] = '';
  filters.page = 1;
  await applyFilters();
}

async function changePage(nextPage: number) {
  filters.page = nextPage;
  await applyFilters();
}

onMounted(async () => {
  await loadMeta();
});

watch(() => route.fullPath, syncFromRoute, { immediate: true });
</script>

<template>
  <AppPageHeader title="资源">
    <template #actions>
      <UiButton
        v-if="authStore.currentUser?.role === 'uploader' || authStore.currentUser?.role === 'admin'"
        to="/upload"
        variant="primary"
      >
        上传种子
      </UiButton>
    </template>
  </AppPageHeader>

  <ReleaseFiltersPanel
    :q="filters.q"
    :category="filters.category"
    :tag="filters.tag"
    :sort="filters.sort"
    :categories="categories"
    :tags="tags"
    @update:q="filters.q = $event"
    @update:category="filters.category = $event"
    @update:tag="filters.tag = $event"
    @update:sort="handleSortUpdate"
    @apply="submitFilters"
    @reset="resetFilters"
  />

  <div v-if="activeFilters.length" class="flex flex-wrap items-center gap-2">
    <button
      v-for="item in activeFilters"
      :key="item.label"
      type="button"
      class="inline-flex items-center gap-2 rounded-full bg-slate-200 px-3 py-1.5 text-sm text-slate-700 transition hover:bg-slate-300"
      @click="clearSingleFilter(item.key)"
    >
      {{ item.label }}
      <span class="text-xs text-slate-500">移除</span>
    </button>
    <UiButton variant="ghost" size="sm" @click="resetFilters">清空</UiButton>
  </div>

  <AppLoading v-if="loading" />
  <AppError v-else-if="failed" title="资源加载失败" description="请稍后重试。" />
  <AppCard v-else-if="!releases.length" title="资源列表">
    <AppEmpty title="没有匹配结果" description="调整筛选后再试。">
      <template #actions>
        <UiButton variant="secondary" @click="resetFilters">重置筛选</UiButton>
      </template>
    </AppEmpty>
  </AppCard>
  <AppCard v-else title="资源列表">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-500">
      <p>{{ resultSummary }}</p>
      <p>第 {{ filters.page }} / {{ pageCount }} 页</p>
    </div>
    <ReleaseListTable :releases="releases">
      <template #actions="{ release }">
        <UiButton variant="secondary" size="sm" @click="downloadRelease(release.id)">下载</UiButton>
        <UiButton :to="`/releases/${release.id}`" size="sm">详情</UiButton>
      </template>
    </ReleaseListTable>
    <template #footer>
      <div class="flex items-center justify-between gap-3">
        <p class="text-sm text-slate-500">第 {{ filters.page }} 页，共 {{ pageCount }} 页</p>
        <div class="flex gap-2">
          <UiButton :disabled="filters.page <= 1" variant="ghost" @click="changePage(filters.page - 1)">上一页</UiButton>
          <UiButton :disabled="filters.page >= pageCount" variant="ghost" @click="changePage(filters.page + 1)">下一页</UiButton>
        </div>
      </div>
    </template>
  </AppCard>
</template>
