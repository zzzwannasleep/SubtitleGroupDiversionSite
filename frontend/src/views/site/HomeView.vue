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
import { getHomeData } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { Category, Release, Tag } from '@/types/release';
import { formatBytes } from '@/utils/format';

const authStore = useAuthStore();
const loading = ref(true);
const failed = ref(false);
const latestReleases = ref<Release[]>([]);
const categories = ref<Category[]>([]);
const tags = ref<Tag[]>([]);

const quickActions = computed(() => [
  { label: '全部资源', to: '/releases', variant: 'primary' as const },
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
  <AppPageHeader title="首页" description="按权限展示统一前台布局，聚焦浏览、下载与订阅。">
    <template #actions>
      <UiButton v-for="item in quickActions" :key="item.to" :to="item.to" :variant="item.variant">
        {{ item.label }}
      </UiButton>
    </template>
  </AppPageHeader>

  <AppLoading v-if="loading" />
  <AppError v-else-if="failed" title="首页加载失败" description="请重试或检查 Mock 服务层。" />
  <template v-else>
    <div class="grid gap-6 xl:grid-cols-[2fr_1fr]">
      <AppCard title="最新资源" description="首页直接给出最新发布与快速下载入口。">
        <AppEmpty v-if="!latestReleases.length" title="暂无资源" description="资源发布后会出现在这里。" />
        <ReleaseListTable v-else :releases="latestReleases">
          <template #actions="{ release }">
            <UiButton :to="`/releases/${release.id}`" size="sm">查看</UiButton>
          </template>
        </ReleaseListTable>
      </AppCard>

      <div class="space-y-6">
        <AppCard title="分类入口" description="快捷进入分类页，减少搜索成本。">
          <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <RouterLink
              v-for="category in categories"
              :key="category.slug"
              :to="`/categories/${category.slug}`"
              class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 transition hover:border-blue-200 hover:bg-blue-50"
            >
              <div class="font-medium text-slate-900">{{ category.name }}</div>
              <div class="mt-1 text-xs text-slate-500">{{ category.slug }}</div>
            </RouterLink>
          </div>
        </AppCard>

        <AppCard title="标签与 RSS" description="标签页和 RSS 是用户最常用的追更入口。">
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
          <div class="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            首页资源条目只保留核心字段：分类、标签、大小、发布时间、发布者和下载入口。
            <div class="mt-3 text-slate-900">推荐首页列表总量控制在 5 条左右，避免信息过密。</div>
          </div>
        </AppCard>

        <AppCard title="当前站点风格" description="浅色主题、白色卡片、低复杂度操作流。">
          <ul class="space-y-2 text-sm text-slate-600">
            <li>统一容器：白色卡片 + 浅灰背景</li>
            <li>统一权限：路由守卫 + 组件按钮控制</li>
            <li>示例资源总容量：{{ formatBytes(latestReleases.reduce((sum, item) => sum + item.sizeBytes, 0)) }}</li>
          </ul>
        </AppCard>
      </div>
    </div>
  </template>
</template>

