<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import { listAdminReleases, toggleReleaseStatus } from '@/services/releases';
import type { Release } from '@/types/release';

const releases = ref<Release[]>([]);
const status = ref<'all' | 'published' | 'draft' | 'hidden'>('all');
const loading = ref(true);
const failed = ref(false);
const feedback = ref('');

async function loadReleases() {
  loading.value = true;
  failed.value = false;

  try {
    const data = await listAdminReleases({ status: status.value });
    releases.value = data.results;
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

async function handleToggle(release: Release) {
  const nextStatus = release.status === 'hidden' ? 'published' : 'hidden';
  await toggleReleaseStatus(release.id, nextStatus);
  feedback.value = nextStatus === 'hidden' ? `已隐藏资源：${release.title}` : `已恢复资源：${release.title}`;
  await loadReleases();
}

onMounted(loadReleases);
</script>

<template>
  <AppPageHeader title="资源管理" description="后台可查看全部资源，并执行隐藏或恢复操作。" />
  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppCard title="资源列表" description="支持状态筛选和运维动作。">
    <div class="mb-4 flex flex-wrap gap-3">
      <UiSelect
        v-model="status"
        :options="[
          { label: '全部状态', value: 'all' },
          { label: '已发布', value: 'published' },
          { label: '草稿', value: 'draft' },
          { label: '已隐藏', value: 'hidden' },
        ]"
      />
      <UiButton variant="primary" @click="loadReleases">筛选</UiButton>
    </div>
    <AppLoading v-if="loading" />
    <AppError v-else-if="failed" title="资源管理加载失败" description="请稍后重试，或检查资源管理接口。" />
    <AppEmpty v-else-if="!releases.length" title="没有匹配的资源" description="当前筛选条件下没有可管理资源。" />
    <ReleaseListTable v-else :releases="releases" show-status>
      <template #actions="{ release }">
        <UiButton :to="`/releases/${release.id}`" size="sm">查看</UiButton>
        <UiButton variant="ghost" size="sm" @click="handleToggle(release)">
          {{ release.status === 'hidden' ? '恢复' : '隐藏' }}
        </UiButton>
      </template>
    </ReleaseListTable>
  </AppCard>
</template>
