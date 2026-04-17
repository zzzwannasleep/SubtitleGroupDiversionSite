<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AppCard from '@/components/app/AppCard.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { getAdminDashboard } from '@/services/admin';
import type { AdminDashboardStats, AdminUser } from '@/types/admin';
import type { Release } from '@/types/release';
import { formatDateTime } from '@/utils/format';

const loading = ref(true);
const failed = ref(false);
const stats = ref<AdminDashboardStats | null>(null);
const latestUsers = ref<AdminUser[]>([]);
const latestReleases = ref<Release[]>([]);

const metricCards = computed(() => {
  if (!stats.value) return [];

  return [
    {
      label: '用户总数',
      value: stats.value.userCount,
      hint: '包含已禁用用户',
    },
    {
      label: '资源总数',
      value: stats.value.releaseCount,
      hint: '包含草稿与隐藏资源',
    },
    {
      label: '前台可见',
      value: stats.value.activeReleaseCount,
      hint: 'Published 状态资源',
    },
    {
      label: '待完善草稿',
      value: stats.value.draftReleaseCount,
      hint: '仍未发布的资源数量',
    },
    {
      label: '在线公告',
      value: stats.value.activeAnnouncementCount,
      hint: '会影响前台顶部公告条',
    },
  ];
});

const systemWatchItems = computed(() => {
  if (!stats.value) return [];

  return [
    {
      label: '草稿状态',
      status: stats.value.draftReleaseCount ? 'warning' : 'success',
      description: stats.value.draftReleaseCount
        ? `当前有 ${stats.value.draftReleaseCount} 条草稿资源还未发布。`
        : '当前没有堆积中的草稿资源。',
    },
    {
      label: '公告状态',
      status: stats.value.activeAnnouncementCount ? 'success' : 'warning',
      description: stats.value.activeAnnouncementCount
        ? '前台公告条正在展示线上公告。'
        : '当前没有线上公告，适合保持安静展示。',
    },
  ] as const;
});

async function loadData() {
  loading.value = true;
  failed.value = false;

  try {
    const data = await getAdminDashboard();
    stats.value = data.stats;
    latestUsers.value = data.latestUsers;
    latestReleases.value = data.latestReleases;
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="后台首页" description="后台首页更聚焦用户、资源和公告等日常管理动作。">
    <template #actions>
      <UiButton to="/admin/users" variant="primary">用户管理</UiButton>
      <UiButton to="/admin/releases" variant="secondary">资源管理</UiButton>
    </template>
  </AppPageHeader>

  <AppLoading v-if="loading" />
  <AppError
    v-else-if="failed"
    title="后台首页加载失败"
    description="请稍后重试，或检查管理端统计接口。"
  />
  <template v-else-if="stats">
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      <div
        v-for="item in metricCards"
        :key="item.label"
        class="app-surface overflow-hidden p-5"
      >
        <div class="h-1 rounded-full bg-blue-600" />
        <p class="mt-4 text-sm text-slate-500">{{ item.label }}</p>
        <p class="mt-3 text-3xl font-semibold text-slate-900">{{ item.value }}</p>
        <p class="mt-2 text-sm text-slate-500">{{ item.hint }}</p>
      </div>
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.1fr_1.1fr_0.8fr]">
      <AppCard title="最近用户" description="帮助管理员快速看见最近登录与维护对象。">
        <div class="space-y-3">
          <RouterLink
            v-for="user in latestUsers"
            :key="user.id"
            :to="`/admin/users/${user.id}`"
            class="block rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 transition hover:border-blue-200 hover:bg-white"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="space-y-2">
                <div>
                  <p class="font-medium text-slate-900">{{ user.displayName }}</p>
                  <p class="text-sm text-slate-500">{{ user.username }} / {{ user.email }}</p>
                </div>
                <div class="flex flex-wrap gap-2">
                  <AppStatusBadge type="role" :value="user.role" />
                  <AppStatusBadge type="user-status" :value="user.status" />
                </div>
              </div>
              <p class="text-xs text-slate-500">{{ formatDateTime(user.lastLoginAt) }}</p>
            </div>
          </RouterLink>
        </div>
      </AppCard>

      <AppCard title="最近资源" description="快速确认新发布条目、状态与前台可见性。">
        <div class="space-y-3">
          <RouterLink
            v-for="release in latestReleases"
            :key="release.id"
            :to="`/releases/${release.id}`"
            class="block rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 transition hover:border-blue-200 hover:bg-white"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="space-y-2">
                <div>
                  <p class="font-medium text-slate-900">{{ release.title }}</p>
                  <p class="mt-1 text-sm text-slate-500">{{ release.subtitle }}</p>
                </div>
                <div class="flex flex-wrap gap-2">
                  <AppStatusBadge type="release-status" :value="release.status" />
                  <span class="rounded-full bg-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700">
                    {{ release.category.name }}
                  </span>
                </div>
              </div>
              <p class="text-xs text-slate-500">{{ formatDateTime(release.publishedAt) }}</p>
            </div>
          </RouterLink>
        </div>
      </AppCard>

      <div class="space-y-6">
        <AppCard title="系统观察" description="用最少的信息判断后台当前是否有需要立刻处理的事情。">
          <div class="space-y-3">
            <div
              v-for="item in systemWatchItems"
              :key="item.label"
              class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
            >
              <div class="flex items-center justify-between gap-3">
                <p class="font-medium text-slate-900">{{ item.label }}</p>
                <AppStatusBadge type="sync-status" :value="item.status" />
              </div>
              <p class="mt-2 text-sm leading-6 text-slate-500">{{ item.description }}</p>
            </div>
          </div>
        </AppCard>

        <AppCard title="快捷入口" description="管理端高频路径尽量保持平直，不把关键操作藏进多层菜单。">
          <div class="grid gap-2">
            <RouterLink
              to="/admin/users"
              class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-blue-200 hover:bg-white hover:text-slate-900"
            >
              用户管理
            </RouterLink>
            <RouterLink
              to="/admin/releases"
              class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-blue-200 hover:bg-white hover:text-slate-900"
            >
              资源管理
            </RouterLink>
            <RouterLink
              to="/admin/announcements"
              class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-blue-200 hover:bg-white hover:text-slate-900"
            >
              公告管理
            </RouterLink>
            <RouterLink
              to="/admin/settings"
              class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-blue-200 hover:bg-white hover:text-slate-900"
            >
              系统设置
            </RouterLink>
          </div>
        </AppCard>
      </div>
    </div>
  </template>
</template>
