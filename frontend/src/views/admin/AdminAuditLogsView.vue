<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { listAuditLogs } from '@/services/admin';
import type { AuditLog } from '@/types/admin';
import { formatDateTime } from '@/utils/format';

const logs = ref<AuditLog[]>([]);
const loading = ref(true);
const failed = ref(false);

async function loadData() {
  loading.value = true;
  failed.value = false;

  try {
    logs.value = await listAuditLogs();
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="审计日志" description="关键操作必须可追溯，便于排障和权限回溯。" />
  <AppCard title="操作记录" description="记录管理员和上传者的关键动作。">
    <AppLoading v-if="loading" />
    <AppError v-else-if="failed" title="审计日志加载失败" description="请稍后重试，或检查审计日志接口。" />
    <AppEmpty v-else-if="!logs.length" title="暂无审计记录" description="执行关键动作后会在这里保留追踪记录。" />
    <UiTable v-else>
      <thead>
        <tr>
          <th>操作人</th>
          <th>动作</th>
          <th>对象</th>
          <th>详情</th>
          <th>时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in logs" :key="item.id">
          <td>{{ item.actorName }}</td>
          <td>{{ item.action }}</td>
          <td>{{ item.targetType }} / {{ item.targetName }}</td>
          <td>{{ item.detail }}</td>
          <td>{{ formatDateTime(item.createdAt) }}</td>
        </tr>
      </tbody>
    </UiTable>
  </AppCard>
</template>
