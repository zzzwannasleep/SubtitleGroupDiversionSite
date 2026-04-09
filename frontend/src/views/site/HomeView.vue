<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import { downloadRelease, getHomeData } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { Category, Release, Tag } from '@/types/release';

const authStore = useAuthStore();

const loading = ref(true);
const failed = ref(false);
const latestReleases = ref<Release[]>([]);
const categories = ref<Category[]>([]);
const tags = ref<Tag[]>([]);

const quickActions = computed(() => [
  { label: '浏览全部资源', to: '/releases', variant: 'primary' as const },
  ...(authStore.currentUser?.role === 'uploader' || authStore.currentUser?.role === 'admin'
    ? [{ label: '上传资源', to: '/upload', variant: 'secondary' as const }]
    : []),
]);

async function loadData() {
  loading.value = true;
  failed.value = false;

  try {
    const data = await getHomeData();
    latestReleases.value = data.latestReleases;
    categories.value = data.categories;
    tags.value = data.tags;
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="首页" description="围绕浏览、下载和订阅设计的前台入口，尽量让高频操作保持短路径。">
    <template #actions>
      <UiButton v-for="item in quickActions" :key="item.to" :to="item.to" :variant="item.variant">
        {{ item.label }}
      </UiButton>
    </template>
  </AppPageHeader>

  <AppLoading v-if="loading" />
  <AppError
    v-else-if="failed"
    title="首页加载失败"
    description="请稍后重试，或检查首页数据接口是否可用。"
  />
  <template v-else>
    <div class="grid gap-6 xl:grid-cols-[2fr_1fr]">
      <AppCard title="最新资源" description="首页直接给出最新发布与进入详情页的快捷入口。">
        <AppEmpty v-if="!latestReleases.length" title="暂无资源" description="资源发布后会出现在这里。" />
        <ReleaseListTable v-else :releases="latestReleases">
          <template #actions="{ release }">
            <UiButton variant="secondary" size="sm" @click="downloadRelease(release.id)">下载</UiButton>
            <UiButton :to="`/releases/${release.id}`" size="sm">查看详情</UiButton>
          </template>
        </ReleaseListTable>
      </AppCard>

      <div class="space-y-6">
        <AppCard title="分类入口" description="优先按分类进入，降低搜索成本。">
          <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <RouterLink
              v-for="category in categories"
              :key="category.slug"
              :to="`/categories/${category.slug}`"
              class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 transition hover:border-blue-200 hover:bg-blue-50"
            >
              <div class="font-medium text-slate-900">{{ category.name }}</div>
              <div class="mt-1 text-xs text-slate-500">分类标识：{{ category.slug }}</div>
            </RouterLink>
          </div>
        </AppCard>

        <AppCard title="标签与 RSS" description="标签页和 RSS 是最常见的追更入口。">
          <div class="flex flex-wrap gap-2">
            <RouterLink
              v-for="tag in tags.slice(0, 6)"
              :key="tag.slug"
              :to="`/tags/${tag.slug}`"
              class="rounded-full bg-slate-100 px-3 py-1.5 text-sm text-slate-700 transition hover:bg-slate-200"
            >
              {{ tag.name }}
            </RouterLink>
          </div>
          <div class="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm leading-7 text-slate-600">
            RSS 页面会把通用地址、分类地址和标签地址集中展示，并保持“一键复制”作为主操作。
          </div>
        </AppCard>
      </div>
    </div>
  </template>
</template>
