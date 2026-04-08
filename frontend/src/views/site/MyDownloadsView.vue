<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { downloadRelease, listMyDownloads } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { DownloadRecord } from '@/types/release';
import { formatDateTime } from '@/utils/format';

const authStore = useAuthStore();
const loading = ref(true);
const failed = ref(false);
const downloads = ref<DownloadRecord[]>([]);

async function loadDownloads() {
  if (!authStore.currentUser) return;
  loading.value = true;
  failed.value = false;

  try {
    downloads.value = await listMyDownloads(authStore.currentUser.id);
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(loadDownloads);
</script>

<template>
  <AppPageHeader title="我的下载" description="记录个性化 torrent 下载，便于问题排查与简单审计。" />
  <AppLoading v-if="loading" />
  <AppError v-else-if="failed" title="下载记录加载失败" description="请稍后再试，或检查下载记录接口状态。" />
  <AppCard v-else title="下载记录" :description="`共 ${downloads.length} 条。`">
    <AppEmpty v-if="!downloads.length" title="还没有下载记录" description="下载任意资源后会显示在这里。" />
    <UiTable v-else>
      <thead>
        <tr>
          <th>下载时间</th>
          <th>资源</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in downloads" :key="item.id">
          <td>{{ formatDateTime(item.downloadedAt) }}</td>
          <td>
            <div class="space-y-1">
              <p class="font-medium text-slate-900">{{ item.releaseTitle }}</p>
              <UiButton :to="`/releases/${item.releaseId}`" variant="ghost" size="sm">查看资源页</UiButton>
            </div>
          </td>
          <td>
            <UiButton size="sm" @click="downloadRelease(item.releaseId)">重新下载</UiButton>
          </td>
        </tr>
      </tbody>
    </UiTable>
  </AppCard>
</template>
