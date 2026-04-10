<script setup lang="ts">
import { computed, ref } from 'vue';
import { FileUp } from 'lucide-vue-next';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { privatizeTorrent } from '@/services/releases';

const toolFile = ref<File | null>(null);
const fileInputKey = ref(0);
const submitting = ref(false);
const feedback = ref('');
const errorMessage = ref('');

const fileName = computed(() => toolFile.value?.name ?? '');
const canSubmit = computed(() => !!toolFile.value && !submitting.value);

function handleTorrentChange(event: Event) {
  const input = event.target as HTMLInputElement;
  toolFile.value = input.files?.[0] ?? null;
}

function resetForm() {
  toolFile.value = null;
  fileInputKey.value += 1;
}

async function submit() {
  if (!toolFile.value) {
    feedback.value = '';
    errorMessage.value = '请先选择一个 .torrent 文件。';
    return;
  }

  submitting.value = true;
  feedback.value = '';
  errorMessage.value = '';

  try {
    const filename = await privatizeTorrent(toolFile.value);
    feedback.value = `已生成并开始下载：${filename}`;
    resetForm();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '修改 torrent 失败。';
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <AppPageHeader
    title="改种工具"
    description="上传任意 torrent，系统会直接改成私有种子，并写入当前登录用户自己的 tracker 凭证后回传下载。"
  />

  <div class="mx-auto max-w-4xl space-y-6">
    <AppAlert v-if="feedback" variant="success" title="改种完成" :description="feedback" />
    <AppAlert v-if="errorMessage" variant="error" title="改种失败" :description="errorMessage" />

    <AppCard
      title="一键私有化"
      description="不会让你先做 private 检查。上传后后端直接改写为私有种子，并注入当前账号自己的 passkey tracker。"
    >
      <div class="space-y-5">
        <div class="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
          <div class="flex items-start gap-3">
            <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
              <FileUp class="h-5 w-5" />
            </div>
            <div class="space-y-1">
              <h3 class="text-base font-semibold text-slate-900">写入当前用户自己的 tracker</h3>
              <p class="text-sm leading-6 text-slate-600">
                输出种子里的 announce 会绑定当前登录用户的 passkey，不会复用别人的 tracker 凭证。
              </p>
            </div>
          </div>
        </div>

        <div>
          <label class="app-field-label">torrent 文件</label>
          <input
            :key="fileInputKey"
            type="file"
            accept=".torrent,application/x-bittorrent"
            class="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            @change="handleTorrentChange"
          />
          <p class="app-field-help">
            {{ fileName ? `已选择：${fileName}` : '请选择任意一个 .torrent 文件。' }}
          </p>
        </div>
      </div>

      <template #footer>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <p class="text-sm text-slate-500">生成后的种子会立即下载到本地。</p>
          <UiButton variant="primary" :disabled="!canSubmit" @click="submit">
            {{ submitting ? '正在修改...' : '私有化并下载' }}
          </UiButton>
        </div>
      </template>
    </AppCard>
  </div>
</template>
