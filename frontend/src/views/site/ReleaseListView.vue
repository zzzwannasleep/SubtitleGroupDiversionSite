<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import ReleaseFiltersPanel from '@/components/release/ReleaseFiltersPanel.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import { listCategories, listReleases, listTags } from '@/services/releases';
import { useReleaseFiltersStore } from '@/stores/releaseFilters';
import type { Category, Release, Tag } from '@/types/release';

const route = useRoute();
const router = useRouter();
const filters = useReleaseFiltersStore();

const loading = ref(true);
const failed = ref(false);
const releases = ref<Release[]>([]);
const categories = ref<Category[]>([]);
const tags = ref<Tag[]>([]);
const count = ref(0);

const getString = (value: unknown) => (typeof value === 'string' ? value : '');
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

async function resetFilters() {
  filters.reset();
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
  <AppPageHeader title="资源列表" description="统一筛选条 + 列表卡片 + 分页区的前台页面模式。">
    <template #actions>
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
    @apply="applyFilters"
    @reset="resetFilters"
  />

  <AppLoading v-if="loading" />
  <AppError v-else-if="failed" title="资源列表加载失败" />
  <AppCard v-else-if="!releases.length" title="资源结果" :description="`共 ${count} 条，当前页展示 0 条。`">
    <AppEmpty v-if="!releases.length" title="没有匹配结果" description="调整关键词、分类或标签后再试一次。" />
  </AppCard>
  <AppCard v-else title="资源结果" :description="`共 ${count} 条，当前页展示 ${releases.length} 条。`">
    <ReleaseListTable :releases="releases">
      <template #actions="{ release }">
        <UiButton :to="`/releases/${release.id}`" size="sm">详情</UiButton>
      </template>
    </ReleaseListTable>
    <template #footer>
      <div class="flex items-center justify-between gap-3">
        <p class="text-sm text-slate-500">页码 {{ filters.page }}</p>
        <div class="flex gap-2">
          <UiButton :disabled="filters.page <= 1" variant="ghost" @click="changePage(filters.page - 1)">上一页</UiButton>
          <UiButton :disabled="releases.length < 5" variant="ghost" @click="changePage(filters.page + 1)">下一页</UiButton>
        </div>
      </div>
    </template>
  </AppCard>
</template>
