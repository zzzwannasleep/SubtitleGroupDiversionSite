import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router';
import { registerRouterGuards } from './guards';
import { routes } from './routes';

const history =
  window.location.protocol === 'file:' ? createWebHashHistory() : createWebHistory();

const router = createRouter({
  history,
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

registerRouterGuards(router);

router.onError((error, to) => {
  console.error('Router navigation failed:', error);

  if (to.name !== 'error') {
    void router.replace({ name: 'error' }).catch((redirectError) => {
      console.error('Failed to redirect to error page:', redirectError);
    });
  }
});

export default router;
