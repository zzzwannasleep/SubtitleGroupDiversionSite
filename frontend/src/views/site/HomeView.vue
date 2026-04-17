<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { ArrowRight, FolderKanban, Radio, Sparkles, Upload } from 'lucide-vue-next';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import UiButton from '@/components/ui/UiButton.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import { downloadRelease, getHomeData } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import { useSiteSettingsStore } from '@/stores/siteSettings';
import type { Category, Release, Tag } from '@/types/release';

const authStore = useAuthStore();
const siteSettingsStore = useSiteSettingsStore();

const loading = ref(true);
const failed = ref(false);
const latestReleases = ref<Release[]>([]);
const categories = ref<Category[]>([]);
const tags = ref<Tag[]>([]);

const settings = computed(() => siteSettingsStore.settings);
const canManageReleases = computed(
  () => authStore.currentUser?.role === 'uploader' || authStore.currentUser?.role === 'admin',
);

const quickActions = computed(() => [
  {
    label: '浏览全部资源',
    description: '从资源总览快速进入下载和详情页。',
    to: '/releases',
    icon: FolderKanban,
  },
  ...(canManageReleases.value
    ? [
        {
          label: '上传资源',
          description: '直接上传 torrent 并完成发布。',
          to: '/upload',
          icon: Upload,
        },
      ]
    : []),
  {
    label: 'RSS 订阅',
    description: '追更和自动化下载都从这里开始。',
    to: '/rss',
    icon: Radio,
  },
]);

const overviewItems = computed(() => [
  { label: '最新资源', value: latestReleases.value.length, description: '首页直接浏览最近发布内容' },
  { label: '分类入口', value: categories.value.length, description: '按类型进入，减少搜索成本' },
  { label: '标签与 RSS', value: tags.value.length, description: '追更入口集中整理' },
]);

