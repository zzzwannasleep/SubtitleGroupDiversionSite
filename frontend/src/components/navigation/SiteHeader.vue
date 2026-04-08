<script setup lang="ts">
import { computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import { Menu, Shield, Upload, X } from 'lucide-vue-next';
import UiButton from '@/components/ui/UiButton.vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';

const authStore = useAuthStore();
const uiStore = useUiStore();
const route = useRoute();
const router = useRouter();
const { currentUser } = storeToRefs(authStore);
const { isMobileMenuOpen } = storeToRefs(uiStore);

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
      <div class="flex items-center gap-3">
        <RouterLink to="/" class="flex items-center gap-3 text-sm font-semibold text-slate-900">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white">SG</div>
          <div class="hidden sm:block">
            <div>字幕组分流站</div>
            <div class="text-xs font-normal text-slate-500">内部资源与订阅入口</div>
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
          {{ currentUser?.displayName }} / {{ currentUser?.role }}
        </div>
        <UiButton v-if="currentUser?.role === 'admin'" to="/admin" variant="ghost" size="sm">
          <Shield class="mr-1 h-4 w-4" />
          管理区
        </UiButton>
        <UiButton v-if="currentUser?.role === 'uploader' || currentUser?.role === 'admin'" to="/upload" variant="ghost" size="sm">
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
      <div class="app-container space-y-2 py-4">
        <div class="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
          {{ currentUser?.displayName }} / {{ currentUser?.role }}
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

