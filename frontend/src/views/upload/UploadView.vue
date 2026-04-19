<script setup lang="ts">
import { computed, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { createRelease } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';

interface UploadResultItem {
  fileName: string;
  status: 'success' | 'error';
  detail: string;
}

const text = {
  pageTitle: '\u4e0a\u4f20\u79cd\u5b50',
  pageDescription:
    '\u652f\u6301\u4e00\u6b21\u9009\u62e9\u591a\u4e2a .torrent \u6587\u4ef6\uff0c\u7cfb\u7edf\u4f1a\u9010\u4e2a\u521b\u5efa\u53d1\u5e03\uff0c\u5e76\u4fdd\u7559\u5931\u8d25\u9879\u65b9\u4fbf\u91cd\u8bd5\u3002',
  cardTitle: '\u6279\u91cf\u4e0a\u4f20 .torrent',
  cardDescription:
    '\u9ed8\u8ba4\u7acb\u5373\u53d1\u5e03\uff0c\u6807\u9898\u7531\u540e\u7aef\u6309\u79cd\u5b50\u7ed3\u6784\u751f\u6210\uff1a\u5355\u6587\u4ef6\u53d6\u4e3b\u6587\u4ef6\u540d\uff1b\u591a\u6587\u4ef6\u4e14\u8def\u5f84\u542b\u5b50\u76ee\u5f55\u65f6\u53d6\u6839\u6587\u4ef6\u5939\u540d\uff1b\u591a\u6587\u4ef6\u4e14\u5747\u5728\u6839\u76ee\u5f55\u5e73\u94fa\u65f6\u53d6\u9996\u4e2a\u6587\u4ef6\u540d\uff08\u5747\u53bb\u6389\u6269\u5c55\u540d\uff09\u3002',
  fileLabel: 'torrent \u6587\u4ef6',
  emptySelectionDescription:
    '\u652f\u6301\u4e00\u6b21\u9009\u62e9\u591a\u4e2a .torrent \u6587\u4ef6\uff0c\u7cfb\u7edf\u4f1a\u9010\u4e2a\u521b\u5efa\u8d44\u6e90\u53d1\u5e03\u3002',
  singleSelectionPrefix: '\u5df2\u9009\u62e9 1 \u4e2a\u6587\u4ef6\uff1a',
  multiSelectionPrefix: '\u5df2\u9009\u62e9 ',
  multiSelectionSuffix: ' \u4e2a\u6587\u4ef6\uff0c\u63d0\u4ea4\u540e\u4f1a\u6309\u987a\u5e8f\u9010\u4e2a\u53d1\u5e03\u3002',
  validationMessage: '\u8bf7\u5148\u9009\u62e9\u81f3\u5c11\u4e00\u4e2a .torrent \u6587\u4ef6\u3002',
  submit: '\u53d1\u5e03',
  batchSubmit: '\u6279\u91cf\u53d1\u5e03',
  submittingPrefix: '\u6b63\u5728\u53d1\u5e03 ',
  submittingFallback: '\u6b63\u5728\u53d1\u5e03...',
  pendingFiles: '\u5f85\u4e0a\u4f20\u6587\u4ef6',
  fileCountSuffix: ' \u4e2a',
  processingPrefix: '\u6b63\u5728\u5904\u7406\uff1a',
  resultCardTitle: '\u672c\u6b21\u4e0a\u4f20\u7ed3\u679c',
  resultCardDescription:
    '\u6bcf\u4e2a torrent \u90fd\u4f1a\u751f\u6210\u72ec\u7acb\u53d1\u5e03\uff0c\u5931\u8d25\u9879\u53ef\u5728\u4fee\u6b63\u540e\u91cd\u65b0\u63d0\u4ea4\u3002',
  successTag: '\u6210\u529f',
  errorTag: '\u5931\u8d25',
  successDetailPrefix: '\u5df2\u53d1\u5e03\u4e3a\uff1a',
  errorDetailFallback: '\u53d1\u5e03\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002',
  fullSuccessPrefix: '\u5df2\u5b8c\u6210\u6279\u91cf\u53d1\u5e03\uff0c\u5171 ',
  fullSuccessSuffix: ' \u4e2a torrent\u3002',
  partialSuccessPrefix: '\u5df2\u6210\u529f\u53d1\u5e03 ',
  partialSuccessSuffix: ' \u4e2a torrent\u3002',
  partialFailurePrefix: '\u4ecd\u6709 ',
  partialFailureMiddle:
    ' \u4e2a\u6587\u4ef6\u53d1\u5e03\u5931\u8d25\uff0c\u5931\u8d25\u9879\u5df2\u4fdd\u7559\uff0c\u53ef\u76f4\u63a5\u91cd\u8bd5\u3002',
  fullFailure:
    '\u6240\u9009\u6587\u4ef6\u5747\u672a\u53d1\u5e03\u6210\u529f\uff0c\u8bf7\u68c0\u67e5\u4e0b\u65b9\u7ed3\u679c\u540e\u91cd\u8bd5\u3002',
} as const;

const authStore = useAuthStore();
const submitting = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const fileInputKey = ref(0);
const selectedFiles = ref<File[]>([]);
const uploadResults = ref<UploadResultItem[]>([]);
const activeFileName = ref('');
const submissionTotal = ref(0);

const validationMessage = computed(() => {
  if (!selectedFiles.value.length) {
    return text.validationMessage;
  }

  return '';
});

const canSubmit = computed(() => !validationMessage.value && !submitting.value);
const submitButtonLabel = computed(() => {
  if (submitting.value) {
    return submissionTotal.value
      ? `${text.submittingPrefix}${uploadResults.value.length}/${submissionTotal.value}`
      : text.submittingFallback;
  }

  return selectedFiles.value.length > 1 ? text.batchSubmit : text.submit;
});

const selectedFilesDescription = computed(() => {
  const count = selectedFiles.value.length;

  if (!count) {
    return text.emptySelectionDescription;
  }

  if (count === 1) {
    return `${text.singleSelectionPrefix}${selectedFiles.value[0]?.name ?? ''}`;
  }

  return `${text.multiSelectionPrefix}${count}${text.multiSelectionSuffix}`;
});

function buildFileKey(file: File, index: number) {
  return `${file.name}-${file.size}-${file.lastModified}-${index}`;
}

function formatFileSize(size: number) {
  if (size <= 0) {
    return '0 B';
  }

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const exponent = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  const value = size / 1024 ** exponent;
  const digits = exponent === 0 ? 0 : value >= 100 ? 0 : value >= 10 ? 1 : 2;
  return `${value.toFixed(digits)} ${units[exponent]}`;
}

function clearFileInput() {
  fileInputKey.value += 1;
}

function handleTorrentChange(event: Event) {
  const input = event.target as HTMLInputElement;

  selectedFiles.value = Array.from(input.files ?? []);
  uploadResults.value = [];
  feedback.value = '';
  errorMessage.value = '';
  activeFileName.value = '';
  submissionTotal.value = 0;
}

async function submit() {
  if (!authStore.currentUser) return;
  if (!canSubmit.value) {
    feedback.value = '';
    errorMessage.value = validationMessage.value;
    return;
  }

  const pendingFiles = [...selectedFiles.value];
  const failedFiles: File[] = [];

  errorMessage.value = '';
  feedback.value = '';
  uploadResults.value = [];
  submitting.value = true;
  submissionTotal.value = pendingFiles.length;

  try {
    for (const file of pendingFiles) {
      activeFileName.value = file.name;

      try {
        const release = await createRelease(
          {
            torrentFile: file,
            torrentFileName: file.name,
            status: 'published',
          },
          authStore.currentUser,
        );

        uploadResults.value.push({
          fileName: file.name,
          status: 'success',
          detail: `${text.successDetailPrefix}${release.title}`,
        });
      } catch (error) {
        failedFiles.push(file);
        uploadResults.value.push({
          fileName: file.name,
          status: 'error',
          detail: error instanceof Error ? error.message : text.errorDetailFallback,
        });
      }
    }

    const successCount = uploadResults.value.filter((item) => item.status === 'success').length;
    const failedCount = failedFiles.length;

    if (successCount > 0) {
      feedback.value =
        failedCount > 0
          ? `${text.partialSuccessPrefix}${successCount}${text.partialSuccessSuffix}`
          : `${text.fullSuccessPrefix}${successCount}${text.fullSuccessSuffix}`;
    }

    if (failedCount > 0) {
      errorMessage.value =
        successCount > 0
          ? `${text.partialFailurePrefix}${failedCount}${text.partialFailureMiddle}`
          : text.fullFailure;
    }

    selectedFiles.value = failedFiles;
    clearFileInput();
  } finally {
    activeFileName.value = '';
    submitting.value = false;
  }
}
</script>

<template>
  <AppPageHeader :title="text.pageTitle" :description="text.pageDescription" />

  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

  <div class="mx-auto max-w-3xl space-y-6">
    <AppCard :title="text.cardTitle" :description="text.cardDescription">
      <div class="space-y-5">
        <div>
          <label class="app-field-label">{{ text.fileLabel }}</label>
          <input
            :key="fileInputKey"
            type="file"
            multiple
            accept=".torrent,application/x-bittorrent"
            class="block h-auto min-h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            @change="handleTorrentChange"
          />
          <p class="app-field-help">{{ selectedFilesDescription }}</p>
        </div>

        <div v-if="selectedFiles.length" class="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm font-semibold text-slate-900">{{ text.pendingFiles }}</p>
            <span class="text-xs text-slate-500">{{ selectedFiles.length }}{{ text.fileCountSuffix }}</span>
          </div>
          <ul class="mt-3 max-h-64 space-y-2 overflow-y-auto">
            <li
              v-for="(file, index) in selectedFiles"
              :key="buildFileKey(file, index)"
              class="flex items-center justify-between gap-3 rounded-lg bg-white px-3 py-2 text-sm text-slate-700 shadow-sm ring-1 ring-slate-200"
            >
              <span class="truncate">{{ file.name }}</span>
              <span class="shrink-0 text-xs text-slate-500">{{ formatFileSize(file.size) }}</span>
            </li>
          </ul>
        </div>

        <div
          v-if="submitting && activeFileName"
          class="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800"
        >
          {{ text.processingPrefix }}{{ activeFileName }}
        </div>
      </div>

      <template #footer>
        <UiButton variant="primary" :disabled="!canSubmit" @click="submit">
          {{ submitButtonLabel }}
        </UiButton>
      </template>
    </AppCard>

    <AppCard
      v-if="uploadResults.length"
      :title="text.resultCardTitle"
      :description="text.resultCardDescription"
    >
      <ul class="space-y-3">
        <li
          v-for="(item, index) in uploadResults"
          :key="`${item.fileName}-${index}`"
          :class="[
            'rounded-xl border px-4 py-3',
            item.status === 'success'
              ? 'border-green-200 bg-green-50 text-green-900'
              : 'border-red-200 bg-red-50 text-red-900',
          ]"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold">{{ item.fileName }}</p>
              <p class="mt-1 text-sm/6 opacity-90">{{ item.detail }}</p>
            </div>
            <span
              :class="[
                'shrink-0 rounded-full px-2.5 py-1 text-xs font-medium',
                item.status === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700',
              ]"
            >
              {{ item.status === 'success' ? text.successTag : text.errorTag }}
            </span>
          </div>
        </li>
      </ul>
    </AppCard>
  </div>
</template>
