<script setup lang="ts">
import { storeToRefs } from 'pinia';
import { Menu } from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import AdminSidebar from '@/components/navigation/AdminSidebar.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';

const authStore = useAuthStore();
const uiStore = useUiStore();
const router = useRouter();
const { currentUser } = storeToRefs(authStore);
const { isAdminSidebarOpen } = storeToRefs(uiStore);

async function handleLogout() {
  await authStore.logout();
  await router.push('/login');
}
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
          <div class="flex items-center gap-3">
            <button
              class="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-200 text-slate-700 lg:hidden"
              type="button"
              @click="uiStore.toggleAdminSidebar()"
            >
              <Menu class="h-5 w-5" />
            </button>
            <div>
              <p class="text-sm font-semibold text-slate-900">管理员控制台</p>
              <p class="text-xs text-slate-500">{{ currentUser?.displayName }}</p>
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

