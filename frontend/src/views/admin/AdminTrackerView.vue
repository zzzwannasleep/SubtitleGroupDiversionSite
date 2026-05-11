<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { getAdminTrackerOverview, runAdminTrackerSync } from '@/services/tracker';
import type { AdminTrackerOverview, AdminTrackerSyncPayload } from '@/types/tracker';
import { formatDateTime } from '@/utils/format';

const loading = ref(true);
const failed = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const pendingAction = ref<'users' | 'releases' | 'scrape' | 'all' | null>(null);
const overview = ref<AdminTrackerOverview | null>(null);

const trackerStatus = computed(() => {
  if (!overview.value?.enabled) return 'warning';
  if (!overview.value.trackerReachable) return 'failed';
  if (overview.value.syncErrorCount > 0) return 'warning';
  return 'success';
});

const summaryCards = computed(() => {
  if (!overview.value) return [];

  return [
    {
      label: 'Key 已分配',
      value: `${overview.value.userKeysProvisioned} / ${overview.value.activeUserCount}`,
      hint: '按活跃用户统计。',
    },
    {
      label: 'Whitelist 覆盖',
      value: `${overview.value.whitelistedReleaseCount} / ${overview.value.publishedReleaseCount}`,
      hint: '按已发布资源统计。',
    },
    {
      label: '同步记录',
      value: overview.value.releaseSyncCount,
      hint: '已建立 tracker 同步快照的资源数。',
    },
    {
      label: '异常数',
      value: overview.value.syncErrorCount,
      hint: '包含 whitelist 与 scrape 的最近错误。',
    },
  ];
});

async function loadOverview() {
  loading.value = true;
  failed.value = false;
  errorMessage.value = '';

  try {
    overview.value = await getAdminTrackerOverview();
  } catch (error) {
    failed.value = true;
    errorMessage.value = error instanceof Error ? error.message : '加载 Tracker 概览失败。';
  } finally {
    loading.value = false;
  }
}

async function handleSync(action: 'users' | 'releases' | 'scrape' | 'all') {
  const payloadMap: Record<typeof action, AdminTrackerSyncPayload> = {
    users: { syncUsers: true },
    releases: { syncReleases: true },
    scrape: { syncScrape: true },
    all: {},
  };

  feedback.value = '';
  errorMessage.value = '';
  pendingAction.value = action;

  try {
    const result = await runAdminTrackerSync(payloadMap[action]);
    await loadOverview();
    feedback.value =
      result.errors.length > 0
        ? `同步已完成，但有 ${result.errors.length} 条错误，请检查下方错误明细。`
        : 'Tracker 同步已完成。';
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '执行 Tracker 同步失败。';
  } finally {
    pendingAction.value = null;
  }
}

onMounted(loadOverview);
</script>

