<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppConfirmDialog from '@/components/app/AppConfirmDialog.vue';
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
const errorMessage = ref('');
const pendingAction = ref(false);
const targetRelease = ref<Release | null>(null);

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

function openToggleDialog(release: Release) {
  targetRelease.value = release;
}

async function handleToggle() {
  if (!targetRelease.value) return;

  const release = targetRelease.value;
  const nextStatus = release.status === 'hidden' ? 'published' : 'hidden';

  feedback.value = '';
  errorMessage.value = '';
  pendingAction.value = true;

  try {
    await toggleReleaseStatus(release.id, nextStatus);
    feedback.value = nextStatus === 'hidden' ? `已隐藏资源：${release.title}` : `已恢复资源：${release.title}`;
    targetRelease.value = null;
    await loadReleases();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新资源状态失败';
  } finally {
    pendingAction.value = false;
  }
}

onMounted(loadReleases);
</script>

<template>
  <AppPageHeader title="资源管理" description="后台可查看全部资源，并执行隐藏或恢复操作。" />
  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />
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
        <UiButton variant="ghost" size="sm" :disabled="pendingAction" @click="openToggleDialog(release)">
          {{ release.status === 'hidden' ? '恢复' : '隐藏' }}
        </UiButton>
      </template>
    </ReleaseListTable>
  </AppCard>

  <AppConfirmDialog
    :open="targetRelease !== null"
    :title="targetRelease?.status === 'hidden' ? '确认恢复该资源' : '确认隐藏该资源'"
    :description="
      targetRelease?.status === 'hidden'
        ? `恢复后，资源《${targetRelease?.title ?? ''}》会重新出现在前台列表和详情页中。`
        : `隐藏后，资源《${targetRelease?.title ?? ''}》将从前台浏览入口移除，仅管理员仍可查看。`
    "
    :confirm-label="targetRelease?.status === 'hidden' ? '确认恢复' : '确认隐藏'"
    :tone="targetRelease?.status === 'hidden' ? 'primary' : 'warning'"
    :pending="pendingAction"
    @close="targetRelease = null"
    @confirm="handleToggle"
  >
    <p>这个动作只改变前台可见性，不会删除资源记录和已有的下载审计信息。</p>
  </AppConfirmDialog>
</template>
