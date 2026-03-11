<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import { useI18n } from "@/composables/useI18n";
import { useSiteDisplayName } from "@/composables/useSiteDisplayName";
import { useAuthStore } from "@/stores/auth";


const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const { t } = useI18n();
const { siteDisplayName } = useSiteDisplayName();

const currentTitle = computed(() => {
  if (route.meta.titleKey) {
    return t(route.meta.titleKey as string);
  }
  return (route.meta.title as string | undefined) ?? siteDisplayName.value;
});

const mobileNavItems = computed(() => {
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

async function logout(): Promise<void> {
  authStore.logout();
  await router.push("/login");
}
</script>

<template>
  <header class="sticky top-0 z-20 border-b border-slate-200/80 bg-white/85 backdrop-blur">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex min-h-16 items-center justify-between gap-4 py-3">
        <div>
          <p class="text-xs font-semibold tracking-[0.08em] text-slate-500">{{ siteDisplayName }}</p>
          <h1 class="text-lg font-semibold text-slate-900">{{ currentTitle }}</h1>
        </div>
        <div class="flex items-center gap-3">
          <LocaleSwitcher />
          <RouterLink
            to="/upload"
            class="hidden rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-blue-600 hover:text-blue-700 sm:inline-flex"
          >
            {{ t("header.upload") }}
          </RouterLink>
          <RouterLink
            v-if="authStore.user"
            to="/profile"
            class="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            {{ authStore.user.username }}
          </RouterLink>
          <button
            v-if="authStore.user"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:text-slate-900"
            @click="logout"
          >
            {{ t("header.logout") }}
          </button>
          <RouterLink
            v-else
            to="/login"
            class="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            {{ t("header.login") }}
          </RouterLink>
        </div>
      </div>

      <nav class="flex gap-2 overflow-x-auto pb-3 lg:hidden">
        <RouterLink
          v-for="item in mobileNavItems"
          :key="item.to"
          :to="item.to"
          class="whitespace-nowrap rounded-full border px-3 py-2 text-sm font-medium transition"
          :class="
            route.path.startsWith(item.to)
              ? 'border-blue-600 bg-blue-600 text-white'
              : 'border-slate-200 bg-white text-slate-700'
          "
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>
  </header>
</template>