<template>
  <AppPageHeader title="Private Tracker" description="查看当前 tracker 状态，并手动触发 key、whitelist 与 scrape 同步。">
    <template #actions>
      <UiButton variant="secondary" :disabled="loading || pendingAction !== null" @click="loadOverview">刷新概览</UiButton>
      <UiButton variant="primary" :disabled="loading || pendingAction !== null" @click="handleSync('all')">
        {{ pendingAction === 'all' ? '同步中...' : '全量同步' }}
      </UiButton>
    </template>
  </AppPageHeader>

  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage && !failed" variant="error" :title="errorMessage" />

  <AppLoading v-if="loading" />
  <AppError
    v-else-if="failed"
    title="Tracker 概览加载失败"
    :description="errorMessage || '请稍后重试。'"
  >
    <template #actions>
      <UiButton variant="primary" @click="loadOverview">重试</UiButton>
    </template>
  </AppError>
  <template v-else-if="overview">
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div v-for="item in summaryCards" :key="item.label" class="app-surface overflow-hidden p-5">
        <div class="h-1 rounded-full bg-blue-600" />
        <p class="mt-4 text-sm text-slate-500">{{ item.label }}</p>
        <p class="mt-3 text-3xl font-semibold text-slate-900">{{ item.value }}</p>
        <p class="mt-2 text-sm text-slate-500">{{ item.hint }}</p>
      </div>
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <AppCard title="运行状态" description="区分站点是否启用 tracker、tracker 服务是否可达，以及最近同步是否出现异常。">
        <div class="space-y-4">
          <div class="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <div>
              <p class="font-medium text-slate-900">总体状态</p>
              <p class="mt-1 text-sm text-slate-500">
                {{ overview.enabled ? 'Private Tracker 已启用。' : '当前站点尚未启用 Private Tracker。' }}
              </p>
            </div>
            <AppStatusBadge type="sync-status" :value="trackerStatus" />
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p class="text-sm text-slate-500">鉴权模式</p>
              <p class="mt-2 font-medium text-slate-900">{{ overview.authMode }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p class="text-sm text-slate-500">下载要求登录</p>
              <p class="mt-2 font-medium text-slate-900">{{ overview.requireAuthDownloads ? '是' : '否' }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p class="text-sm text-slate-500">最近 whitelist 同步</p>
              <p class="mt-2 font-medium text-slate-900">
                {{ overview.latestSyncAt ? formatDateTime(overview.latestSyncAt) : '暂无记录' }}
              </p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p class="text-sm text-slate-500">最近 scrape 同步</p>
              <p class="mt-2 font-medium text-slate-900">
                {{ overview.latestScrapeAt ? formatDateTime(overview.latestScrapeAt) : '暂无记录' }}
              </p>
            </div>
          </div>

          <div class="space-y-3">
            <div>
              <p class="mb-2 text-sm text-slate-500">Announce Base URL</p>
              <p class="break-all rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 font-mono text-xs text-slate-700">
                {{ overview.announceUrl || '未配置' }}
              </p>
            </div>
            <div>
              <p class="mb-2 text-sm text-slate-500">Scrape Base URL</p>
              <p class="break-all rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 font-mono text-xs text-slate-700">
                {{ overview.scrapeUrl || '未配置' }}
              </p>
            </div>
          </div>

          <div v-if="overview.trackerMessage" class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {{ overview.trackerMessage }}
          </div>
        </div>
      </AppCard>

      <div class="space-y-6">
        <AppCard title="手动同步" description="在部署后补历史数据，或在 tracker 服务恢复后重新推送状态。">
          <div class="grid gap-2">
            <UiButton variant="secondary" :disabled="pendingAction !== null" @click="handleSync('users')">
              {{ pendingAction === 'users' ? '处理中...' : '同步用户 Key' }}
            </UiButton>
            <UiButton variant="secondary" :disabled="pendingAction !== null" @click="handleSync('releases')">
              {{ pendingAction === 'releases' ? '处理中...' : '同步 Whitelist' }}
            </UiButton>
            <UiButton variant="secondary" :disabled="pendingAction !== null" @click="handleSync('scrape')">
              {{ pendingAction === 'scrape' ? '处理中...' : '刷新 Scrape 统计' }}
            </UiButton>
          </div>
        </AppCard>

        <AppCard title="Tracker 统计" description="来自 tracker 服务的聚合视图，用于快速判断站内活跃度。">
          <div v-if="overview.trackerStats" class="grid gap-4 sm:grid-cols-2">
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p class="text-sm text-slate-500">Torrents</p>
              <p class="mt-2 text-2xl font-semibold text-slate-900">{{ overview.trackerStats.torrents }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p class="text-sm text-slate-500">Seeders</p>
              <p class="mt-2 text-2xl font-semibold text-slate-900">{{ overview.trackerStats.seeders }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p class="text-sm text-slate-500">Leechers</p>
              <p class="mt-2 text-2xl font-semibold text-slate-900">{{ overview.trackerStats.leechers }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p class="text-sm text-slate-500">Completed</p>
              <p class="mt-2 text-2xl font-semibold text-slate-900">{{ overview.trackerStats.completed }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p class="text-sm text-slate-500">Announces Handled</p>
              <p class="mt-2 text-2xl font-semibold text-slate-900">{{ overview.trackerStats.announcesHandled }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p class="text-sm text-slate-500">Scrapes Handled</p>
              <p class="mt-2 text-2xl font-semibold text-slate-900">{{ overview.trackerStats.scrapesHandled }}</p>
            </div>
          </div>
          <div
            v-else
            class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm leading-6 text-slate-600"
          >
            暂时无法从 tracker 服务读取聚合统计。
          </div>
        </AppCard>
      </div>
    </div>
  </template>
</template>
