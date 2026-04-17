<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { createRelease } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const submitting = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const fileInputKey = ref(0);

const form = reactive({
  torrentFile: null as File | null,
  torrentFileName: '',
});

const validationMessage = computed(() => {
  if (!form.torrentFile && !form.torrentFileName) {
    return '请先选择一个 .torrent 文件。';
  }

  return '';
});

const canSubmit = computed(() => !validationMessage.value && !submitting.value);

function handleTorrentChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  form.torrentFile = file;
  form.torrentFileName = file?.name ?? '';
}

function resetForm() {
  form.torrentFile = null;
  form.torrentFileName = '';
  fileInputKey.value += 1;
}

async function submit() {
  if (!authStore.currentUser) return;
  if (!canSubmit.value) {
    feedback.value = '';
    errorMessage.value = validationMessage.value;
    return;
  }

  errorMessage.value = '';
  feedback.value = '';
  submitting.value = true;

  try {
    const release = await createRelease(
      {
        torrentFile: form.torrentFile,
        torrentFileName: form.torrentFileName,
        status: 'published',
      },
      authStore.currentUser,
    );
    feedback.value = `已发布：${release.title}`;
    resetForm();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '发布失败。';
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <AppPageHeader title="上传种子" />

  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

  <div class="mx-auto max-w-3xl">
    <AppCard title="上传 .torrent">
      <div class="space-y-5">
        <div>
          <label class="app-field-label">torrent 文件</label>
          <input
            :key="fileInputKey"
            type="file"
            accept=".torrent,application/x-bittorrent"
            class="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            @change="handleTorrentChange"
          />
          <p class="app-field-help">
            {{ form.torrentFileName ? `已选择：${form.torrentFileName}` : '选择文件后直接发布。' }}
          </p>
        </div>
      </div>

      <template #footer>
        <UiButton variant="primary" :disabled="!canSubmit" @click="submit">
          {{ submitting ? '正在发布...' : '发布' }}
        </UiButton>
      </template>
    </AppCard>
  </div>
</template>
