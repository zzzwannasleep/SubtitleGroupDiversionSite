<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ArrowRight, LayoutGrid, RadioTower, Search, ShieldCheck, UploadCloud } from 'lucide-vue-next';
import { RouterLink, useRouter } from 'vue-router';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import { downloadRelease, getHomeData } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { Category, Release, Tag } from '@/types/release';
import { formatBytes } from '@/utils/format';

const authStore = useAuthStore();
const router = useRouter();

const loading = ref(true);
const failed = ref(false);
const latestReleases = ref<Release[]>([]);
const categories = ref<Category[]>([]);
const tags = ref<Tag[]>([]);
const searchKeyword = ref('');

const quickActions = computed(() => [
  { label: '浏览全部资源', to: '/releases', variant: 'primary' as const },
  ...(authStore.currentUser?.role === 'uploader' || authStore.currentUser?.role === 'admin'
    ? [{ label: '上传资源', to: '/upload', variant: 'secondary' as const }]
    : []),
]);

const roleTitle = computed(() => {
  if (authStore.currentUser?.role === 'admin') return '管理员';
  if (authStore.currentUser?.role === 'uploader') return '上传者';
  return '登录用户';
});

const heroStats = computed(() => [
  {
    label: '最新资源',
    value: `${latestReleases.value.length} 条`,
    hint: '首页只保留少量最新条目，避免信息过密。',
  },
  {
    label: '可用分类',
    value: `${categories.value.length} 个`,
    hint: '优先从分类进入，减少重复搜索。',
  },
  {
    label: '资源体量',
    value: formatBytes(latestReleases.value.reduce((sum, item) => sum + item.sizeBytes, 0)),
    hint: '示例统计基于首页展示的最新资源。',
  },
]);

const entryCards = computed(() => {
  const items = [
    {
      title: '资源列表',
      description: '从统一筛选页进入详情和下载，保持最短操作路径。',
      action: '进入列表',
      to: '/releases',
      icon: LayoutGrid,
    },
    {
      title: 'RSS 订阅',
      description: '按通用、分类和标签维度复制地址，直接接入下载器。',
      action: '查看 RSS',
      to: '/rss',
      icon: RadioTower,
    },
  ];

  if (authStore.currentUser?.role === 'uploader' || authStore.currentUser?.role === 'admin') {
    items.unshift({
      title: '上传入口',
      description: '上传页保持字段精简，适合快速发布和保存草稿。',
      action: '开始上传',
      to: '/upload',
      icon: UploadCloud,
    });
  }

  if (authStore.currentUser?.role === 'admin') {
    items.push({
      title: '后台管理',
      description: '前后台共用同一套设计系统，但后台强调管理与操作确认。',
      action: '进入后台',
      to: '/admin',
      icon: ShieldCheck,
    });
  }

  return items;
});

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

async function searchReleases() {
  await router.push({
    name: 'release-list',
    query: {
      q: searchKeyword.value.trim() || undefined,
    },
  });
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
    <section class="app-surface overflow-hidden">
      <div class="grid gap-8 bg-gradient-to-br from-blue-50 via-white to-slate-50 p-6 lg:grid-cols-[1.3fr_0.7fr] lg:p-8">
        <div class="space-y-6">
          <div class="space-y-3">
            <p class="text-sm font-semibold uppercase tracking-[0.22em] text-blue-700">Front Desk</p>
            <div class="space-y-4">
              <h2 class="text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
                在同一个入口完成资源浏览、下载和订阅。
              </h2>
              <p class="max-w-2xl text-sm leading-7 text-slate-600">
                首页只展示最必要的信息：最新资源、分类入口、常用标签和角色相关操作。避免像传统 PT
                站那样信息堆叠过多，也避免把上传者和管理员误导进错误区域。
              </p>
            </div>
          </div>

          <form
            class="grid gap-3 rounded-2xl border border-blue-100 bg-white/90 p-4 shadow-sm sm:grid-cols-[minmax(0,1fr)_auto]"
            @submit.prevent="searchReleases"
          >
            <UiInput v-model="searchKeyword" placeholder="搜索标题、副标题或简介" />
            <UiButton type="submit" variant="primary">
              <Search class="mr-2 h-4 w-4" />
              搜索资源
            </UiButton>
          </form>

          <div class="grid gap-3 sm:grid-cols-3">
            <div
              v-for="item in heroStats"
              :key="item.label"
              class="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm"
            >
              <p class="text-sm text-slate-500">{{ item.label }}</p>
              <p class="mt-3 text-2xl font-semibold text-slate-900">{{ item.value }}</p>
              <p class="mt-2 text-xs leading-6 text-slate-500">{{ item.hint }}</p>
            </div>
          </div>
        </div>

        <div class="space-y-3">
          <div class="rounded-2xl border border-slate-200 bg-slate-900 p-5 text-white shadow-sm">
            <p class="text-sm text-slate-300">当前身份</p>
            <p class="mt-2 text-2xl font-semibold">{{ roleTitle }}</p>
            <p class="mt-3 text-sm leading-7 text-slate-300">
              {{ authStore.currentUser?.displayName }} 已登录，页面导航和操作入口会随角色自动收敛。
            </p>
          </div>

          <div
            v-for="item in entryCards"
            :key="item.to"
            class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-blue-200 hover:shadow-md"
          >
            <div class="flex items-start gap-3">
              <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                <component :is="item.icon" class="h-5 w-5" />
              </div>
              <div class="min-w-0 flex-1">
                <h3 class="text-base font-semibold text-slate-900">{{ item.title }}</h3>
                <p class="mt-2 text-sm leading-6 text-slate-500">{{ item.description }}</p>
                <RouterLink
                  :to="item.to"
                  class="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-blue-700"
                >
                  {{ item.action }}
                  <ArrowRight class="h-4 w-4" />
                </RouterLink>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

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

        <AppCard title="页面原则" description="遵循简单、统一、权限清晰的前台设计。">
          <ul class="space-y-2 text-sm leading-7 text-slate-600">
            <li>只在首屏展示最必要的信息，不把首页做成信息密集型面板。</li>
            <li>上传者入口保留在前台，不和管理员后台混在一起。</li>
            <li>浏览到下载的主路径尽量控制在三次点击以内。</li>
          </ul>
        </AppCard>
      </div>
    </div>
  </template>
</template>
