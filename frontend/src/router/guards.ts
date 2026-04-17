import type { Router } from 'vue-router';
import { pinia } from '@/stores';
import { useAuthStore } from '@/stores/auth';
import { useSiteSettingsStore } from '@/stores/siteSettings';
import { hasRole } from '@/utils/permissions';

export function registerRouterGuards(router: Router) {
  router.beforeEach(async (to) => {
    const authStore = useAuthStore(pinia);

    if (!authStore.isBootstrapped) {
      try {
        await authStore.bootstrap();
      } catch (error) {
        console.error('Auth bootstrap failed during navigation:', error);

        if (to.name !== 'error') {
          return { name: 'error' };
        }
      }
    }

    if (to.meta.guestOnly && authStore.isAuthenticated) {
      return { name: 'release-list' };
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
    const siteSettingsStore = useSiteSettingsStore(pinia);
    siteSettingsStore.syncDocumentTitle(typeof to.meta.title === 'string' ? to.meta.title : undefined);
  });
}
