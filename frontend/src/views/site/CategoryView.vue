<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import AppCard from '@/components/app/AppCard.vue';
import AppNotFound from '@/components/app/AppNotFound.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import { listCategories, listReleases } from '@/services/releases';
import type { Category, Release } from '@/types/release';

const route = useRoute();
const category = ref<Category | null>(null);
const releases = ref<Release[]>([]);

const hasData = computed(() => !!category.value);

onMounted(async () => {
  const allCategories = await listCategories();
  category.value = allCategories.find((item) => item.slug === route.params.slug) ?? null;

  if (category.value) {
    const data = await listReleases({ category: category.value.slug });
    releases.value = data.results;
  }
});
</script>

<template>
  <AppNotFound v-if="!hasData" />
  <template v-else>
    <AppPageHeader :title="category!.name" description="分类页沿用资源列表模式，但预置当前分类过滤。" />
    <AppCard :title="`${category!.name} 下的资源`" :description="`当前展示 ${releases.length} 条资源。`">
      <ReleaseListTable :releases="releases">
        <template #actions="{ release }">
          <UiButton :to="`/releases/${release.id}`" size="sm">详情</UiButton>
        </template>
      </ReleaseListTable>
    </AppCard>
  </template>
</template>

