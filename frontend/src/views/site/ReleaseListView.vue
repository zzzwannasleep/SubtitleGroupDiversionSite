<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AppAlert from '@/components/app/AppAlert.vue';
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
const resultDescription = computed(() =>
  `共 ${count.value} 条结果，本页展示 ${releases.value.length} 条，当前按「${sortLabels[filters.sort]}」排序。`,
);
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
    const data = await listReleases(filters.toQuery());
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
  <AppPageHeader title="资源列表" description="统一筛选条、列表卡片和分页区，保持浏览与下载路径清晰。">
    <template #actions>
      <UiButton
        v-if="authStore.currentUser?.role === 'uploader' || authStore.currentUser?.role === 'admin'"
        to="/upload"
        variant="primary"
      >
        上传资源
      </UiButton>
      <UiButton to="/rss" variant="secondary">查看 RSS</UiButton>
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

  <AppAlert
    v-if="activeFilters.length"
    variant="info"
    title="已应用筛选条件"
    :description="`当前结果会同时受到 ${activeFilters.length} 个条件影响。`"
  >
    <template #actions>
      <UiButton variant="ghost" size="sm" @click="resetFilters">清空全部</UiButton>
    </template>
  </AppAlert>

  <div class="grid gap-4 md:grid-cols-3">
    <div class="app-surface p-4">
      <p class="text-sm text-slate-500">结果总数</p>
      <p class="mt-3 text-2xl font-semibold text-slate-900">{{ count }}</p>
      <p class="mt-2 text-xs text-slate-500">筛选后会立即同步到 URL，方便回到当前结果集。</p>
    </div>
    <div class="app-surface p-4">
      <p class="text-sm text-slate-500">当前页码</p>
      <p class="mt-3 text-2xl font-semibold text-slate-900">{{ filters.page }} / {{ pageCount }}</p>
      <p class="mt-2 text-xs text-slate-500">每页保留较少条目，提升扫读效率。</p>
    </div>
    <div class="app-surface p-4">
      <p class="text-sm text-slate-500">排序方式</p>
      <p class="mt-3 text-2xl font-semibold text-slate-900">{{ sortLabels[filters.sort] }}</p>
      <p class="mt-2 text-xs text-slate-500">列表默认优先展示最新发布的资源。</p>
    </div>
  </div>

  <div v-if="activeFilters.length" class="flex flex-wrap gap-2">
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
  </div>

  <AppLoading v-if="loading" />
  <AppError v-else-if="failed" title="资源列表加载失败" description="请稍后重试，或检查资源接口状态。" />
  <AppCard v-else-if="!releases.length" title="资源结果" description="当前筛选条件下没有可展示的条目。">
    <AppEmpty title="没有匹配结果" description="调整关键词、分类或标签后再试一次。">
      <template #actions>
        <UiButton variant="secondary" @click="resetFilters">重置筛选</UiButton>
      </template>
    </AppEmpty>
  </AppCard>
  <AppCard v-else title="资源结果" :description="resultDescription">
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
