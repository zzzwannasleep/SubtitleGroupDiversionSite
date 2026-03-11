<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, useRoute } from "vue-router";

import { useI18n } from "@/composables/useI18n";
import { useAuthStore } from "@/stores/auth";


const route = useRoute();
const authStore = useAuthStore();
const { t } = useI18n();

const navItems = computed(() => {
  const items = [
    { to: "/torrents", label: t("navigation.torrents") },
    { to: "/rss", label: t("navigation.rss"), auth: true },
    { to: "/upload", label: t("navigation.upload"), roles: ["admin", "uploader"] },
    { to: "/admin", label: t("navigation.admin"), roles: ["admin"] },
  ];

  return items.filter((item) => {
    if (item.auth && !authStore.user) {
      return false;
    }
    if (item.roles && !authStore.user) {
      return false;
    }
    if (item.roles && authStore.user && !item.roles.includes(authStore.user.role)) {
      return false;
    }
    return true;
  });
});
</script>

<template>
  <aside class="hidden w-64 shrink-0 border-r border-slate-200/80 bg-slate-50/85 px-5 py-6 lg:block">
    <RouterLink to="/torrents" class="block rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
      <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ t("navigation.title") }}</p>
      <p class="mt-2 text-lg font-semibold text-slate-900">{{ t("navigation.subtitle") }}</p>
    </RouterLink>

    <nav class="mt-6 space-y-2">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="block rounded-xl px-4 py-3 text-sm font-medium transition"
        :class="
          route.path.startsWith(item.to)
            ? 'bg-blue-600 text-white shadow-sm'
            : 'text-slate-700 hover:bg-white hover:text-slate-900'
        "
      >
        {{ item.label }}
      </RouterLink>
    </nav>
  </aside>
</template>
