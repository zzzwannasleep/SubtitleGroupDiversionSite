<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import { listMyReleases } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { Release } from '@/types/release';

const authStore = useAuthStore();
const loading = ref(true);
const failed = ref(false);
const releases = ref<Release[]>([]);

async function loadReleases() {
  if (!authStore.currentUser) return;
  loading.value = true;
  failed.value = false;

  try {
    releases.value = await listMyReleases(authStore.currentUser.id);
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(loadReleases);
</script>

<template>
  <AppPageHeader title="我的发布" description="上传者和管理员都在前台查看自己的资源，不误入后台。" />
  <AppLoading v-if="loading" />
  <AppError v-else-if="failed" title="我的发布加载失败" description="请稍后再试，或检查资源接口状态。" />
  <AppCard v-else title="我发布的资源" :description="`共 ${releases.length} 条。`">
    <AppEmpty v-if="!releases.length" title="暂时没有已发布资源" description="发布成功后会出现在这里。" />
    <ReleaseListTable v-else :releases="releases" show-status>
      <template #actions="{ release }">
        <UiButton :to="`/my/releases/${release.id}/edit`" size="sm">编辑</UiButton>
        <UiButton :to="`/releases/${release.id}`" size="sm" variant="ghost">查看</UiButton>
      </template>
    </ReleaseListTable>
  </AppCard>
</template>
