<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { getRssOverview } from '@/services/rss';
import type { RssOverview } from '@/types/admin';

const loading = ref(true);
const failed = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const rssOverview = ref<RssOverview | null>(null);

async function loadData() {
  loading.value = true;
  failed.value = false;

  try {
    rssOverview.value = await getRssOverview();
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

async function copyFeed(value: string, label = '个人 RSS 地址') {
  errorMessage.value = '';

  try {
    await navigator.clipboard.writeText(value);
    feedback.value = `${label}已复制。`;
  } catch {
    errorMessage.value = '复制失败，请手动复制当前地址。';
  }
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="RSS" />
  <AppLoading v-if="loading" />
  <AppError v-else-if="failed" title="RSS 加载失败" description="请稍后重试。" />
  <template v-else-if="rssOverview">
    <AppAlert v-if="feedback" variant="success" :title="feedback" />
    <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

    <div class="space-y-6">
      <AppCard
        v-if="rssOverview.personalFeed"
        title="个人 RSS"
        description="这个地址内的条目下载链接会带上你自己的 passkey，下载下来的 torrent 会自动改写成你的个人 tracker 链接。"
      >
        <div class="break-all rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900">
          {{ rssOverview.personalFeed }}
        </div>
        <template #footer>
          <UiButton variant="primary" @click="copyFeed(rssOverview.personalFeed)">复制个人 RSS</UiButton>
        </template>
      </AppCard>

      <AppCard v-else title="个人 RSS" description="当前站点不再提供通用 RSS，仅保留个人 RSS。">
        <div class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm leading-6 text-slate-600">
          当前账号暂时无法获取个人 RSS 地址，请确认已登录且 Private Tracker 已启用。
        </div>
      </AppCard>
    </div>
  </template>
</template>
