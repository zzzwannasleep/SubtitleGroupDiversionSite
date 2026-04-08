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

export default router;
