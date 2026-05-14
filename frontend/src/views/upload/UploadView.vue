<script setup lang="ts">
import { computed, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { createRelease, listWebseedLibrary, previewWebseedLibrary } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { WebseedLibraryEntry, WebseedLibraryListing, WebseedLibraryPreview } from '@/types/release';
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

type WebseedSourceMode = 'upload' | 'library';

const text = {
  pageTitle: '上传种子',
  pageDescription: '支持批量选择多个 .torrent 文件；如需给种子写入 webseed，可选择本地分流文件，或直接引用服务器映射目录里的文件与文件夹。',
  cardTitle: '发布与分流',
  cardDescription:
    '默认仍支持批量发种；启用 webseed 后，一次只处理 1 个 torrent，并把映射目录中的真实文件地址写回下载种子。',
  fileLabel: 'torrent 文件',
  emptySelectionDescription: '支持一次选择多个 .torrent 文件，系统会逐个创建资源发布。',
  singleSelectionPrefix: '已选择 1 个文件：',
  multiSelectionPrefix: '已选择 ',
  multiSelectionSuffix: ' 个文件，提交后会按顺序逐个发布。',
  validationMessage: '请先选择至少 1 个 .torrent 文件。',
  webseedValidationMessage: '启用 webseed 时，一次只能发布 1 个 torrent。',
  submit: '发布',
  batchSubmit: '批量发布',
  submittingPrefix: '正在发布 ',
  submittingFallback: '正在发布...',
  pendingFiles: '待上传文件',
  pendingWebseedFiles: '待写入 webseed 的本地文件',
  pendingServerPath: '已选择的服务器路径',
  fileCountSuffix: ' 个',
  processingPrefix: '正在处理：',
  resultCardTitle: '本次上传结果',
  resultCardDescription: '每个 torrent 都会生成独立发布，失败项会保留，方便修正后重试。',
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
const webseedMode = ref<WebseedSourceMode>('upload');
const selectedLibraryEntry = ref<WebseedLibraryEntry | null>(null);
const libraryState = ref<WebseedLibraryListing>({
  currentPath: '',
  parentPath: null,
  entries: [],
});
const libraryLoaded = ref(false);
const libraryLoading = ref(false);
const libraryError = ref('');
const previewLoading = ref(false);
const previewError = ref('');
const webseedPreview = ref<WebseedLibraryPreview | null>(null);
const uploadResults = ref<UploadResultItem[]>([]);
const activeFileName = ref('');
const submissionTotal = ref(0);

const hasWebseedSelection = computed(
  () => webseedEntries.value.length > 0 || Boolean(selectedLibraryEntry.value),
);
const canPreviewLibraryLinks = computed(
  () => selectedFiles.value.length === 1 && Boolean(selectedLibraryEntry.value),
);

const validationMessage = computed(() => {
  if (!selectedFiles.value.length) {
    return text.validationMessage;
  }
  if (hasWebseedSelection.value && selectedFiles.value.length !== 1) {
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
  if (webseedEntries.value.length) {
    return `已准备 ${webseedEntries.value.length} 个本地分流文件，下载种子时会自动写入 webseed。`;
  }
  if (selectedLibraryEntry.value) {
    return `已选择服务器${selectedLibraryEntry.value.kind === 'directory' ? '目录' : '文件'}：${selectedLibraryEntry.value.path}`;
  }
  return '可选。单文件 torrent 可直接选择文件；多文件 torrent 建议选择完整目录，保持与 torrent 内部路径一致。';
});

function buildFileKey(file: File, index: number) {
  return `${file.name}-${file.size}-${file.lastModified}-${index}`;
}

function buildWebseedKey(entry: WebseedUploadEntry, index: number) {
  return `${entry.relativePath}-${entry.file.size}-${entry.file.lastModified}-${index}`;
}

function buildLibraryKey(entry: WebseedLibraryEntry) {
  return `${entry.kind}-${entry.path}`;
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
  previewError.value = '';
  webseedPreview.value = null;
}

function handleTorrentChange(event: Event) {
  const input = event.target as HTMLInputElement;
  selectedFiles.value = Array.from(input.files ?? []);
  resetTransientState();
}

function setWebseedEntries(files: BrowserFile[], pickRelativePath: (file: BrowserFile) => string) {
  webseedMode.value = 'upload';
  selectedLibraryEntry.value = null;
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
  selectedLibraryEntry.value = null;
  clearWebseedInputs();
  resetTransientState();
}

async function loadLibrary(path = '') {
  libraryLoading.value = true;
  libraryError.value = '';
  try {
    libraryState.value = await listWebseedLibrary(path);
    libraryLoaded.value = true;
  } catch (error) {
    libraryError.value = error instanceof Error ? error.message : '加载映射目录失败，请稍后重试。';
  } finally {
    libraryLoading.value = false;
  }
}

async function switchWebseedMode(mode: WebseedSourceMode) {
  webseedMode.value = mode;
  if (mode === 'library' && !libraryLoaded.value && !libraryLoading.value) {
    await loadLibrary('');
  }
}

function selectLibraryEntry(entry: WebseedLibraryEntry) {
  selectedLibraryEntry.value = entry;
  webseedEntries.value = [];
  clearWebseedInputs();
  resetTransientState();
}

function selectCurrentDirectory() {
  if (!libraryState.value.currentPath) return;
  const currentPath = libraryState.value.currentPath;
  const segments = currentPath.split('/').filter(Boolean);
  selectedLibraryEntry.value = {
    name: segments[segments.length - 1] ?? currentPath,
    path: currentPath,
    kind: 'directory',
    sizeBytes: null,
  };
  webseedEntries.value = [];
  clearWebseedInputs();
  resetTransientState();
}

async function generateLibraryPreview() {
  if (!canPreviewLibraryLinks.value || !selectedLibraryEntry.value) {
    previewError.value = '请先选择 1 个 torrent 文件和 1 个服务器资源。';
    webseedPreview.value = null;
    return;
  }

  previewLoading.value = true;
  previewError.value = '';
  try {
    webseedPreview.value = await previewWebseedLibrary({
      torrentFile: selectedFiles.value[0] as File,
      webseedRootPath: selectedLibraryEntry.value.path,
    });
  } catch (error) {
    webseedPreview.value = null;
    previewError.value = error instanceof Error ? error.message : '生成直链预览失败，请稍后重试。';
  } finally {
    previewLoading.value = false;
  }
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
            webseedFiles: webseedEntries.value.length ? webseedEntries.value.map((item) => item.file) : undefined,
            webseedPaths: webseedEntries.value.length ? webseedEntries.value.map((item) => item.relativePath) : undefined,
            webseedRootPath: selectedLibraryEntry.value?.path,
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
      clearWebseedSelection();
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
              <p class="text-sm font-semibold text-slate-900">可选 webseed 来源</p>
              <p class="text-sm leading-6 text-slate-500">
                可以上传本地分流文件，也可以直接选择服务器映射目录中的文件或文件夹。多文件 torrent
                建议选择与 torrent 根目录一致的完整文件夹。
              </p>
              <p class="text-xs leading-6 text-slate-500">{{ webseedDescription }}</p>
            </div>
            <UiButton v-if="hasWebseedSelection" size="sm" variant="ghost" @click="clearWebseedSelection">
              清空 webseed 选择
            </UiButton>
          </div>

          <div class="mt-4 flex flex-wrap gap-3">
            <UiButton
              size="sm"
              :variant="webseedMode === 'upload' ? 'primary' : 'secondary'"
              @click="switchWebseedMode('upload')"
            >
              本地上传
            </UiButton>
            <UiButton
              size="sm"
              :variant="webseedMode === 'library' ? 'primary' : 'secondary'"
              @click="switchWebseedMode('library')"
            >
              服务器目录
            </UiButton>
          </div>

          <div v-if="webseedMode === 'upload'" class="mt-4 grid gap-4 md:grid-cols-2">
            <div class="rounded-2xl border border-dashed border-slate-300 bg-white p-4">
              <label class="app-field-label">上传单个或多个文件</label>
              <input
                :key="webseedFileInputKey"
                type="file"
                multiple
                class="block h-auto min-h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                @change="handleWebseedFilesChange"
              />
              <p class="mt-2 text-xs leading-6 text-slate-500">适合单文件 torrent，或多文件但都在根目录时使用。</p>
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

          <div v-else class="mt-4 space-y-4">
            <div class="flex flex-wrap items-center gap-3">
              <UiButton size="sm" variant="secondary" :disabled="libraryLoading" @click="loadLibrary(libraryState.currentPath)">
                刷新目录
              </UiButton>
              <UiButton
                size="sm"
                variant="ghost"
                :disabled="libraryLoading || libraryState.parentPath === null"
                @click="loadLibrary(libraryState.parentPath ?? '')"
              >
                返回上一级
              </UiButton>
              <UiButton
                v-if="libraryState.currentPath"
                size="sm"
                variant="ghost"
                :disabled="libraryLoading"
                @click="selectCurrentDirectory"
              >
                选择当前文件夹
              </UiButton>
              <p class="text-xs text-slate-500">
                当前目录：{{ libraryState.currentPath || '/' }}
              </p>
            </div>

            <AppAlert v-if="libraryError" variant="error" :title="libraryError" />

            <div class="rounded-2xl border border-slate-200 bg-white p-4">
              <p v-if="libraryLoading" class="text-sm text-slate-500">正在加载映射目录…</p>
              <p v-else-if="!libraryState.entries.length" class="text-sm text-slate-500">当前目录为空。</p>
              <ul v-else class="space-y-2">
                <li
                  v-for="entry in libraryState.entries"
                  :key="buildLibraryKey(entry)"
                  class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-3"
                >
                  <div class="min-w-0">
                    <p class="truncate text-sm font-medium text-slate-900">
                      {{ entry.kind === 'directory' ? '目录' : '文件' }} · {{ entry.name }}
                    </p>
                    <p class="truncate text-xs text-slate-500">{{ entry.path }}</p>
                  </div>
                  <div class="flex flex-wrap items-center gap-2">
                    <span v-if="entry.sizeBytes !== null" class="text-xs text-slate-500">
                      {{ formatBytes(entry.sizeBytes) }}
                    </span>
                    <UiButton
                      v-if="entry.kind === 'directory'"
                      size="sm"
                      variant="secondary"
                      @click="loadLibrary(entry.path)"
                    >
                      打开
                    </UiButton>
                    <UiButton size="sm" variant="ghost" @click="selectLibraryEntry(entry)">
                      {{ entry.kind === 'directory' ? '选择目录' : '选择文件' }}
                    </UiButton>
                  </div>
                </li>
              </ul>
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

          <div v-if="selectedLibraryEntry" class="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
            <div class="flex items-center justify-between gap-3">
              <p class="text-sm font-semibold text-slate-900">{{ text.pendingServerPath }}</p>
              <span class="text-xs text-slate-500">
                {{ selectedLibraryEntry.kind === 'directory' ? '目录' : '文件' }}
              </span>
            </div>
            <div class="mt-3 rounded-lg bg-slate-50 px-3 py-3 text-sm text-slate-700 ring-1 ring-slate-200">
              <p class="font-medium text-slate-900">{{ selectedLibraryEntry.name }}</p>
              <p class="mt-1 break-all text-xs text-slate-500">{{ selectedLibraryEntry.path }}</p>
            </div>
            <div class="mt-4 flex flex-wrap items-center gap-3">
              <UiButton
                size="sm"
                variant="secondary"
                :disabled="previewLoading || !canPreviewLibraryLinks"
                @click="generateLibraryPreview"
              >
                {{ previewLoading ? '生成中...' : webseedPreview ? '刷新直链预览' : '生成直链预览' }}
              </UiButton>
              <p class="text-xs text-slate-500">
                {{
                  canPreviewLibraryLinks
                    ? '会按当前 torrent 结构解析目录并列出逐文件直链。'
                    : '需要先选择 1 个 torrent 文件后才能生成直链预览。'
                }}
              </p>
            </div>
            <AppAlert v-if="previewError" class="mt-4" variant="error" :title="previewError" />
            <div v-if="webseedPreview" class="mt-4 space-y-4">
              <div class="rounded-lg bg-slate-50 px-3 py-3 ring-1 ring-slate-200">
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Torrent Webseed Root URL</p>
                <p class="mt-2 break-all text-sm text-slate-900">{{ webseedPreview.rootUrl || '-' }}</p>
              </div>
              <div class="rounded-lg bg-slate-50 px-3 py-3 ring-1 ring-slate-200">
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">qB HTTP Seed URL</p>
                <p class="mt-2 break-all text-sm text-slate-900">{{ webseedPreview.httpSeedUrl }}</p>
              </div>
              <div class="rounded-lg bg-slate-50 px-3 py-3 ring-1 ring-slate-200">
                <div class="flex items-center justify-between gap-3">
                  <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Resolved File Links</p>
                  <span class="text-xs text-slate-500">{{ webseedPreview.files.length }} 个</span>
                </div>
                <ul class="mt-3 max-h-72 space-y-3 overflow-y-auto">
                  <li
                    v-for="item in webseedPreview.files"
                    :key="`${item.relativePath}-${item.directUrl}`"
                    class="rounded-lg bg-white px-3 py-3 text-sm text-slate-700 ring-1 ring-slate-200"
                  >
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <p class="min-w-0 flex-1 truncate font-medium text-slate-900">{{ item.relativePath }}</p>
                      <span class="text-xs text-slate-500">{{ formatBytes(item.sizeBytes) }}</span>
                    </div>
                    <p class="mt-1 break-all text-xs text-slate-500">{{ item.sourcePath }}</p>
                    <p class="mt-2 break-all text-xs text-blue-700">{{ item.directUrl }}</p>
                  </li>
                </ul>
              </div>
            </div>
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
              hasWebseedSelection
                ? '当前已启用 webseed 写入，提交时只会处理 1 个 torrent。'
                : '未启用 webseed 时，仍按原有模式支持批量上传多个 torrent。'
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
