<script setup lang="ts">
import { computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import { Menu, Shield, Upload, X } from 'lucide-vue-next';
import UiButton from '@/components/ui/UiButton.vue';
import { useAuthStore } from '@/stores/auth';
import { useSiteSettingsStore } from '@/stores/siteSettings';
import { useUiStore } from '@/stores/ui';
import { roleLabels } from '@/utils/labels';
import { buildSiteMonogram } from '@/utils/site-branding';

const authStore = useAuthStore();
const siteSettingsStore = useSiteSettingsStore();
const uiStore = useUiStore();
const route = useRoute();
const router = useRouter();
const { currentUser } = storeToRefs(authStore);
const { isMobileMenuOpen } = storeToRefs(uiStore);

const roleLabel = computed(() => {
  const role = currentUser.value?.role;
  return role ? roleLabels[role] : '';
});

const siteSettings = computed(() => siteSettingsStore.settings);
const brandIconUrl = computed(() => siteSettings.value.siteIconResolvedUrl);
const brandMonogram = computed(() => buildSiteMonogram(siteSettings.value.siteName));

const navItems = computed(() => {
  const items = [
    { label: '首页', to: '/' },
    { label: '资源', to: '/releases' },
    { label: 'RSS', to: '/rss' },
  ];

  if (currentUser.value?.role === 'uploader' || currentUser.value?.role === 'admin') {
    items.push({ label: '上传资源', to: '/upload' });
    items.push({ label: '我的发布', to: '/my/releases' });
  }

  if (currentUser.value?.role === 'admin') {
    items.push({ label: '后台管理', to: '/admin' });
  }

  items.push({ label: '我的账户', to: '/me' });
  items.push({ label: '我的下载', to: '/me/downloads' });

  return items;
});

function isActive(path: string) {
  return route.path === path || (path !== '/' && route.path.startsWith(path));
}

async function handleLogout() {
  await authStore.logout();
  uiStore.closeMobileMenu();
  await router.push('/login');
}

watch(
  () => route.fullPath,
  () => {
    uiStore.closeMobileMenu();
  },
);
</script>

<template>
  <header class="border-b border-slate-200 bg-white">
    <div class="app-container flex h-16 items-center justify-between gap-4">
      <div class="flex min-w-0 items-center gap-3">
        <RouterLink to="/" class="flex min-w-0 items-center gap-3 text-sm font-semibold text-slate-900">
          <div :class="['site-header-brand__icon', brandIconUrl ? 'site-header-brand__icon--plain' : '']">
            <img
              v-if="brandIconUrl"
              :src="brandIconUrl"
              :alt="`${siteSettings.siteName} 图标`"
              class="site-header-brand__image"
            />
            <span v-else class="site-header-brand__fallback">{{ brandMonogram }}</span>
          </div>
          <div class="hidden min-w-0 sm:block">
            <div class="truncate">{{ siteSettings.siteName }}</div>
            <div class="truncate text-xs font-normal text-slate-500">{{ siteSettings.siteDescription }}</div>
          </div>
        </RouterLink>

        <nav class="hidden items-center gap-1 lg:flex">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            :class="[
              'rounded-md px-3 py-2 text-sm transition',
              isActive(item.to) ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
            ]"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
      </div>

      <div class="hidden items-center gap-2 lg:flex">
        <div class="rounded-full bg-slate-100 px-3 py-1.5 text-xs text-slate-600">
          {{ currentUser?.displayName }} / {{ roleLabel }}
        </div>
        <UiButton v-if="currentUser?.role === 'admin'" to="/admin" variant="ghost" size="sm">
          <Shield class="mr-1 h-4 w-4" />
          管理区
        </UiButton>
        <UiButton
          v-if="currentUser?.role === 'uploader' || currentUser?.role === 'admin'"
          to="/upload"
          variant="ghost"
          size="sm"
        >
          <Upload class="mr-1 h-4 w-4" />
          发布
        </UiButton>
        <UiButton variant="secondary" size="sm" @click="handleLogout">退出登录</UiButton>
      </div>

      <button
        class="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-200 text-slate-700 lg:hidden"
        type="button"
        @click="uiStore.toggleMobileMenu()"
      >
        <Menu v-if="!isMobileMenuOpen" class="h-5 w-5" />
        <X v-else class="h-5 w-5" />
      </button>
    </div>

    <div v-if="isMobileMenuOpen" class="border-t border-slate-200 bg-white lg:hidden">
      <div class="app-container space-y-3 py-4">
        <div class="flex items-center gap-3 rounded-xl bg-slate-50 px-4 py-3">
          <div
            :class="[
              'site-header-brand__icon',
              'site-header-brand__icon--mobile',
              brandIconUrl ? 'site-header-brand__icon--plain' : '',
            ]"
          >
            <img
              v-if="brandIconUrl"
              :src="brandIconUrl"
              :alt="`${siteSettings.siteName} 图标`"
              class="site-header-brand__image"
            />
            <span v-else class="site-header-brand__fallback">{{ brandMonogram }}</span>
          </div>
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold text-slate-900">{{ siteSettings.siteName }}</p>
            <p class="truncate text-xs text-slate-500">{{ siteSettings.siteDescription }}</p>
          </div>
        </div>

        <div class="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
          {{ currentUser?.displayName }} / {{ roleLabel }}
        </div>

        <nav class="grid gap-2">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            :class="[
              'rounded-md px-3 py-2 text-sm transition',
              isActive(item.to) ? 'bg-blue-50 text-blue-700' : 'bg-slate-50 text-slate-700',
            ]"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
        <UiButton block variant="secondary" @click="handleLogout">退出登录</UiButton>
      </div>
    </div>
  </header>
</template>

<style scoped>
.site-header-brand__icon {
  display: flex;
  height: 2.5rem;
  width: 2.5rem;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  border-radius: 0.9rem;
  background:
    linear-gradient(145deg, rgba(37, 99, 235, 0.92), rgba(59, 130, 246, 0.74)),
    rgb(37 99 235);
  box-shadow: 0 10px 24px rgb(37 99 235 / 0.18);
}

.site-header-brand__icon--plain {
  background: transparent;
  box-shadow: none;
}

.site-header-brand__icon--mobile {
  height: 2.75rem;
  width: 2.75rem;
}

.site-header-brand__image {
  height: 100%;
  width: 100%;
  object-fit: contain;
}

.site-header-brand__fallback {
  color: white;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}
</style>
