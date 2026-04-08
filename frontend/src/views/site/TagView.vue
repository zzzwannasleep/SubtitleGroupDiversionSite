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
import { listReleases, listTags } from '@/services/releases';
import type { Release, Tag } from '@/types/release';

const route = useRoute();
const loading = ref(true);
const failed = ref(false);
const tag = ref<Tag | null>(null);
const releases = ref<Release[]>([]);

const hasData = computed(() => !!tag.value);

async function loadData() {
  loading.value = true;
  failed.value = false;

  try {
    const allTags = await listTags();
    tag.value = allTags.find((item) => item.slug === route.params.slug) ?? null;

    if (tag.value) {
      const data = await listReleases({ tag: tag.value.slug });
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
  <AppError v-else-if="failed" title="标签页加载失败" description="请稍后重试，或检查标签与资源接口。" />
  <AppNotFound v-else-if="!hasData" />
  <template v-else>
    <AppPageHeader :title="`标签：${tag!.name}`" description="标签页用于快速追更和 RSS 精准订阅。" />
    <AppCard :title="`${tag!.name} 相关资源`" :description="`当前展示 ${releases.length} 条资源。`">
      <AppEmpty v-if="!releases.length" title="当前标签还没有资源" description="关联此标签的资源稍后会显示在这里。" />
      <ReleaseListTable v-else :releases="releases">
        <template #actions="{ release }">
          <UiButton :to="`/releases/${release.id}`" size="sm">详情</UiButton>
        </template>
      </ReleaseListTable>
    </AppCard>
  </template>
</template>
