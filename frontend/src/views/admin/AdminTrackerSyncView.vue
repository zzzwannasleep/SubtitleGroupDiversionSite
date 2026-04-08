<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
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

async function handleRunFullSync() {
  await runFullTrackerSync();
  feedback.value = '已触发一次全量同步，请关注后续日志状态。';
  await loadData();
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="XBT 同步" description="提供最近同步记录、失败记录与手动全量补偿入口。" />
  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppCard title="同步状态" description="MVP 阶段优先保证用户状态和资源白名单可重试。">
    <template #header>
      <UiButton variant="primary" @click="handleRunFullSync">手动全量同步</UiButton>
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
</template>
