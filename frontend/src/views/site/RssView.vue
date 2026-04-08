<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { getRssOverview } from '@/services/rss';
import { useAuthStore } from '@/stores/auth';
import type { RssOverview } from '@/types/admin';

const authStore = useAuthStore();
const loading = ref(true);
const failed = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const rssOverview = ref<RssOverview | null>(null);

async function loadData() {
  if (!authStore.currentUser) return;
  loading.value = true;
  failed.value = false;

  try {
    rssOverview.value = await getRssOverview(authStore.currentUser);
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
    feedback.value = 'RSS 地址已复制，请注意其中包含个人身份信息。';
  } catch {
    errorMessage.value = '复制失败，请手动复制当前地址。';
  }
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="RSS 订阅" description="支持全量、分类与标签级地址，一键复制即可接入下载器。" />
  <AppLoading v-if="loading" />
  <AppError v-else-if="failed" title="RSS 数据加载失败" description="请稍后重试，或检查后端 RSS 服务状态。" />
  <template v-else-if="rssOverview">
    <AppAlert v-if="feedback" variant="success" :title="feedback" />
    <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

    <div class="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
      <div class="space-y-6">
        <AppCard title="我的通用 RSS 地址" description="适合直接接入自动下载器。">
          <div class="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
            {{ rssOverview.generalFeed }}
          </div>
          <template #footer>
            <UiButton variant="primary" @click="copyFeed(rssOverview.generalFeed)">复制通用地址</UiButton>
          </template>
        </AppCard>

        <AppCard title="分类订阅" description="按分类缩小订阅范围。">
          <div class="space-y-3">
            <div
              v-for="feed in rssOverview.categoryFeeds"
              :key="feed.url"
              class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between"
            >
              <div>
                <p class="font-medium text-slate-900">{{ feed.label }}</p>
                <p class="mt-1 break-all text-sm text-slate-500">{{ feed.url }}</p>
              </div>
              <UiButton variant="ghost" size="sm" @click="copyFeed(feed.url)">复制</UiButton>
            </div>
          </div>
        </AppCard>
      </div>

      <div class="space-y-6">
        <AppCard title="标签订阅" description="适合做细粒度追更。">
          <div class="space-y-3">
            <div
              v-for="feed in rssOverview.tagFeeds"
              :key="feed.url"
              class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between"
            >
              <div>
                <p class="font-medium text-slate-900">{{ feed.label }}</p>
                <p class="mt-1 break-all text-sm text-slate-500">{{ feed.url }}</p>
              </div>
              <UiButton variant="ghost" size="sm" @click="copyFeed(feed.url)">复制</UiButton>
            </div>
          </div>
        </AppCard>

        <AppCard title="使用说明" description="地址内含 passkey，泄露后可在“我的账户”中重置。">
          <ul class="space-y-2 text-sm text-slate-600">
            <li>不要把 RSS 地址贴到公共聊天或脚本仓库。</li>
            <li>禁用用户后，RSS 访问应立即失效。</li>
            <li>最近更新：{{ rssOverview.recentReleaseTitles.join('、') }}</li>
          </ul>
        </AppCard>
      </div>
    </div>
  </template>
</template>
