<script setup lang="ts">
import { computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { Menu } from 'lucide-vue-next';
import { useRoute, useRouter } from 'vue-router';
import AdminSidebar from '@/components/navigation/AdminSidebar.vue';
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
const { isAdminSidebarOpen } = storeToRefs(uiStore);

const siteSettings = computed(() => siteSettingsStore.settings);
const brandIconUrl = computed(() => siteSettings.value.siteIconResolvedUrl);
const brandMonogram = computed(() => buildSiteMonogram(siteSettings.value.siteName));

async function handleLogout() {
  await authStore.logout();
  await router.push('/login');
}

watch(
  () => route.fullPath,
  () => {
    uiStore.closeAdminSidebar();
  },
);
</script>

<template>
  <div class="min-h-screen bg-slate-100 lg:grid lg:grid-cols-[272px_1fr]">
    <div class="hidden lg:block">
      <AdminSidebar />
    </div>

    <div
      v-if="isAdminSidebarOpen"
      class="fixed inset-0 z-40 bg-slate-950/30 lg:hidden"
      @click="uiStore.closeAdminSidebar()"
    />
    <div
      :class="[
        'fixed inset-y-0 left-0 z-50 w-72 -translate-x-full transition-transform lg:hidden',
        isAdminSidebarOpen ? 'translate-x-0' : '',
      ]"
    >
      <AdminSidebar />
    </div>

    <div class="min-w-0">
      <header class="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div class="flex h-16 items-center justify-between gap-3 px-4 md:px-6">
          <div class="flex min-w-0 items-center gap-3">
            <button
              class="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-200 text-slate-700 lg:hidden"
              type="button"
              @click="uiStore.toggleAdminSidebar()"
            >
              <Menu class="h-5 w-5" />
            </button>

            <div :class="['admin-layout-brand__icon', brandIconUrl ? 'admin-layout-brand__icon--plain' : '']">
              <img
                v-if="brandIconUrl"
                :src="brandIconUrl"
                :alt="`${siteSettings.siteName} 图标`"
                class="admin-layout-brand__image"
              />
              <span v-else class="admin-layout-brand__fallback">{{ brandMonogram }}</span>
            </div>

            <div class="min-w-0">
              <p class="truncate text-sm font-semibold text-slate-900">
                {{ siteSettings.siteName }} / 管理后台
              </p>
              <p class="truncate text-xs text-slate-500">
                {{ currentUser?.displayName }} / {{ currentUser?.role ? roleLabels[currentUser.role] : '' }}
              </p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <UiButton to="/" variant="ghost" size="sm">返回前台</UiButton>
            <UiButton variant="secondary" size="sm" @click="handleLogout">退出登录</UiButton>
          </div>
        </div>
      </header>

      <main class="p-4 md:p-6">
        <div class="space-y-6">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout-brand__icon {
  display: flex;
  height: 2.5rem;
  width: 2.5rem;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  border-radius: 0.95rem;
  background:
    linear-gradient(145deg, rgba(37, 99, 235, 0.92), rgba(59, 130, 246, 0.74)),
    rgb(37 99 235);
  box-shadow: 0 10px 24px rgb(37 99 235 / 0.18);
}

.admin-layout-brand__icon--plain {
  background: transparent;
  box-shadow: none;
}

.admin-layout-brand__image {
  height: 100%;
  width: 100%;
  object-fit: contain;
}

.admin-layout-brand__fallback {
  color: white;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}
</style>
