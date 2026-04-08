<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppConfirmDialog from '@/components/app/AppConfirmDialog.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { listTrackerSyncLogs, runFullTrackerSync } from '@/services/trackerSync';
import type { TrackerSyncLog } from '@/types/admin';
import { formatDateTime } from '@/utils/format';
import { trackerScopeLabels } from '@/utils/labels';

const logs = ref<TrackerSyncLog[]>([]);
const loading = ref(true);
const failed = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const pendingFullSync = ref(false);
const confirmOpen = ref(false);

async function loadData() {
  loading.value = true;
  failed.value = false;

  try {
    logs.value = await listTrackerSyncLogs();
  } catch {
    failed.value = true;
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
    feedback.value = '已触发一次全量同步，请关注后续日志状态。';
    confirmOpen.value = false;
    await loadData();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '触发全量同步失败';
  } finally {
    pendingFullSync.value = false;
  }
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="XBT 同步" description="提供最近同步记录、失败记录与手动全量补偿入口。" />
  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />
  <AppCard title="同步状态" description="MVP 阶段优先保证用户状态和资源白名单可重试。">
    <template #header>
      <UiButton variant="primary" :disabled="pendingFullSync" @click="openFullSyncDialog">手动全量同步</UiButton>
    </template>
    <AppLoading v-if="loading" />
    <AppError v-else-if="failed" title="同步记录加载失败" description="请稍后重试，或检查同步日志接口。" />
    <AppEmpty v-else-if="!logs.length" title="暂无同步记录" description="触发同步后会在这里显示结果。" />
    <UiTable v-else>
      <thead>
        <tr>
          <th>范围</th>
          <th>目标</th>
          <th>状态</th>
          <th>说明</th>
          <th>时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in logs" :key="item.id">
          <td>{{ trackerScopeLabels[item.scope] }}</td>
          <td>{{ item.targetName }}</td>
          <td><AppStatusBadge type="sync-status" :value="item.status" /></td>
          <td>{{ item.message }}</td>
          <td>{{ formatDateTime(item.updatedAt) }}</td>
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
</template>