const workflowTips = computed(() => [
  {
    title: '先浏览，再决定动作',
    description: '从分类、标签或最新资源进入，先看清楚再下载或继续处理。',
  },
  {
    title: '发布流程更直接',
    description: '上传页现在可以直接提交 torrent 文件，不再需要额外处理。',
  },
  {
    title: '高频入口放在首屏',
    description: '把最常用的动作聚在首页，尽量少跳页面。',
  },
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
  <div class="home-view">
    <section class="home-hero">
      <div class="home-hero__copy">
        <p class="home-hero__eyebrow">
          <Sparkles class="h-4 w-4" />
          首页入口
        </p>
        <h1 class="home-hero__title">{{ settings.siteName }}</h1>
        <p class="home-hero__description">
          {{ settings.siteDescription }}
          首页把浏览、下载、上传和订阅入口重新整合到一个更清爽的首屏里。
        </p>

        <div class="home-hero__overview">
          <div v-for="item in overviewItems" :key="item.label" class="home-overview-card">
            <span class="home-overview-card__label">{{ item.label }}</span>
            <strong class="home-overview-card__value">{{ item.value }}</strong>
            <span class="home-overview-card__description">{{ item.description }}</span>
          </div>
        </div>
      </div>

      <div class="home-hero__actions">
        <RouterLink
          v-for="item in quickActions"
          :key="item.to"
          :to="item.to"
          class="home-action-card"
        >
          <div class="home-action-card__icon">
            <component :is="item.icon" class="h-5 w-5" />
          </div>
          <div class="min-w-0">
            <p class="home-action-card__title">{{ item.label }}</p>
            <p class="home-action-card__description">{{ item.description }}</p>
          </div>
          <ArrowRight class="home-action-card__arrow h-4 w-4" />
        </RouterLink>
      </div>
    </section>

    <AppLoading v-if="loading" />
    <AppError
      v-else-if="failed"
      title="首页加载失败"
      description="请稍后重试，或检查首页数据接口是否可用。"
    />
    <template v-else>
      <div class="home-grid">
        <section class="home-panel home-panel--feed">
          <div class="home-panel__header">
            <div>
              <p class="home-panel__eyebrow">最新资源</p>
              <h2 class="home-panel__title">最近发布</h2>
              <p class="home-panel__description">首页先看最新内容，需要更多筛选再进入完整资源列表。</p>
            </div>
            <UiButton to="/releases" variant="secondary" size="sm">资源列表</UiButton>
          </div>

          <div class="home-panel__body">
            <div v-if="!latestReleases.length" class="home-empty">
              <div class="home-empty__icon">
                <FolderKanban class="h-7 w-7" />
              </div>
              <h3 class="home-empty__title">暂时还没有资源</h3>
              <p class="home-empty__description">资源发布后会出现在这里，你也可以先从分类和 RSS 入口整理浏览路径。</p>
              <div class="flex flex-wrap justify-center gap-3">
                <UiButton to="/releases">查看资源列表</UiButton>
                <UiButton v-if="canManageReleases" to="/upload" variant="secondary">去上传资源</UiButton>
              </div>
            </div>

            <ReleaseListTable v-else :releases="latestReleases">
              <template #actions="{ release }">
                <UiButton variant="secondary" size="sm" @click="downloadRelease(release.id)">下载</UiButton>
                <UiButton :to="`/releases/${release.id}`" size="sm">查看详情</UiButton>
              </template>
            </ReleaseListTable>
          </div>
        </section>

        <aside class="home-side">
          <section class="home-panel">
            <div class="home-panel__header home-panel__header--compact">
              <div>
                <p class="home-panel__eyebrow">分类入口</p>
                <h2 class="home-panel__title">按分类进入</h2>
              </div>
            </div>

            <div class="home-category-list">
              <RouterLink
                v-for="category in categories"
                :key="category.slug"
                :to="`/categories/${category.slug}`"
                class="home-category-card"
              >
                <div>
                  <p class="home-category-card__title">{{ category.name }}</p>
                  <p class="home-category-card__meta">分类标识：{{ category.slug }}</p>
                </div>
                <ArrowRight class="h-4 w-4 text-slate-400" />
              </RouterLink>
            </div>
          </section>

          <section class="home-panel">
            <div class="home-panel__header home-panel__header--compact">
              <div>
                <p class="home-panel__eyebrow">标签与 RSS</p>
                <h2 class="home-panel__title">追更入口</h2>
              </div>
            </div>

            <div class="home-tag-cloud">
              <RouterLink
                v-for="tag in tags.slice(0, 8)"
                :key="tag.slug"
                :to="`/tags/${tag.slug}`"
                class="home-tag"
              >
                {{ tag.name }}
              </RouterLink>
            </div>

            <RouterLink to="/rss" class="home-rss-card">
              <div>
                <p class="home-rss-card__title">RSS 订阅入口</p>
                <p class="home-rss-card__description">直接去 RSS 页面整理订阅地址和自动化下载方案。</p>
              </div>
              <ArrowRight class="h-4 w-4" />
            </RouterLink>
          </section>

          <section class="home-panel">
            <div class="home-panel__header home-panel__header--compact">
              <div>
                <p class="home-panel__eyebrow">使用建议</p>
                <h2 class="home-panel__title">首页工作流</h2>
              </div>
            </div>

            <div class="home-workflow">
              <div v-for="(item, index) in workflowTips" :key="item.title" class="home-workflow__item">
                <span class="home-workflow__index">0{{ index + 1 }}</span>
                <div>
                  <p class="home-workflow__title">{{ item.title }}</p>
                  <p class="home-workflow__description">{{ item.description }}</p>
                </div>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped>
.home-view {
  display: grid;
  gap: 1.5rem;
}

.home-hero {
  position: relative;
  overflow: hidden;
  border: 1px solid rgb(226 232 240 / 0.9);
  border-radius: 2rem;
  background:
    radial-gradient(circle at top left, rgb(191 219 254 / 0.75), transparent 34%),
    radial-gradient(circle at 85% 20%, rgb(219 234 254 / 0.92), transparent 28%),
    linear-gradient(135deg, rgb(255 255 255 / 0.96), rgb(248 250 252 / 0.92));
  box-shadow:
    0 24px 60px rgb(148 163 184 / 0.16),
    inset 0 1px 0 rgb(255 255 255 / 0.9);
  padding: 1.6rem;
}

.home-hero__copy,
.home-hero__actions {
  position: relative;
  z-index: 1;
}

.home-hero__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: 999px;
  background: rgb(239 246 255);
  padding: 0.45rem 0.8rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: rgb(29 78 216);
}

.home-hero__title {
  margin-top: 1rem;
  font-size: clamp(2rem, 4vw, 3.3rem);
  line-height: 1.02;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: rgb(15 23 42);
}

.home-hero__description {
  margin-top: 1rem;
  max-width: 46rem;
  font-size: 1rem;
  line-height: 1.9;
  color: rgb(71 85 105);
}

.home-hero__overview {
  margin-top: 1.35rem;
  display: grid;
  gap: 0.9rem;
}

.home-overview-card {
  display: grid;
  gap: 0.2rem;
  border: 1px solid rgb(226 232 240);
  border-radius: 1.35rem;
  background: rgb(255 255 255 / 0.72);
  padding: 1rem 1.05rem;
}

.home-overview-card__label {
  font-size: 0.8rem;
  color: rgb(100 116 139);
}

.home-overview-card__value {
  font-size: 1.65rem;
  font-weight: 700;
  color: rgb(15 23 42);
}

.home-overview-card__description {
  font-size: 0.85rem;
  line-height: 1.7;
  color: rgb(100 116 139);
}

.home-hero__actions {
  margin-top: 1.4rem;
  display: grid;
  gap: 0.9rem;
}

.home-action-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.9rem;
  border: 1px solid rgb(226 232 240);
  border-radius: 1.35rem;
  background: rgb(255 255 255 / 0.78);
  padding: 1rem 1.05rem;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.home-action-card:hover {
  transform: translateY(-2px);
  border-color: rgb(147 197 253);
  box-shadow: 0 14px 28px rgb(148 163 184 / 0.14);
}

.home-action-card__icon {
  display: flex;
  height: 2.7rem;
  width: 2.7rem;
  align-items: center;
  justify-content: center;
  border-radius: 1rem;
  background: linear-gradient(135deg, rgb(59 130 246), rgb(147 197 253));
  color: white;
}

.home-action-card__title {
  font-size: 0.96rem;
  font-weight: 700;
  color: rgb(15 23 42);
}

.home-action-card__description {
  margin-top: 0.2rem;
  font-size: 0.85rem;
  line-height: 1.65;
  color: rgb(100 116 139);
}

.home-action-card__arrow {
  color: rgb(100 116 139);
}

.home-grid {
  display: grid;
  gap: 1.5rem;
}

.home-side {
  display: grid;
  gap: 1.5rem;
}

.home-panel {
  overflow: hidden;
  border: 1px solid rgb(226 232 240 / 0.95);
  border-radius: 1.8rem;
  background: rgb(255 255 255 / 0.88);
  box-shadow: 0 18px 40px rgb(148 163 184 / 0.12);
}

.home-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  border-bottom: 1px solid rgb(241 245 249);
  padding: 1.35rem 1.35rem 1.1rem;
}

