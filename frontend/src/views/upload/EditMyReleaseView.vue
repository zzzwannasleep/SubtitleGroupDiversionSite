<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { useRoute } from 'vue-router';
import AppCard from '@/components/app/AppCard.vue';
import AppForbidden from '@/components/app/AppForbidden.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppNotFound from '@/components/app/AppNotFound.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiTextarea from '@/components/ui/UiTextarea.vue';
import { editRelease, getReleaseById } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { Release } from '@/types/release';
import { canEditRelease } from '@/utils/permissions';

const route = useRoute();
const authStore = useAuthStore();
const loading = ref(true);
const release = ref<Release | null>(null);
const feedback = ref('');
const form = reactive({
  title: '',
  subtitle: '',
  description: '',
});

const state = ref<'loading' | 'ready' | 'forbidden' | 'not-found'>('loading');

onMounted(async () => {
  release.value = await getReleaseById(Number(route.params.id));

  if (!release.value) {
    state.value = 'not-found';
    loading.value = false;
    return;
  }

  if (!canEditRelease(authStore.currentUser, release.value)) {
    state.value = 'forbidden';
    loading.value = false;
    return;
  }

  form.title = release.value.title;
  form.subtitle = release.value.subtitle;
  form.description = release.value.description;
  state.value = 'ready';
  loading.value = false;
});

async function handleSave() {
  if (!release.value) return;
  release.value = await editRelease(release.value.id, {
    title: form.title,
    subtitle: form.subtitle,
    description: form.description,
    categorySlug: release.value.category.slug,
    tagSlugs: release.value.tags.map((item) => item.slug),
    status: release.value.status,
  });
  feedback.value = '资源信息已更新。';
}
</script>

<template>
  <AppLoading v-if="loading" />
  <AppNotFound v-else-if="state === 'not-found'" />
  <AppForbidden v-else-if="state === 'forbidden'" />
  <template v-else>
    <AppPageHeader title="编辑资源" description="上传者只能编辑自己发布的资源，管理员可编辑任意资源。" />
    <div v-if="feedback" class="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
      {{ feedback }}
    </div>
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
        <UiButton variant="primary" @click="handleSave">保存修改</UiButton>
      </template>
    </AppCard>
  </template>
</template>
