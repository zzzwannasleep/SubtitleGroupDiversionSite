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

async function copyFeed(value: string) {
  errorMessage.value = '';

  try {
    await navigator.clipboard.writeText(value);
    feedback.value = 'RSS 地址已复制。';
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

    <AppCard title="通用地址">
      <div class="break-all rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
        {{ rssOverview.generalFeed }}
      </div>
      <template #footer>
        <UiButton variant="primary" @click="copyFeed(rssOverview.generalFeed)">复制 RSS</UiButton>
      </template>
    </AppCard>
  </template>
</template>
