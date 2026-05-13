<script setup lang="ts">
import { computed, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { createRelease } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import { formatBytes } from '@/utils/format';

interface UploadResultItem {
  fileName: string;
  status: 'success' | 'error';
  detail: string;
}

interface WebseedUploadEntry {
  file: File;
  relativePath: string;
}

type BrowserFile = File & {
  webkitRelativePath?: string;
};

const text = {
  pageTitle: '上传种子',
  pageDescription: '支持批量选择多个 .torrent 文件；如需给种子写入 webseed，可额外上传对应的分流文件或目录。',
  cardTitle: '发布与分流',
  cardDescription:
    '默认仍支持批量发种；启用分流文件后，会按 torrent 结构把实体文件转成站内直链，并在下载出来的种子里写入 webseed。',
  fileLabel: 'torrent 文件',
  emptySelectionDescription: '支持一次选择多个 .torrent 文件，系统会逐个创建资源发布。',
  singleSelectionPrefix: '已选择 1 个文件：',
  multiSelectionPrefix: '已选择 ',
  multiSelectionSuffix: ' 个文件，提交后会按顺序逐个发布。',
  validationMessage: '请先选择至少 1 个 .torrent 文件。',
  webseedValidationMessage: '启用分流文件时，一次只能发布 1 个 torrent。',
  submit: '发布',
  batchSubmit: '批量发布',
  submittingPrefix: '正在发布 ',
  submittingFallback: '正在发布...',
  pendingFiles: '待上传文件',
  pendingWebseedFiles: '待写入 webseed 的分流文件',
  fileCountSuffix: ' 个',
  processingPrefix: '正在处理：',
  resultCardTitle: '本次上传结果',
  resultCardDescription: '每个 torrent 都会生成独立发布，失败项会保留，方便你修正后重试。',
  successTag: '成功',
  errorTag: '失败',
  successDetailPrefix: '已发布为：',
  errorDetailFallback: '发布失败，请稍后重试。',
  fullSuccessPrefix: '已完成批量发布，共 ',
  fullSuccessSuffix: ' 个 torrent。',
  partialSuccessPrefix: '已成功发布 ',
  partialSuccessSuffix: ' 个 torrent。',
  partialFailurePrefix: '仍有 ',
  partialFailureMiddle: ' 个文件发布失败，失败项已保留，可直接重试。',
  fullFailure: '所选文件均未发布成功，请检查下方结果后重试。',
} as const;

const authStore = useAuthStore();
const submitting = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const fileInputKey = ref(0);
const webseedFileInputKey = ref(0);
const webseedDirectoryInputKey = ref(0);
const selectedFiles = ref<File[]>([]);
const webseedEntries = ref<WebseedUploadEntry[]>([]);
const uploadResults = ref<UploadResultItem[]>([]);
const activeFileName = ref('');
const submissionTotal = ref(0);

const validationMessage = computed(() => {
  if (!selectedFiles.value.length) {
    return text.validationMessage;
  }
  if (webseedEntries.value.length && selectedFiles.value.length !== 1) {
    return text.webseedValidationMessage;
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

const webseedDescription = computed(() => {
  if (!webseedEntries.value.length) {
    return '可选。单文件 torrent 请选择对应文件；多文件 torrent 建议选择完整目录，以保留原始路径结构。';
  }

  return `已准备 ${webseedEntries.value.length} 个分流文件，下载种子时会自动写入 webseed。`;
});

function buildFileKey(file: File, index: number) {
  return `${file.name}-${file.size}-${file.lastModified}-${index}`;
}

function buildWebseedKey(entry: WebseedUploadEntry, index: number) {
  return `${entry.relativePath}-${entry.file.size}-${entry.file.lastModified}-${index}`;
}

function clearTorrentInput() {
  fileInputKey.value += 1;
}

function clearWebseedInputs() {
  webseedFileInputKey.value += 1;
  webseedDirectoryInputKey.value += 1;
}

function resetTransientState() {
  uploadResults.value = [];
  feedback.value = '';
  errorMessage.value = '';
  activeFileName.value = '';
  submissionTotal.value = 0;
}

function handleTorrentChange(event: Event) {
  const input = event.target as HTMLInputElement;

  selectedFiles.value = Array.from(input.files ?? []);
  resetTransientState();
}

function setWebseedEntries(files: BrowserFile[], pickRelativePath: (file: BrowserFile) => string) {
  webseedEntries.value = files.map((file) => ({
    file,
    relativePath: pickRelativePath(file),
  }));
  resetTransientState();
}

function handleWebseedFilesChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []) as BrowserFile[];
  setWebseedEntries(files, (file) => file.name);
}

function handleWebseedDirectoryChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []) as BrowserFile[];
  setWebseedEntries(files, (file) => file.webkitRelativePath || file.name);
}

