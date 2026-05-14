<script setup lang="ts">
import { computed, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import { lookupUserStats } from '@/services/users';
import type { UserStatsRecord } from '@/types/user-stats';
import { formatBytes, formatDateTime } from '@/utils/format';

const username = ref('');
const loading = ref(false);
const lookupCompleted = ref(false);
const errorMessage = ref('');
const stats = ref<UserStatsRecord | null>(null);

const shareRatioText = computed(() => {
  if (!stats.value) return '--';
  if (stats.value.downloadedBytes <= 0) {
    return stats.value.uploadedBytes > 0 ? '∞' : '0.00';
  }
  if (stats.value.shareRatio !== null) {
    return stats.value.shareRatio.toFixed(2);
  }
  return (stats.value.uploadedBytes / stats.value.downloadedBytes).toFixed(2);
});

const metricCards = computed(() => {
  if (!stats.value) return [];

  return [
    {
      label: '上传量',
      value: formatBytes(stats.value.uploadedBytes),
      hint: '用户资料里记录的累计上传数据',
    },
    {
      label: '下载量',
      value: formatBytes(stats.value.downloadedBytes),
      hint: '用户资料里记录的累计下载数据',
    },
    {
      label: '分享率',
      value: shareRatioText.value,
      hint: '按上传量 ÷ 下载量计算',
    },
    {
      label: '做种量',
      value: formatBytes(stats.value.seedingSizeBytes),
      hint: `当前做种 ${stats.value.seedingCount} 个任务`,
    },
  ];
});

async function handleLookup() {
  const normalizedUsername = username.value.trim();
  if (!normalizedUsername) {
    errorMessage.value = '请输入要查询的用户名。';
    stats.value = null;
    lookupCompleted.value = false;
    return;
  }

  loading.value = true;
  errorMessage.value = '';
  stats.value = null;

  try {
    stats.value = await lookupUserStats(normalizedUsername);
    lookupCompleted.value = true;
  } catch (error) {
    lookupCompleted.value = false;
    errorMessage.value = error instanceof Error ? error.message : '查询用户数据失败，请稍后重试。';
  } finally {
    loading.value = false;
  }
}

function resetLookup() {
  username.value = '';
  stats.value = null;
  errorMessage.value = '';
  lookupCompleted.value = false;
}
</script>

<template>
  <AppPageHeader
    title="用户数据查询"
    description="输入用户名后，可快速查询注册用户的做种、上传、下载和基础账户信息。该页面仅对 uploader 和 admin 开放。"
  />

  <AppAlert
    v-if="errorMessage"
    variant="error"
    title="查询失败"
    :description="errorMessage"
  />

  <AppCard
    title="按用户名查询"
    description="按用户名精确查询，自动忽略大小写。"
  >
    <form class="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto_auto]" @submit.prevent="handleLookup">
      <UiInput v-model="username" placeholder="请输入用户名，例如：uploader" />
      <UiButton type="submit" variant="primary" :disabled="loading">查询</UiButton>
      <UiButton type="button" variant="ghost" :disabled="loading" @click="resetLookup">清空</UiButton>
    </form>
  </AppCard>

  <AppLoading v-if="loading" />

  <AppEmpty
    v-else-if="lookupCompleted && !stats"
    title="未找到对应用户"
    description="请确认输入的是注册用户名，而不是显示名称。"
  />

  <template v-else-if="stats">
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div v-for="item in metricCards" :key="item.label" class="app-surface p-4">
        <p class="text-sm text-slate-500">{{ item.label }}</p>
        <p class="mt-3 text-2xl font-semibold text-slate-900">{{ item.value }}</p>
        <p class="mt-2 text-xs leading-6 text-slate-500">{{ item.hint }}</p>
      </div>
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
      <AppCard title="基础资料" description="账户身份、状态和登录时间等基础信息。">
        <dl class="grid gap-4 sm:grid-cols-2">
          <div>
            <dt class="text-sm text-slate-500">用户名</dt>
            <dd class="mt-1 font-medium text-slate-900">{{ stats.username }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">显示名</dt>
            <dd class="mt-1 font-medium text-slate-900">{{ stats.displayName }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">角色</dt>
            <dd class="mt-1"><AppStatusBadge type="role" :value="stats.role" /></dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">状态</dt>
            <dd class="mt-1"><AppStatusBadge type="user-status" :value="stats.status" /></dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">邮箱</dt>
            <dd class="mt-1 break-all font-medium text-slate-900">{{ stats.email }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">最近登录</dt>
            <dd class="mt-1 font-medium text-slate-900">{{ formatDateTime(stats.lastLoginAt) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">注册时间</dt>
            <dd class="mt-1 font-medium text-slate-900">{{ formatDateTime(stats.joinedAt) }}</dd>
          </div>
        </dl>
      </AppCard>

      <AppCard title="常用统计" description="适合快速核对用户当前常见数据。">
        <dl class="grid gap-4 sm:grid-cols-2">
          <div>
            <dt class="text-sm text-slate-500">做种任务数</dt>
            <dd class="mt-1 font-medium text-slate-900">{{ stats.seedingCount }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">做种体积</dt>
            <dd class="mt-1 font-medium text-slate-900">{{ formatBytes(stats.seedingSizeBytes) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">下载次数</dt>
            <dd class="mt-1 font-medium text-slate-900">{{ stats.downloadCount }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">发布数</dt>
            <dd class="mt-1 font-medium text-slate-900">{{ stats.createdReleaseCount }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">发布体积</dt>
            <dd class="mt-1 font-medium text-slate-900">{{ formatBytes(stats.createdReleaseSizeBytes) }}</dd>
          </div>
        </dl>
      </AppCard>
    </div>
  </template>
</template>
