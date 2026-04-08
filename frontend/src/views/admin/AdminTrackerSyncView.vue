<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { listTrackerSyncLogs, runFullTrackerSync } from '@/services/trackerSync';
import type { TrackerSyncLog } from '@/types/admin';
import { formatDateTime } from '@/utils/format';

const logs = ref<TrackerSyncLog[]>([]);

async function loadData() {
  logs.value = await listTrackerSyncLogs();
}

async function handleRunFullSync() {
  await runFullTrackerSync();
  await loadData();
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="XBT 同步" description="提供最近同步记录、失败记录与手动全量补偿入口。" />
  <AppCard title="同步状态" description="MVP 阶段优先保证用户状态和资源白名单可重试。">
    <template #header>
      <UiButton variant="primary" @click="handleRunFullSync">手动全量同步</UiButton>
    </template>
    <UiTable>
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
          <td>{{ item.scope }}</td>
          <td>{{ item.targetName }}</td>
          <td><AppStatusBadge type="sync-status" :value="item.status" /></td>
          <td>{{ item.message }}</td>
          <td>{{ formatDateTime(item.updatedAt) }}</td>
        </tr>
      </tbody>
    </UiTable>
  </AppCard>
</template>

