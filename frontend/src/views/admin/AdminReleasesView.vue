<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import { listAdminReleases, toggleReleaseStatus } from '@/services/releases';
import type { Release } from '@/types/release';

const releases = ref<Release[]>([]);
const status = ref<'all' | 'published' | 'draft' | 'hidden'>('all');

async function loadReleases() {
  const data = await listAdminReleases({ status: status.value });
  releases.value = data.results;
}

async function handleToggle(release: Release) {
  const nextStatus = release.status === 'hidden' ? 'published' : 'hidden';
  await toggleReleaseStatus(release.id, nextStatus);
  await loadReleases();
}

onMounted(loadReleases);
</script>

<template>
  <AppPageHeader title="资源管理" description="后台可查看全部资源，并执行隐藏或恢复操作。" />
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
    <ReleaseListTable :releases="releases" show-status>
      <template #actions="{ release }">
        <UiButton :to="`/releases/${release.id}`" size="sm">查看</UiButton>
        <UiButton variant="ghost" size="sm" @click="handleToggle(release)">
          {{ release.status === 'hidden' ? '恢复' : '隐藏' }}
        </UiButton>
      </template>
    </ReleaseListTable>
  </AppCard>
</template>