function clearWebseedSelection() {
  webseedEntries.value = [];
  clearWebseedInputs();
  resetTransientState();
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
            webseedFiles: webseedEntries.value.map((item) => item.file),
            webseedPaths: webseedEntries.value.map((item) => item.relativePath),
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
    clearTorrentInput();

    if (!failedCount) {
      webseedEntries.value = [];
      clearWebseedInputs();
    }
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

  <div class="mx-auto max-w-4xl space-y-6">
    <AppCard :title="text.cardTitle" :description="text.cardDescription">
      <div class="space-y-6">
        <section class="space-y-4">
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

          <div v-if="selectedFiles.length" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
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
                <span class="shrink-0 text-xs text-slate-500">{{ formatBytes(file.size) }}</span>
              </li>
            </ul>
          </div>
        </section>

        <section class="rounded-3xl border border-slate-200 bg-slate-50/80 p-5">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div class="max-w-2xl space-y-2">
              <p class="text-sm font-semibold text-slate-900">可选分流文件 / 目录</p>
              <p class="text-sm leading-6 text-slate-500">
                单文件 torrent 请选择对应实体文件；多文件 torrent 建议直接选择目录，系统会保留相对路径并生成 webseed。
              </p>
              <p class="text-xs leading-6 text-slate-500">{{ webseedDescription }}</p>
            </div>
            <UiButton v-if="webseedEntries.length" size="sm" variant="ghost" @click="clearWebseedSelection">
              清空分流文件
            </UiButton>
          </div>

          <div class="mt-4 grid gap-4 md:grid-cols-2">
            <div class="rounded-2xl border border-dashed border-slate-300 bg-white p-4">
              <label class="app-field-label">上传单个或多个文件</label>
              <input
                :key="webseedFileInputKey"
                type="file"
                multiple
                class="block h-auto min-h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                @change="handleWebseedFilesChange"
              />
              <p class="mt-2 text-xs leading-6 text-slate-500">适合单文件 torrent，或多文件但所有内容都在根目录时使用。</p>
            </div>

            <div class="rounded-2xl border border-dashed border-slate-300 bg-white p-4">
              <label class="app-field-label">上传完整目录</label>
              <input
                :key="webseedDirectoryInputKey"
                type="file"
                multiple
                webkitdirectory
                directory
                class="block h-auto min-h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                @change="handleWebseedDirectoryChange"
              />
              <p class="mt-2 text-xs leading-6 text-slate-500">适合整季、合集等多文件 torrent，可保留目录层级。</p>
            </div>
          </div>

          <div v-if="webseedEntries.length" class="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
            <div class="flex items-center justify-between gap-3">
              <p class="text-sm font-semibold text-slate-900">{{ text.pendingWebseedFiles }}</p>
              <span class="text-xs text-slate-500">{{ webseedEntries.length }}{{ text.fileCountSuffix }}</span>
            </div>
            <ul class="mt-3 max-h-72 space-y-2 overflow-y-auto">
              <li
                v-for="(entry, index) in webseedEntries"
                :key="buildWebseedKey(entry, index)"
                class="flex items-center justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700 ring-1 ring-slate-200"
              >
                <div class="min-w-0">
                  <p class="truncate font-medium text-slate-900">{{ entry.relativePath }}</p>
                  <p class="truncate text-xs text-slate-500">{{ entry.file.name }}</p>
                </div>
                <span class="shrink-0 text-xs text-slate-500">{{ formatBytes(entry.file.size) }}</span>
              </li>
            </ul>
          </div>
        </section>

        <div
          v-if="submitting && activeFileName"
          class="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800"
        >
          {{ text.processingPrefix }}{{ activeFileName }}
        </div>
      </div>

      <template #footer>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <p class="text-sm text-slate-500">
            {{
              webseedEntries.length
                ? '当前已启用 webseed 写入，提交时只会处理 1 个 torrent。'
                : '未选择分流文件时，仍按原有模式支持批量上传多个 torrent。'
            }}
          </p>
          <UiButton variant="primary" :disabled="!canSubmit" @click="submit">
            {{ submitButtonLabel }}
          </UiButton>
        </div>
      </template>
    </AppCard>

    <AppCard v-if="uploadResults.length" :title="text.resultCardTitle" :description="text.resultCardDescription">
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
