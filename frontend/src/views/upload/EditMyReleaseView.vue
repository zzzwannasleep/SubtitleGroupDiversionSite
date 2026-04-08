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
const form = reactive({
  title: '',
  subtitle: '',
  description: '',
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

    pageErrorMessage.value = error instanceof Error ? error.message : '资源编辑页加载失败';
    state.value = 'error';
  }
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
    });
    feedback.value = '资源信息已更新。';
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存资源修改失败';
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
    <AppPageHeader title="编辑资源" description="上传者只能编辑自己发布的资源，管理员可编辑任意资源。" />
    <AppAlert v-if="feedback" variant="success" :title="feedback" />
    <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />
    <AppCard title="编辑内容" description="MVP 先覆盖标题、副标题、简介与状态等常改字段。">
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
      </div>
      <template #footer>
        <UiButton variant="primary" :disabled="submitting" @click="handleSave">
          {{ submitting ? '保存中...' : '保存修改' }}
        </UiButton>
      </template>
    </AppCard>
  </template>
</template>
