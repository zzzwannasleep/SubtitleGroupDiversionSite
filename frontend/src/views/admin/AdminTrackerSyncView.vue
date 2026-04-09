<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppConfirmDialog from '@/components/app/AppConfirmDialog.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { getTrackerSyncOverview, listTrackerSyncLogs, retryTrackerSyncLog, runFullTrackerSync } from '@/services/trackerSync';
import type { TrackerSyncLog, TrackerSyncOverview } from '@/types/admin';
import { formatDateTime } from '@/utils/format';
import { trackerScopeLabels } from '@/utils/labels';

const overview = ref<TrackerSyncOverview | null>(null);
const logs = ref<TrackerSyncLog[]>([]);
const loading = ref(true);
const failed = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const pendingFullSync = ref(false);
const confirmOpen = ref(false);
const pendingRetryLogId = ref<number | null>(null);
const retryDialogTarget = ref<TrackerSyncLog | null>(null);
const filters = reactive({
  scope: '',
  status: '',
  keyword: '',
});

const summaryCards = computed(() => {
  if (!overview.value) return [];

  return [
    {
      label: '同步开关',
      value: overview.value.summary.xbtSyncEnabled ? '已启用' : '已关闭',
      hint: `数据库别名：${overview.value.summary.xbtDatabaseAlias}`,
    },
    {
      label: '日志总数',
      value: overview.value.summary.totalLogs,
      hint: `成功 ${overview.value.summary.successCount} / 警告 ${overview.value.summary.warningCount}`,
    },
    {
      label: '待处理',
      value: overview.value.summary.pendingCount,
      hint: `失败 ${overview.value.summary.failedCount} 条，建议优先处理`,
    },
    {
      label: '最近成功',
      value: overview.value.summary.lastSuccessAt ? formatDateTime(overview.value.summary.lastSuccessAt) : '-',
      hint: '最近一次成功同步时间',
    },
    {
      label: '最近失败',
      value: overview.value.summary.lastFailureAt ? formatDateTime(overview.value.summary.lastFailureAt) : '-',
      hint: '最近一次失败同步时间',
    },
    {
      label: '最近全量',
      value: overview.value.summary.lastFullSyncAt ? formatDateTime(overview.value.summary.lastFullSyncAt) : '-',
      hint: '全量补偿同步最近执行时间',
    },
  ];
});

const failedLogs = computed(() => overview.value?.failedLogs ?? []);

async function loadData() {
  loading.value = true;
  failed.value = false;
  errorMessage.value = '';

  try {
    const [nextOverview, nextLogs] = await Promise.all([
      getTrackerSyncOverview(),
      listTrackerSyncLogs({
        scope: filters.scope ? (filters.scope as TrackerSyncLog['scope']) : undefined,
        status: filters.status ? (filters.status as TrackerSyncLog['status']) : undefined,
        q: filters.keyword.trim() || undefined,
        limit: 100,
      }),
    ]);

    overview.value = nextOverview;
    logs.value = nextLogs;
  } catch (error) {
    failed.value = true;
    errorMessage.value = error instanceof Error ? error.message : '加载 XBT 同步数据失败';
  } finally {
    loading.value = false;
  }
}

function openFullSyncDialog() {
  confirmOpen.value = true;
}

async function handleRunFullSync() {
  feedback.value = '';
  errorMessage.value = '';
  pendingFullSync.value = true;

  try {
    await runFullTrackerSync();
    feedback.value = '已触发一次全量同步，请关注失败日志是否继续增长。';
    confirmOpen.value = false;
    await loadData();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '触发全量同步失败';
  } finally {
    pendingFullSync.value = false;
  }
}

function resetFilters() {
  filters.scope = '';
  filters.status = '';
  filters.keyword = '';
  loadData();
}

