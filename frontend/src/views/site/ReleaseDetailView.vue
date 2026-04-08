<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppConfirmDialog from '@/components/app/AppConfirmDialog.vue';
import AppError from '@/components/app/AppError.vue';
import AppForbidden from '@/components/app/AppForbidden.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppNotFound from '@/components/app/AppNotFound.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { isApiError } from '@/services/api';
import { downloadRelease, getReleaseById, toggleReleaseStatus } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { Release } from '@/types/release';
import { formatBytes, formatDateTime } from '@/utils/format';
import { canEditRelease } from '@/utils/permissions';

const route = useRoute();
const authStore = useAuthStore();

const state = ref<'loading' | 'ready' | 'forbidden' | 'not-found' | 'error'>('loading');
const release = ref<Release | null>(null);
const feedback = ref('');
const errorMessage = ref('');
const pageErrorMessage = ref('');
const pendingVisibilityAction = ref(false);
const visibilityDialogOpen = ref(false);

const canEdit = computed(() => canEditRelease(authStore.currentUser, release.value));
const canHide = computed(() => authStore.currentUser?.role === 'admin');
const canViewTrackerPanel = computed(() => {
  if (!authStore.currentUser || !release.value) return false;
  return authStore.currentUser.role === 'admin' || authStore.currentUser.id === release.value.createdBy.id;
});
const hasTrackerPanel = computed(
  () => canViewTrackerPanel.value && Boolean(release.value?.trackerSync || release.value?.xbtFile),
);
const detailMetrics = computed(() => {
  if (!release.value) return [];

  return [
    { label: '文件数', value: `${release.value.files.length} 个`, hint: 'torrent 解析后的资源文件列表' },
    { label: '下载次数', value: release.value.downloadCount, hint: '个性化种子下载记录' },
    { label: '完成次数', value: release.value.completionCount, hint: '用于衡量分发完成情况' },
    { label: '活跃 peers', value: release.value.activePeers, hint: '便于快速判断资源健康度' },
  ];
});
const trackerFacts = computed(() => {
  if (!release.value?.xbtFile) return [];

  return [
    {
      label: 'Seeders',
      value: release.value.xbtFile.seeders === null ? '-' : `${release.value.xbtFile.seeders}`,
    },
    {
      label: 'Leechers',
      value: release.value.xbtFile.leechers === null ? '-' : `${release.value.xbtFile.leechers}`,
    },
    {
      label: '完成数',
      value: release.value.xbtFile.completed === null ? '-' : `${release.value.xbtFile.completed}`,
    },
    {
      label: '白名单写入',
      value: release.value.xbtFile.createdAt ? formatDateTime(release.value.xbtFile.createdAt) : '-',
    },
  ];
});
const hiddenNotice = computed(() => {
  if (release.value?.status !== 'hidden') return null;

  return {
    title: '当前资源处于隐藏状态',
    description: '它不会出现在前台列表、分类页和标签页中，当前页面仅管理员可见。',
  };
});
const isVisibleToCurrentUser = computed(() => {
  if (!release.value) return false;
  if (release.value.status !== 'hidden') return true;
  return authStore.currentUser?.role === 'admin';
});

async function loadRelease() {
  state.value = 'loading';
  release.value = null;
  feedback.value = '';
  errorMessage.value = '';
  pageErrorMessage.value = '';

  try {
    release.value = await getReleaseById(Number(route.params.id));
    state.value = release.value ? 'ready' : 'not-found';
  } catch (error) {
    if (isApiError(error) && error.status === 403) {
      state.value = 'forbidden';
      return;
    }

    if (isApiError(error) && error.status === 404) {
      state.value = 'not-found';
      return;
    }

    pageErrorMessage.value = error instanceof Error ? error.message : '资源详情加载失败';
    state.value = 'error';
  }
}

async function toggleVisibility() {
  if (!release.value) return;

  const releaseId = release.value.id;
  errorMessage.value = '';
  feedback.value = '';
  pendingVisibilityAction.value = true;

  try {
    const nextStatus = release.value.status === 'hidden' ? 'published' : 'hidden';
    await toggleReleaseStatus(releaseId, nextStatus);
    release.value = await getReleaseById(releaseId);
    feedback.value = nextStatus === 'hidden' ? '资源已隐藏，前台入口已移除。' : '资源已恢复为前台可见。';
    visibilityDialogOpen.value = false;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新资源状态失败';
  } finally {
    pendingVisibilityAction.value = false;
  }
}

