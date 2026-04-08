<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
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
const isVisibleToCurrentUser = computed(() => {
  if (!release.value) return false;
  if (release.value.status !== 'hidden') return true;
  return authStore.currentUser?.role === 'admin';
});

async function loadRelease() {
  state.value = 'loading';
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
  } finally {
  }
}

async function toggleVisibility() {
  if (!release.value) return;

  errorMessage.value = '';
  feedback.value = '';
  pendingVisibilityAction.value = true;

  try {
    const nextStatus = release.value.status === 'hidden' ? 'published' : 'hidden';
    release.value = await toggleReleaseStatus(release.value.id, nextStatus);
    feedback.value = nextStatus === 'hidden' ? '资源已隐藏，仅管理员可见。' : '资源已恢复为前台可见。';
    visibilityDialogOpen.value = false;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新资源状态失败';
  } finally {
    pendingVisibilityAction.value = false;
  }
}

function handleDownload() {
  if (!release.value) return;
  feedback.value = '正在生成带个人 passkey 的 torrent 下载。';
  errorMessage.value = '';
  downloadRelease(release.value.id);
}

onMounted(loadRelease);
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
        <UiButton v-if="canEdit" :to="`/my/releases/${release.id}/edit`" variant="secondary">编辑</UiButton>
        <UiButton v-if="canHide" variant="ghost" :disabled="pendingVisibilityAction" @click="visibilityDialogOpen = true">
          {{ release.status === 'hidden' ? '恢复前台可见' : '隐藏资源' }}
        </UiButton>
      </template>
    </AppPageHeader>

    <AppAlert v-if="feedback" variant="info" :title="feedback" />
    <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

    <div class="grid gap-6 xl:grid-cols-[2fr_1fr]">
      <div class="space-y-6">
        <AppCard title="资源简介" description="详情页集中展示正文信息、标签和文件列表。">
          <p class="text-sm leading-7 text-slate-700">{{ release.description }}</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <RouterLink
              v-for="tag in release.tags"
              :key="tag.slug"
              :to="`/tags/${tag.slug}`"
              class="rounded-full bg-slate-100 px-3 py-1.5 text-sm text-slate-700"
            >
              {{ tag.name }}
            </RouterLink>
          </div>
        </AppCard>

        <AppCard title="文件列表" description="由后端解析 torrent 后写入 release_files。">
          <div class="space-y-3">
            <div
              v-for="file in release.files"
              :key="file.path"
              class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm"
            >
              <div class="font-medium text-slate-900">{{ file.path }}</div>
              <div class="mt-1 text-slate-500">{{ formatBytes(file.sizeBytes) }}</div>
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
              <dd>{{ release.category.name }}</dd>
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
              <dt class="text-slate-500">发布者</dt>
              <dd>{{ release.createdBy.displayName }}</dd>
            </div>
            <div class="flex items-center justify-between gap-3">
              <dt class="text-slate-500">活跃 Peers</dt>
              <dd>{{ release.activePeers }}</dd>
            </div>
          </dl>
        </AppCard>
      </div>
    </div>

    <AppConfirmDialog
      :open="visibilityDialogOpen"
      :title="release.status === 'hidden' ? '确认恢复该资源' : '确认隐藏该资源'"
      :description="
        release.status === 'hidden'
          ? '恢复后，这个资源会重新回到前台列表、分类页和标签页中。'
          : '隐藏后，这个资源会从前台浏览入口移除，仅管理员仍可查看和恢复。'
      "
      :confirm-label="release.status === 'hidden' ? '确认恢复' : '确认隐藏'"
      :tone="release.status === 'hidden' ? 'primary' : 'warning'"
      :pending="pendingVisibilityAction"
      @close="visibilityDialogOpen = false"
      @confirm="toggleVisibility"
    >
      <p>这个操作不会删除资源文件和审计记录，只调整前台访问可见性。</p>
    </AppConfirmDialog>
  </template>
</template>
