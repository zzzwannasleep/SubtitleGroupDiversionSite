import type { Router } from 'vue-router';
import { pinia } from '@/stores';
import { useAuthStore } from '@/stores/auth';
import { hasRole } from '@/utils/permissions';

export function registerRouterGuards(router: Router) {
  router.beforeEach(async (to) => {
    const authStore = useAuthStore(pinia);

    if (!authStore.isBootstrapped) {
      await authStore.bootstrap();
    }

    if (to.meta.guestOnly && authStore.isAuthenticated) {
      return { name: 'home' };
    }

    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      return {
        name: 'login',
        query: { redirect: to.fullPath },
      };
    }

    if (to.meta.roles && !hasRole(authStore.currentUser, to.meta.roles)) {
      return { name: 'forbidden' };
    }

    return true;
  });

  router.afterEach((to) => {
    const title = to.meta.title ? `${to.meta.title} | 字幕组分流站` : '字幕组分流站';
    document.title = title;
  });
}