function handleDownload() {
  if (!release.value) return;
  feedback.value = '正在生成带个人 passkey 的 torrent 下载文件。';
  errorMessage.value = '';
  downloadRelease(release.value.id);
}

watch(() => route.params.id, loadRelease, { immediate: true });
</script>

<template>
  <AppLoading v-if="state === 'loading'" />
  <AppForbidden v-else-if="state === 'forbidden'" />
  <AppError v-else-if="state === 'error'" title="资源详情加载失败" :description="pageErrorMessage">
    <template #actions>
      <UiButton variant="primary" @click="loadRelease">重试</UiButton>
    </template>
  </AppError>
  <AppNotFound v-else-if="state === 'not-found' || !release || !isVisibleToCurrentUser" />
  <template v-else>
    <AppPageHeader :title="release.title" :description="release.subtitle">
      <template #actions>
        <UiButton variant="primary" @click="handleDownload">下载种子</UiButton>
        <UiButton v-if="canEdit" :to="`/my/releases/${release.id}/edit`" variant="secondary">编辑资源</UiButton>
        <UiButton v-if="canHide" variant="ghost" :disabled="pendingVisibilityAction" @click="visibilityDialogOpen = true">
          {{ release.status === 'hidden' ? '恢复前台可见' : '隐藏资源' }}
        </UiButton>
      </template>
    </AppPageHeader>

    <AppAlert
      v-if="hiddenNotice"
      variant="warning"
      :title="hiddenNotice.title"
      :description="hiddenNotice.description"
    />
    <AppAlert v-if="feedback" variant="info" :title="feedback" />
    <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <div
        v-for="item in detailMetrics"
        :key="item.label"
        class="app-surface p-4"
      >
        <p class="text-sm text-slate-500">{{ item.label }}</p>
        <p class="mt-3 text-2xl font-semibold text-slate-900">{{ item.value }}</p>
        <p class="mt-2 text-xs leading-6 text-slate-500">{{ item.hint }}</p>
      </div>
    </div>

    <div class="grid gap-6 xl:grid-cols-[2fr_1fr]">
      <div class="space-y-6">
        <AppCard title="资源简介" description="详情页集中展示正文说明、分类标签和下载前需要确认的信息。">
          <div class="mb-4 flex flex-wrap items-center gap-2">
            <RouterLink
              :to="`/categories/${release.category.slug}`"
              class="rounded-full bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700"
            >
              {{ release.category.name }}
            </RouterLink>
            <AppStatusBadge type="release-status" :value="release.status" />
          </div>
          <p class="text-sm leading-7 text-slate-700">{{ release.description }}</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <RouterLink
              v-for="tag in release.tags"
              :key="tag.slug"
              :to="`/tags/${tag.slug}`"
              class="rounded-full bg-slate-100 px-3 py-1.5 text-sm text-slate-700 transition hover:bg-slate-200"
            >
              {{ tag.name }}
            </RouterLink>
          </div>
        </AppCard>

        <AppCard title="文件列表" description="由后端解析 torrent 后写入的文件清单，便于下载前快速核对。">
          <div class="space-y-3">
            <div
              v-for="(file, index) in release.files"
              :key="file.path"
              class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <div class="font-medium text-slate-900">{{ file.path }}</div>
                  <div class="mt-1 text-xs text-slate-500">文件 {{ index + 1 }}</div>
                </div>
                <div class="shrink-0 text-slate-500">{{ formatBytes(file.sizeBytes) }}</div>
              </div>
            </div>
          </div>
        </AppCard>
      </div>

      <div class="space-y-6">
        <AppCard title="资源信息">
          <dl class="space-y-4 text-sm">
            <div class="flex items-center justify-between gap-3">
              <dt class="text-slate-500">状态</dt>
              <dd><AppStatusBadge type="release-status" :value="release.status" /></dd>
            </div>
            <div class="flex items-center justify-between gap-3">
              <dt class="text-slate-500">分类</dt>
              <dd>
                <RouterLink :to="`/categories/${release.category.slug}`" class="text-blue-700 hover:text-blue-800">
                  {{ release.category.name }}
                </RouterLink>
              </dd>
            </div>
            <div class="flex items-center justify-between gap-3">
              <dt class="text-slate-500">大小</dt>
              <dd>{{ formatBytes(release.sizeBytes) }}</dd>
            </div>
            <div class="flex items-center justify-between gap-3">
              <dt class="text-slate-500">发布时间</dt>
              <dd>{{ formatDateTime(release.publishedAt) }}</dd>
            </div>
            <div class="flex items-center justify-between gap-3">
              <dt class="text-slate-500">最后更新</dt>
              <dd>{{ formatDateTime(release.updatedAt) }}</dd>
            </div>
            <div class="flex items-center justify-between gap-3">
              <dt class="text-slate-500">发布者</dt>
              <dd>{{ release.createdBy.displayName }}</dd>
            </div>
            <div class="flex items-center justify-between gap-3">
              <dt class="text-slate-500">下载次数</dt>
              <dd>{{ release.downloadCount }}</dd>
            </div>
            <div class="flex items-center justify-between gap-3">
              <dt class="text-slate-500">完成次数</dt>
              <dd>{{ release.completionCount }}</dd>
            </div>
            <div class="flex items-center justify-between gap-3">
              <dt class="text-slate-500">活跃 peers</dt>
              <dd>{{ release.activePeers }}</dd>
            </div>
          </dl>
        </AppCard>

        <AppCard title="下载说明" description="下载的 torrent 会携带个人 passkey，请勿外传。">
          <div class="space-y-4 text-sm text-slate-600">
            <div>
              <p class="mb-2 text-slate-500">Infohash</p>
              <p class="break-all rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700">
                {{ release.infohash }}
              </p>
            </div>
            <ul class="space-y-2 leading-7">
              <li>下载前可先核对文件列表、分类和标签，避免误下错包。</li>
              <li>若 RSS 地址或种子泄露，可在“我的账户”中重置 passkey。</li>
              <li>管理员隐藏资源时，不会删除文件和审计记录，只会收起前台入口。</li>
            </ul>
          </div>
        </AppCard>

        <AppCard
          v-if="hasTrackerPanel"
          title="Tracker 状态"
          description="发布者和管理员可直接看到白名单状态，便于判断同步是否完成。"
        >
          <div class="space-y-4">
            <div>
              <div class="mb-2 flex items-center justify-between gap-3">
                <p class="text-sm text-slate-500">最近同步</p>
                <AppStatusBadge
                  v-if="release.trackerSync"
                  type="sync-status"
                  :value="release.trackerSync.status"
                />
              </div>
              <div v-if="release.trackerSync" class="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p class="text-sm leading-6 text-slate-700">{{ release.trackerSync.message }}</p>
                <p class="mt-2 text-xs text-slate-500">{{ formatDateTime(release.trackerSync.updatedAt) }}</p>
              </div>
            </div>

            <div>
              <div class="mb-2 flex items-center justify-between gap-3">
                <p class="text-sm text-slate-500">XBT 白名单</p>
                <AppStatusBadge
                  v-if="release.xbtFile"
                  type="xbt-file-state"
                  :value="release.xbtFile.state"
                />
              </div>
              <div v-if="release.xbtFile" class="grid gap-3 sm:grid-cols-2">
                <div
                  v-for="item in trackerFacts"
                  :key="item.label"
                  class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                >
                  <p class="text-xs text-slate-500">{{ item.label }}</p>
                  <p class="mt-2 text-sm font-medium text-slate-900">{{ item.value }}</p>
                </div>
              </div>
              <p
                v-if="release.xbtFile?.updatedAt"
                class="text-xs text-slate-500"
              >
                最近白名单更新时间：{{ formatDateTime(release.xbtFile.updatedAt) }}
              </p>
            </div>
          </div>
        </AppCard>
      </div>
    </div>

    <AppConfirmDialog
      :open="visibilityDialogOpen"
      :title="release.status === 'hidden' ? '确认恢复该资源' : '确认隐藏该资源'"
      :description="
        release.status === 'hidden'
          ? '恢复后，资源会重新回到前台列表、分类页和标签页中。'
          : '隐藏后，资源会从前台浏览入口移除，仅管理员仍可查看和恢复。'
      "
      :confirm-label="release.status === 'hidden' ? '确认恢复' : '确认隐藏'"
      :tone="release.status === 'hidden' ? 'primary' : 'warning'"
      :pending="pendingVisibilityAction"
      @close="visibilityDialogOpen = false"
      @confirm="toggleVisibility"
    >
      <p>这个操作不会删除资源文件和审计记录，只会调整前台可见性。</p>
    </AppConfirmDialog>
  </template>
</template>
