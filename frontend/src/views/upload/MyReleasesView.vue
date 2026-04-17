<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import { listMyReleases } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { Release } from '@/types/release';

const authStore = useAuthStore();
const loading = ref(true);
const failed = ref(false);
const releases = ref<Release[]>([]);
const statusFilter = ref<'all' | 'published' | 'draft' | 'hidden'>('all');

const filteredReleases = computed(() =>
  statusFilter.value === 'all'
    ? releases.value
    : releases.value.filter((item) => item.status === statusFilter.value),
);
const summary = computed(() => `共 ${filteredReleases.value.length} / ${releases.value.length} 条`);

async function loadReleases() {
  if (!authStore.currentUser) return;
  loading.value = true;
  failed.value = false;

  try {
    releases.value = await listMyReleases(authStore.currentUser.id);
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(loadReleases);
</script>

<template>
  <AppPageHeader title="我的发布">
    <template #actions>
      <UiButton to="/upload" variant="primary">上传种子</UiButton>
    </template>
  </AppPageHeader>
  <AppLoading v-if="loading" />
  <AppError v-else-if="failed" title="我的发布加载失败" description="请稍后重试。" />
  <AppCard v-else title="资源列表">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <UiSelect
        v-model="statusFilter"
        :options="[
          { label: '全部状态', value: 'all' },
          { label: '已发布', value: 'published' },
          { label: '草稿', value: 'draft' },
          { label: '已隐藏', value: 'hidden' },
        ]"
      />
      <div class="flex items-center gap-2">
        <p class="text-sm text-slate-500">{{ summary }}</p>
        <UiButton variant="ghost" @click="statusFilter = 'all'">重置</UiButton>
      </div>
    </div>
    <AppEmpty v-if="!filteredReleases.length" title="暂无资源" description="当前筛选下没有内容。" />
    <ReleaseListTable v-else :releases="filteredReleases" show-status>
      <template #actions="{ release }">
        <UiButton :to="`/my/releases/${release.id}/edit`" size="sm">编辑</UiButton>
        <UiButton :to="`/releases/${release.id}`" size="sm" variant="ghost">查看</UiButton>
      </template>
    </ReleaseListTable>
  </AppCard>
</template>
