<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, useRoute } from 'vue-router';

const route = useRoute();

const navItems = computed(() => [
  { label: '仪表盘', to: '/admin' },
  { label: '用户管理', to: '/admin/users' },
  { label: '资源管理', to: '/admin/releases' },
  { label: '分类管理', to: '/admin/categories' },
  { label: '标签管理', to: '/admin/tags' },
  { label: '公告管理', to: '/admin/announcements' },
  { label: 'XBT 同步', to: '/admin/tracker-sync' },
  { label: '审计日志', to: '/admin/audit-logs' },
  { label: '系统设置', to: '/admin/settings' },
]);

function isActive(path: string) {
  return route.path === path || (path !== '/admin' && route.path.startsWith(path));
}
</script>

<template>
  <aside class="flex h-full flex-col bg-slate-950 text-slate-100">
    <div class="border-b border-slate-800 px-5 py-5">
      <p class="text-sm font-semibold">后台管理</p>
      <p class="mt-1 text-xs text-slate-400">角色与系统控制台</p>
    </div>
    <nav class="flex-1 space-y-1 px-3 py-4">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="[
          'block rounded-md px-3 py-2 text-sm transition',
          isActive(item.to) ? 'bg-slate-800 text-white' : 'text-slate-300 hover:bg-slate-900 hover:text-white',
        ]"
      >
        {{ item.label }}
      </RouterLink>
    </nav>
  </aside>
</template>

