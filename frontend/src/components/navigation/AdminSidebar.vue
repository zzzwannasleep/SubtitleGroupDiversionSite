<script setup lang="ts">
import { computed } from 'vue';
import {
  Blocks,
  FolderOpen,
  KeyRound,
  LayoutDashboard,
  Logs,
  Megaphone,
  RefreshCw,
  Settings,
  Tags,
  Users,
} from 'lucide-vue-next';
import { RouterLink, useRoute } from 'vue-router';
import { useSiteSettingsStore } from '@/stores/siteSettings';
import { buildSiteMonogram } from '@/utils/site-branding';

const route = useRoute();
const siteSettingsStore = useSiteSettingsStore();

const siteSettings = computed(() => siteSettingsStore.settings);
const brandIconUrl = computed(() => siteSettings.value.siteIconResolvedUrl);
const brandMonogram = computed(() => buildSiteMonogram(siteSettings.value.siteName));

const navItems = computed(() => [
  { label: '仪表盘', to: '/admin', icon: LayoutDashboard },
  { label: '邀请码', to: '/admin/invite-codes', icon: KeyRound },
  { label: '用户管理', to: '/admin/users', icon: Users },
  { label: '资源管理', to: '/admin/releases', icon: FolderOpen },
  { label: '分类管理', to: '/admin/categories', icon: Blocks },
  { label: '标签管理', to: '/admin/tags', icon: Tags },
  { label: '公告管理', to: '/admin/announcements', icon: Megaphone },
  { label: 'XBT 同步', to: '/admin/tracker-sync', icon: RefreshCw },
  { label: '审计日志', to: '/admin/audit-logs', icon: Logs },
  { label: '系统设置', to: '/admin/settings', icon: Settings },
]);

function isActive(path: string) {
  return route.path === path || (path !== '/admin' && route.path.startsWith(path));
}
</script>

<template>
  <aside class="flex h-full flex-col bg-slate-950 text-slate-100">
    <div class="border-b border-slate-800 px-5 py-5">
      <div class="flex items-center gap-3">
        <div :class="['admin-sidebar-brand__icon', brandIconUrl ? 'admin-sidebar-brand__icon--plain' : '']">
          <img
            v-if="brandIconUrl"
            :src="brandIconUrl"
            :alt="`${siteSettings.siteName} 图标`"
            class="admin-sidebar-brand__image"
          />
          <span v-else class="admin-sidebar-brand__fallback">{{ brandMonogram }}</span>
        </div>
        <div class="min-w-0">
          <p class="truncate text-sm font-semibold">{{ siteSettings.siteName }}</p>
          <p class="truncate text-xs text-slate-400">管理后台</p>
        </div>
      </div>
      <p class="mt-3 line-clamp-2 text-xs leading-5 text-slate-500">
        {{ siteSettings.siteDescription }}
      </p>
    </div>

    <nav class="flex-1 space-y-1 px-3 py-4">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="[
          'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition',
          isActive(item.to) ? 'bg-slate-800 text-white' : 'text-slate-300 hover:bg-slate-900 hover:text-white',
        ]"
      >
        <component :is="item.icon" class="h-4 w-4" />
        {{ item.label }}
      </RouterLink>
    </nav>
  </aside>
</template>

<style scoped>
.admin-sidebar-brand__icon {
  display: flex;
  height: 2.9rem;
  width: 2.9rem;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  border-radius: 1rem;
  background:
    linear-gradient(145deg, rgba(96, 165, 250, 0.4), rgba(15, 23, 42, 0.92)),
    rgb(15 23 42);
  box-shadow:
    0 12px 26px rgb(2 6 23 / 0.34),
    inset 0 1px 0 rgb(255 255 255 / 0.08);
}

.admin-sidebar-brand__icon--plain {
  background: transparent;
  box-shadow: none;
}

.admin-sidebar-brand__image {
  height: 100%;
  width: 100%;
  object-fit: contain;
}

.admin-sidebar-brand__fallback {
  color: white;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}
</style>