async function handleRetryLog() {
  if (!retryDialogTarget.value) return;

  feedback.value = '';
  errorMessage.value = '';
  pendingRetryLogId.value = retryDialogTarget.value.id;

  try {
    await retryTrackerSyncLog(retryDialogTarget.value.id);
    feedback.value = `已触发日志 #${retryDialogTarget.value.id} 的同步重试。`;
    retryDialogTarget.value = null;
    await loadData();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '触发同步重试失败';
  } finally {
    pendingRetryLogId.value = null;
  }
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="XBT 同步" description="这里已接入总览、失败日志、按日志重试和目标跳转，便于后台联动排障。">
    <template #actions>
      <UiButton variant="secondary" @click="loadData">刷新数据</UiButton>
      <UiButton variant="primary" :disabled="pendingFullSync" @click="openFullSyncDialog">手动全量同步</UiButton>
    </template>
  </AppPageHeader>

  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
    <div
      v-for="item in summaryCards"
      :key="item.label"
      class="app-surface p-4"
    >
      <p class="text-sm text-slate-500">{{ item.label }}</p>
      <p class="mt-3 text-2xl font-semibold text-slate-900">{{ item.value }}</p>
      <p class="mt-2 text-xs leading-6 text-slate-500">{{ item.hint }}</p>
    </div>
  </div>

  <AppCard title="失败日志" description="优先处理失败同步，并直接跳到对应用户或资源。">
    <AppLoading v-if="loading && !overview" />
    <AppError
      v-else-if="failed && !overview"
      title="同步总览加载失败"
      description="请稍后重试，或检查后台同步接口与数据库连接。"
    />
    <AppEmpty
      v-else-if="!failedLogs.length"
      title="没有失败日志"
      description="当前失败列表为空，最近同步状态看起来是健康的。"
    />
    <UiTable v-else>
      <thead>
        <tr>
          <th>范围</th>
          <th>目标</th>
          <th>状态</th>
          <th>说明</th>
          <th>时间</th>
          <th>动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in failedLogs" :key="item.id">
          <td>{{ trackerScopeLabels[item.scope] }}</td>
          <td>{{ item.targetName }}</td>
          <td><AppStatusBadge type="sync-status" :value="item.status" /></td>
          <td>{{ item.message }}</td>
          <td class="whitespace-nowrap text-slate-500">{{ formatDateTime(item.updatedAt) }}</td>
          <td>
            <div class="flex flex-wrap items-center gap-2">
              <UiButton
                v-if="item.userId !== null"
                :to="`/admin/users/${item.userId}`"
                variant="ghost"
                size="sm"
              >
                用户详情
              </UiButton>
              <UiButton
                v-if="item.releaseId !== null"
                :to="`/releases/${item.releaseId}`"
                variant="ghost"
                size="sm"
              >
                资源页
              </UiButton>
              <UiButton
                v-if="item.retryable"
                variant="secondary"
                size="sm"
                :disabled="pendingRetryLogId === item.id"
                @click="retryDialogTarget = item"
              >
                {{ pendingRetryLogId === item.id ? '重试中...' : '重试' }}
              </UiButton>
            </div>
          </td>
        </tr>
      </tbody>
    </UiTable>
  </AppCard>

  <AppCard title="同步日志" description="支持范围、状态和关键字筛选，并消费日志里的目标关联信息。">
    <div class="mb-4 grid gap-3 md:grid-cols-2 xl:grid-cols-[180px_180px_minmax(0,1fr)_auto_auto]">
      <UiSelect
        v-model="filters.scope"
        :options="[
          { label: '用户', value: 'user' },
          { label: '资源', value: 'release' },
          { label: '全量', value: 'full' },
        ]"
        placeholder="全部范围"
      />
      <UiSelect
        v-model="filters.status"
        :options="[
          { label: '成功', value: 'success' },
          { label: '警告', value: 'warning' },
          { label: '失败', value: 'failed' },
        ]"
        placeholder="全部状态"
      />
      <UiInput v-model="filters.keyword" placeholder="搜索目标名称或日志说明" />
      <UiButton variant="primary" :disabled="loading" @click="loadData">筛选</UiButton>
      <UiButton variant="ghost" :disabled="loading" @click="resetFilters">清空</UiButton>
    </div>

    <AppLoading v-if="loading && !logs.length" />
    <AppError
      v-else-if="failed && !logs.length"
      title="同步日志加载失败"
      description="请稍后重试，或检查 XBT 同步日志接口。"
    />
    <AppEmpty
      v-else-if="!logs.length"
      title="暂无匹配日志"
      description="当前筛选条件下没有返回任何同步日志。"
    />
    <UiTable v-else>
      <thead>
        <tr>
          <th>范围</th>
          <th>目标</th>
          <th>状态</th>
          <th>说明</th>
          <th>时间</th>
          <th>动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in logs" :key="item.id">
          <td>{{ trackerScopeLabels[item.scope] }}</td>
          <td>{{ item.targetName }}</td>
          <td><AppStatusBadge type="sync-status" :value="item.status" /></td>
          <td>{{ item.message }}</td>
          <td class="whitespace-nowrap text-slate-500">{{ formatDateTime(item.updatedAt) }}</td>
          <td>
            <div class="flex flex-wrap items-center gap-2">
              <UiButton
                v-if="item.userId !== null"
                :to="`/admin/users/${item.userId}`"
                variant="ghost"
                size="sm"
              >
                用户详情
              </UiButton>
              <UiButton
                v-if="item.releaseId !== null"
                :to="`/releases/${item.releaseId}`"
                variant="ghost"
                size="sm"
              >
                资源页
              </UiButton>
              <UiButton
                v-if="item.retryable"
                variant="secondary"
                size="sm"
                :disabled="pendingRetryLogId === item.id"
                @click="retryDialogTarget = item"
              >
                {{ pendingRetryLogId === item.id ? '重试中...' : '重试' }}
              </UiButton>
            </div>
          </td>
        </tr>
      </tbody>
    </UiTable>
  </AppCard>

  <AppConfirmDialog
    :open="confirmOpen"
    title="确认执行全量同步"
    description="全量同步会重新比对用户、资源与白名单映射，适合大范围配置变更后的补偿处理。"
    confirm-label="立即同步"
    tone="warning"
    :pending="pendingFullSync"
    @close="confirmOpen = false"
    @confirm="handleRunFullSync"
  >
    <p>建议先确认当前没有正在进行的重要维护，再执行这次补偿同步。</p>
  </AppConfirmDialog>

  <AppConfirmDialog
    :open="retryDialogTarget !== null"
    title="确认重试这条同步日志"
    :description="retryDialogTarget ? `将根据日志 #${retryDialogTarget.id} 的目标重新触发一次同步。` : ''"
    confirm-label="立即重试"
    tone="primary"
    :pending="pendingRetryLogId !== null"
    @close="retryDialogTarget = null"
    @confirm="handleRetryLog"
  >
    <p>如果是同一类配置问题，请优先确认根因已经处理，再执行重试。</p>
  </AppConfirmDialog>
</template>
