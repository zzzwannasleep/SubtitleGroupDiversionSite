<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AdminMetricCard from '@/components/admin/AdminMetricCard.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import { getAdminDashboard } from '@/services/admin';
import type { AdminDashboardStats, AdminUser } from '@/types/admin';
import type { Release } from '@/types/release';
import { formatDateTime } from '@/utils/format';

const loading = ref(true);
const stats = ref<AdminDashboardStats | null>(null);
const latestUsers = ref<AdminUser[]>([]);
const latestReleases = ref<Release[]>([]);

onMounted(async () => {
  const data = await getAdminDashboard();
  stats.value = data.stats;
  latestUsers.value = data.latestUsers;
  latestReleases.value = data.latestReleases;
  loading.value = false;
});
</script>

<template>
  <AppPageHeader title="后台首页" description="与前台同属一套设计系统，但通过深色侧边栏强化管理层级。" />
  <AppLoading v-if="loading" />
  <template v-else-if="stats">
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      <AdminMetricCard label="用户数" :value="stats.userCount" hint="包含已禁用用户" />
      <AdminMetricCard label="资源总数" :value="stats.releaseCount" hint="包含草稿与隐藏资源" />
      <AdminMetricCard label="前台可见" :value="stats.activeReleaseCount" hint="Published 状态资源" />
      <AdminMetricCard label="待处理同步" :value="stats.pendingSyncCount" hint="失败或警告记录需要关注" />
      <AdminMetricCard label="在线公告" :value="stats.activeAnnouncementCount" hint="影响前台顶部公告条" />
    </div>

    <div class="grid gap-6 xl:grid-cols-2">
      <AppCard title="最近用户" description="帮助管理员快速看到最近维护对象。">
        <div class="space-y-3">
          <div v-for="user in latestUsers" :key="user.id" class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="font-medium text-slate-900">{{ user.displayName }}</p>
                <p class="text-sm text-slate-500">{{ user.username }} / {{ user.role }}</p>
              </div>
              <p class="text-xs text-slate-500">{{ formatDateTime(user.lastLoginAt) }}</p>
            </div>
          </div>
        </div>
      </AppCard>

      <AppCard title="最近资源" description="后台首页重点展示最近资源和异常同步线索。">
        <div class="space-y-3">
          <div
            v-for="release in latestReleases"
            :key="release.id"
            class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
          >
            <p class="font-medium text-slate-900">{{ release.title }}</p>
            <p class="mt-1 text-sm text-slate-500">{{ release.subtitle }}</p>
          </div>
        </div>
      </AppCard>
    </div>
  </template>
</template>