.home-panel__header--compact {
  padding-bottom: 1rem;
}

.home-panel__eyebrow {
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: rgb(96 165 250);
  text-transform: uppercase;
}

.home-panel__title {
  margin-top: 0.35rem;
  font-size: 1.45rem;
  font-weight: 700;
  color: rgb(15 23 42);
}

.home-panel__description {
  margin-top: 0.45rem;
  font-size: 0.92rem;
  line-height: 1.75;
  color: rgb(100 116 139);
}

.home-panel__body {
  padding: 1.35rem;
}

.home-empty {
  display: grid;
  justify-items: center;
  gap: 0.9rem;
  border: 1px dashed rgb(203 213 225);
  border-radius: 1.5rem;
  background:
    radial-gradient(circle at top left, rgb(239 246 255), transparent 38%),
    rgb(248 250 252);
  padding: 3rem 1.25rem;
  text-align: center;
}

.home-empty__icon {
  display: flex;
  height: 4rem;
  width: 4rem;
  align-items: center;
  justify-content: center;
  border-radius: 1.3rem;
  background: rgb(239 246 255);
  color: rgb(59 130 246);
}

.home-empty__title {
  font-size: 1.6rem;
  font-weight: 700;
  color: rgb(15 23 42);
}

.home-empty__description {
  max-width: 28rem;
  font-size: 0.95rem;
  line-height: 1.8;
  color: rgb(100 116 139);
}

.home-category-list {
  display: grid;
  gap: 0.85rem;
  padding: 1.1rem 1.35rem 1.35rem;
}

.home-category-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border: 1px solid rgb(226 232 240);
  border-radius: 1.25rem;
  background: linear-gradient(135deg, rgb(248 250 252), rgb(255 255 255));
  padding: 1rem 1.05rem;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    background-color 0.2s ease;
}

.home-category-card:hover {
  transform: translateY(-1px);
  border-color: rgb(147 197 253);
  background: rgb(239 246 255);
}

.home-category-card__title {
  font-size: 1.05rem;
  font-weight: 700;
  color: rgb(15 23 42);
}

.home-category-card__meta {
  margin-top: 0.25rem;
  font-size: 0.82rem;
  color: rgb(100 116 139);
}

.home-tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  padding: 1.1rem 1.35rem 0;
}

.home-tag {
  border-radius: 999px;
  background: rgb(241 245 249);
  padding: 0.55rem 0.9rem;
  font-size: 0.88rem;
  color: rgb(51 65 85);
  transition: background-color 0.2s ease;
}

.home-tag:hover {
  background: rgb(226 232 240);
}

.home-rss-card {
  margin: 1rem 1.35rem 1.35rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border-radius: 1.35rem;
  background: linear-gradient(135deg, rgb(15 23 42), rgb(30 41 59));
  padding: 1rem 1.05rem;
  color: white;
}

.home-rss-card__title {
  font-size: 1rem;
  font-weight: 700;
}

.home-rss-card__description {
  margin-top: 0.3rem;
  font-size: 0.85rem;
  line-height: 1.7;
  color: rgb(226 232 240 / 0.9);
}

.home-workflow {
  display: grid;
  gap: 0.95rem;
  padding: 1.1rem 1.35rem 1.35rem;
}

.home-workflow__item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.9rem;
  align-items: flex-start;
}

.home-workflow__index {
  display: inline-flex;
  height: 2rem;
  width: 2rem;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgb(239 246 255);
  font-size: 0.82rem;
  font-weight: 700;
  color: rgb(37 99 235);
}

.home-workflow__title {
  font-size: 0.98rem;
  font-weight: 700;
  color: rgb(15 23 42);
}

.home-workflow__description {
  margin-top: 0.25rem;
  font-size: 0.85rem;
  line-height: 1.75;
  color: rgb(100 116 139);
}

@media (min-width: 900px) {
  .home-hero {
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.9fr);
    gap: 1.5rem;
    align-items: start;
  }

  .home-hero__overview {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (min-width: 1280px) {
  .home-grid {
    grid-template-columns: minmax(0, 1.8fr) minmax(330px, 0.92fr);
  }
}
</style>
