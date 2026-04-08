<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppNotFound from '@/components/app/AppNotFound.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import { listCategories, listReleases } from '@/services/releases';
import type { Category, Release } from '@/types/release';

const route = useRoute();
const loading = ref(true);
const failed = ref(false);
const category = ref<Category | null>(null);
const releases = ref<Release[]>([]);

const hasData = computed(() => !!category.value);

async function loadData() {
  loading.value = true;
  failed.value = false;

  try {
    const allCategories = await listCategories();
    category.value = allCategories.find((item) => item.slug === route.params.slug) ?? null;

    if (category.value) {
      const data = await listReleases({ category: category.value.slug });
      releases.value = data.results;
    }
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
</script>

<template>
  <AppLoading v-if="loading" />
  <AppError v-else-if="failed" title="分类页加载失败" description="请稍后重试，或检查分类与资源接口。" />
  <AppNotFound v-else-if="!hasData" />
  <template v-else>
    <AppPageHeader :title="category!.name" description="分类页沿用资源列表模式，但预置当前分类过滤。" />
    <AppCard :title="`${category!.name} 下的资源`" :description="`当前展示 ${releases.length} 条资源。`">
      <AppEmpty v-if="!releases.length" title="当前分类还没有资源" description="新的分类资源发布后会显示在这里。" />
      <ReleaseListTable v-else :releases="releases">
        <template #actions="{ release }">
          <UiButton :to="`/releases/${release.id}`" size="sm">详情</UiButton>
        </template>
      </ReleaseListTable>
    </AppCard>
  </template>
</template>
