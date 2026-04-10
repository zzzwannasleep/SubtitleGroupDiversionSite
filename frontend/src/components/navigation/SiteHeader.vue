<script setup lang="ts">
import { computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import { LogOut, Menu, X } from 'lucide-vue-next';
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

const canManageReleases = computed(
  () => currentUser.value?.role === 'uploader' || currentUser.value?.role === 'admin',
);

const siteSettings = computed(() => siteSettingsStore.settings);
const brandIconUrl = computed(() => siteSettings.value.siteIconResolvedUrl);
const brandMonogram = computed(() => buildSiteMonogram(siteSettings.value.siteName));

const navItems = computed(() => {
  const items = [
    { label: '首页', to: '/' },
    { label: '资源', to: '/releases' },
    { label: 'RSS', to: '/rss' },
  ];

  if (canManageReleases.value) {
    items.push({ label: '改种工具', to: '/torrent-tool' });
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
  <header class="site-header">
    <div class="site-header__container">
      <div class="site-header__top">
        <RouterLink to="/" class="site-header__brand">
          <div :class="['site-header__brand-icon', brandIconUrl ? 'site-header__brand-icon--plain' : '']">
            <img
              v-if="brandIconUrl"
              :src="brandIconUrl"
              :alt="`${siteSettings.siteName} 图标`"
              class="site-header__brand-image"
            />
            <span v-else class="site-header__brand-fallback">{{ brandMonogram }}</span>
          </div>
          <div class="site-header__brand-copy">
            <p class="site-header__brand-title">{{ siteSettings.siteName }}</p>
            <p class="site-header__brand-subtitle">{{ siteSettings.siteDescription }}</p>
          </div>
        </RouterLink>

        <div class="site-header__top-actions">
          <RouterLink to="/me" class="site-header__account">
            <span class="site-header__account-name">{{ currentUser?.displayName }}</span>
            <span class="site-header__account-role">{{ roleLabel }}</span>
          </RouterLink>
          <UiButton variant="ghost" size="sm" @click="handleLogout">
            <LogOut class="mr-1 h-4 w-4" />
            <span class="whitespace-nowrap">退出登录</span>
          </UiButton>
          <button
            class="site-header__menu-button"
            type="button"
            aria-label="切换导航菜单"
            @click="uiStore.toggleMobileMenu()"
          >
            <Menu v-if="!isMobileMenuOpen" class="h-5 w-5" />
            <X v-else class="h-5 w-5" />
          </button>
        </div>
      </div>

      <nav class="site-header__desktop-nav" aria-label="主导航">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="['site-header__nav-item', isActive(item.to) ? 'site-header__nav-item--active' : '']"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>

    <div v-if="isMobileMenuOpen" class="site-header__mobile-shell">
      <div class="site-header__container site-header__mobile-panel">
        <div class="site-header__mobile-account">
          <div :class="['site-header__brand-icon', 'site-header__brand-icon--mobile', brandIconUrl ? 'site-header__brand-icon--plain' : '']">
            <img
              v-if="brandIconUrl"
              :src="brandIconUrl"
              :alt="`${siteSettings.siteName} 图标`"
              class="site-header__brand-image"
            />
            <span v-else class="site-header__brand-fallback">{{ brandMonogram }}</span>
          </div>
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold text-slate-900">{{ currentUser?.displayName }}</p>
            <p class="truncate text-xs text-slate-500">{{ roleLabel }}</p>
          </div>
        </div>

        <nav class="grid gap-2" aria-label="移动端导航">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            :class="['site-header__mobile-link', isActive(item.to) ? 'site-header__mobile-link--active' : '']"
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
.site-header {
  position: relative;
  z-index: 10;
  border-bottom: 1px solid rgb(226 232 240 / 0.92);
  background: rgb(255 255 255 / 0.92);
  backdrop-filter: blur(18px);
}

.site-header__container {
  width: min(100%, 96rem);
  margin: 0 auto;
  padding-left: clamp(1rem, 2vw, 1.75rem);
  padding-right: clamp(1rem, 2vw, 1.75rem);
}

.site-header__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 0.9rem;
  padding-bottom: 0.85rem;
}

.site-header__brand {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 0.95rem;
}

.site-header__brand-icon {
  display: flex;
  height: 3.05rem;
  width: 3.05rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 1rem;
  background:
    linear-gradient(145deg, rgba(37, 99, 235, 0.94), rgba(96, 165, 250, 0.78)),
    rgb(37 99 235);
  box-shadow:
    0 12px 28px rgb(37 99 235 / 0.18),
    inset 0 1px 0 rgb(255 255 255 / 0.12);
}

.site-header__brand-icon--plain {
  background: transparent;
  box-shadow: none;
}

.site-header__brand-icon--mobile {
  height: 2.75rem;
  width: 2.75rem;
}

.site-header__brand-image {
  height: 100%;
  width: 100%;
  object-fit: contain;
}

.site-header__brand-fallback {
  color: white;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.site-header__brand-copy {
  min-width: 0;
}

.site-header__brand-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 1rem;
  font-weight: 700;
  color: rgb(15 23 42);
}

.site-header__brand-subtitle {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.82rem;
  color: rgb(100 116 139);
}

.site-header__top-actions {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 0.75rem;
}

.site-header__account {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  white-space: nowrap;
  border-radius: 999px;
  border: 1px solid rgb(226 232 240);
  background: rgb(248 250 252 / 0.92);
  padding: 0.52rem 0.9rem;
  color: rgb(51 65 85);
}

.site-header__account-name {
  font-size: 0.88rem;
  font-weight: 600;
}

.site-header__account-role {
  border-left: 1px solid rgb(203 213 225);
  padding-left: 0.55rem;
  font-size: 0.78rem;
  color: rgb(100 116 139);
}

.site-header__menu-button {
  display: none;
  height: 2.75rem;
  width: 2.75rem;
  align-items: center;
  justify-content: center;
  border-radius: 0.9rem;
  border: 1px solid rgb(226 232 240);
  background: rgb(255 255 255 / 0.9);
  color: rgb(51 65 85);
}

.site-header__desktop-nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.55rem;
  border-top: 1px solid rgb(241 245 249);
  padding-top: 0.8rem;
  padding-bottom: 0.95rem;
}

.site-header__nav-item {
  white-space: nowrap;
  border-radius: 999px;
  padding: 0.66rem 1rem;
  font-size: 0.92rem;
  color: rgb(71 85 105);
  transition:
    background-color 0.2s ease,
    color 0.2s ease,
    box-shadow 0.2s ease;
}

.site-header__nav-item:hover {
  background: rgb(241 245 249);
  color: rgb(15 23 42);
}

.site-header__nav-item--active {
  background: linear-gradient(135deg, rgb(37 99 235), rgb(96 165 250));
  color: white;
  box-shadow: 0 10px 24px rgb(37 99 235 / 0.18);
}

.site-header__mobile-shell {
  display: none;
  border-top: 1px solid rgb(226 232 240);
  background: rgb(255 255 255 / 0.94);
}

.site-header__mobile-panel {
  display: grid;
  gap: 1rem;
  padding-top: 1rem;
  padding-bottom: 1rem;
}

.site-header__mobile-account {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  border-radius: 1.1rem;
  background: rgb(248 250 252);
  padding: 0.9rem;
}

.site-header__mobile-link {
  border-radius: 0.95rem;
  background: rgb(248 250 252);
  padding: 0.85rem 0.95rem;
  font-size: 0.92rem;
  color: rgb(51 65 85);
}

.site-header__mobile-link--active {
  background: rgb(239 246 255);
  color: rgb(29 78 216);
}

@media (max-width: 1180px) {
  .site-header__menu-button {
    display: inline-flex;
  }

  .site-header__desktop-nav {
    display: none;
  }

  .site-header__mobile-shell {
    display: block;
  }
}

@media (max-width: 760px) {
  .site-header__account {
    display: none;
  }
}

@media (max-width: 639px) {
  .site-header__brand-subtitle {
    display: none;
  }
}
</style>
