<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';
import { ArrowRight, FolderKanban, Radio, Sparkles, Upload } from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { useSiteSettingsStore } from '@/stores/siteSettings';

const authStore = useAuthStore();
const siteSettingsStore = useSiteSettingsStore();

const settings = computed(() => siteSettingsStore.settings);
const canManageReleases = computed(
  () => authStore.currentUser?.role === 'uploader' || authStore.currentUser?.role === 'admin',
);

const quickActions = computed(() => [
  {
    label: '浏览全部资源',
    description: '直接进入完整资源列表，按需要再筛选、下载或查看详情。',
    to: '/releases',
    icon: FolderKanban,
  },
  ...(canManageReleases.value
    ? [
        {
          label: '上传种子',
          description: '上传页已经改成极简模式，只传 torrent 就能发布。',
          to: '/upload',
          icon: Upload,
        },
      ]
    : []),
  {
    label: 'RSS 订阅',
    description: '需要自动化下载时，再从独立 RSS 页复制通用或分类地址。',
    to: '/rss',
    icon: Radio,
  },
]);

const workflowTips = [
  {
    title: '首页只保留常用入口',
    description: '把没必要常驻首屏的模块拿掉，减少干扰，进站后可以更快找到真正要点。',
  },
  {
    title: '资源浏览回到列表页处理',
    description: '最新资源、分类入口和标签追更都不再塞在首页，需要时直接去资源列表或对应页面。',
  },
  {
    title: '上传流程只做分流',
    description: '发布页现在只负责上传种子，标题、分类和简介会由系统自动补默认值。',
  },
];
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
          首页现在只保留常用操作入口，避免再堆“最新资源、分类入口、标签与 RSS”这些低价值模块。
        </p>
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

    <section class="home-panel">
      <div class="home-panel__header">
        <div>
          <p class="home-panel__eyebrow">使用说明</p>
          <h2 class="home-panel__title">当前首页逻辑</h2>
          <p class="home-panel__description">常用动作留在首屏，内容浏览和订阅管理分别回到各自页面处理。</p>
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
    grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
    gap: 1.5rem;
    align-items: start;
  }
}
</style>
