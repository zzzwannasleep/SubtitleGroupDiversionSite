<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import AppCard from '@/components/app/AppCard.vue';
import AppNotFound from '@/components/app/AppNotFound.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import { listReleases, listTags } from '@/services/releases';
import type { Release, Tag } from '@/types/release';

const route = useRoute();
const tag = ref<Tag | null>(null);
const releases = ref<Release[]>([]);

const hasData = computed(() => !!tag.value);

onMounted(async () => {
  const allTags = await listTags();
  tag.value = allTags.find((item) => item.slug === route.params.slug) ?? null;

  if (tag.value) {
    const data = await listReleases({ tag: tag.value.slug });
    releases.value = data.results;
  }
});
</script>

<template>
  <AppNotFound v-if="!hasData" />
  <template v-else>
    <AppPageHeader :title="`标签：${tag!.name}`" description="标签页用于快速追更和 RSS 精准订阅。" />
    <AppCard :title="`${tag!.name} 相关资源`" :description="`当前展示 ${releases.length} 条资源。`">
      <ReleaseListTable :releases="releases">
        <template #actions="{ release }">
          <UiButton :to="`/releases/${release.id}`" size="sm">详情</UiButton>
        </template>
      </ReleaseListTable>
    </AppCard>
  </template>
</template>
