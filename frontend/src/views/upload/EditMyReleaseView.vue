<script setup lang="ts">
import { reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppError from '@/components/app/AppError.vue';
import AppForbidden from '@/components/app/AppForbidden.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppNotFound from '@/components/app/AppNotFound.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiTextarea from '@/components/ui/UiTextarea.vue';
import { isApiError } from '@/services/api';
import { editRelease, getReleaseById } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { Release } from '@/types/release';
import { canEditRelease } from '@/utils/permissions';

const route = useRoute();
const authStore = useAuthStore();
const release = ref<Release | null>(null);
const feedback = ref('');
const errorMessage = ref('');
const pageErrorMessage = ref('');
const submitting = ref(false);
const fileInputKey = ref(0);
const form = reactive({
  title: '',
  subtitle: '',
  description: '',
  torrentFile: null as File | null,
  torrentFileName: '',
});

const state = ref<'loading' | 'ready' | 'forbidden' | 'not-found' | 'error'>('loading');

async function loadRelease() {
  state.value = 'loading';
  release.value = null;
  feedback.value = '';
  errorMessage.value = '';
  pageErrorMessage.value = '';

  try {
    release.value = await getReleaseById(Number(route.params.id));

    if (!release.value) {
      state.value = 'not-found';
      return;
    }

    if (!canEditRelease(authStore.currentUser, release.value)) {
      state.value = 'forbidden';
      return;
    }

    form.title = release.value.title;
    form.subtitle = release.value.subtitle;
    form.description = release.value.description;
    form.torrentFile = null;
    form.torrentFileName = '';
    fileInputKey.value += 1;
    state.value = 'ready';
  } catch (error) {
    if (isApiError(error) && error.status === 403) {
      state.value = 'forbidden';
      return;
    }

    if (isApiError(error) && error.status === 404) {
      state.value = 'not-found';
      return;
    }

    pageErrorMessage.value = error instanceof Error ? error.message : '资源编辑页加载失败。';
    state.value = 'error';
  }
}

function handleTorrentChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  form.torrentFile = file;
  form.torrentFileName = file?.name ?? '';
}

async function handleSave() {
  if (!release.value) return;

  feedback.value = '';
  errorMessage.value = '';
  submitting.value = true;

  try {
    release.value = await editRelease(release.value.id, {
      title: form.title,
      subtitle: form.subtitle,
      description: form.description,
      categorySlug: release.value.category.slug,
      tagSlugs: release.value.tags.map((item) => item.slug),
      status: release.value.status,
      torrentFile: form.torrentFile,
      torrentFileName: form.torrentFileName,
    });
    feedback.value = form.torrentFile ? '资源信息和 torrent 已更新。' : '资源信息已更新。';
    form.torrentFile = null;
    form.torrentFileName = '';
    fileInputKey.value += 1;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存资源修改失败。';
  } finally {
    submitting.value = false;
  }
}

watch(() => route.params.id, loadRelease, { immediate: true });
</script>

<template>
  <AppLoading v-if="state === 'loading'" />
  <AppNotFound v-else-if="state === 'not-found'" />
  <AppForbidden v-else-if="state === 'forbidden'" />
  <AppError v-else-if="state === 'error'" title="编辑页加载失败" :description="pageErrorMessage">
    <template #actions>
      <UiButton variant="primary" @click="loadRelease">重试</UiButton>
    </template>
  </AppError>
  <template v-else>
    <AppPageHeader title="编辑资源" description="你可以直接替换 torrent 文件，提交后会覆盖当前资源包。" />
    <AppAlert v-if="feedback" variant="success" :title="feedback" />
    <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />
    <AppCard title="编辑内容" description="标题、副标题、简介和 torrent 文件都可以在这里一次完成更新。">
      <div class="space-y-5">
        <div>
          <label class="app-field-label">标题</label>
          <UiInput v-model="form.title" />
        </div>
        <div>
          <label class="app-field-label">副标题</label>
          <UiInput v-model="form.subtitle" />
        </div>
        <div>
          <label class="app-field-label">简介</label>
          <UiTextarea v-model="form.description" />
        </div>
        <div>
          <label class="app-field-label">替换 torrent</label>
          <input
            :key="fileInputKey"
            type="file"
            accept=".torrent,application/x-bittorrent"
            class="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            @change="handleTorrentChange"
          />
          <p class="app-field-help">
            {{ form.torrentFileName ? `本次将上传：${form.torrentFileName}` : '不选择文件则沿用当前 torrent。' }}
          </p>
        </div>
      </div>
      <template #footer>
        <UiButton variant="primary" :disabled="submitting" @click="handleSave">
          {{ submitting ? '保存中...' : '保存修改' }}
        </UiButton>
      </template>
    </AppCard>
  </template>
</template>
