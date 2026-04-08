<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { listMyDownloads } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { DownloadRecord } from '@/types/release';
import { formatDateTime } from '@/utils/format';

const authStore = useAuthStore();
const loading = ref(true);
const downloads = ref<DownloadRecord[]>([]);

onMounted(async () => {
  if (!authStore.currentUser) return;
  downloads.value = await listMyDownloads(authStore.currentUser.id);
  loading.value = false;
});
</script>

<template>
  <AppPageHeader title="我的下载" description="记录个性化 torrent 下载，便于问题排查与简单审计。" />
  <AppLoading v-if="loading" />
  <AppCard v-else title="下载记录" :description="`共 ${downloads.length} 条。`">
    <AppEmpty v-if="!downloads.length" title="还没有下载记录" description="下载任意资源后会显示在这里。" />
    <UiTable v-else>
      <thead>
        <tr>
          <th>下载时间</th>
          <th>资源名</th>
          <th>重新下载</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in downloads" :key="item.id">
          <td>{{ formatDateTime(item.downloadedAt) }}</td>
          <td>{{ item.releaseTitle }}</td>
          <td>
            <UiButton :to="`/releases/${item.releaseId}`" size="sm">前往资源</UiButton>
          </td>
        </tr>
      </tbody>
    </UiTable>
  </AppCard>
</template>

