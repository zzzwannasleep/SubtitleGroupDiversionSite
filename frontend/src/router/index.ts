import { createRouter, createWebHistory } from "vue-router";

import AppShell from "@/layouts/AppShell.vue";
import AdminEntryView from "@/views/AdminEntryView.vue";
import LoginView from "@/views/LoginView.vue";
import NotFoundView from "@/views/NotFoundView.vue";
import ProfileView from "@/views/ProfileView.vue";
import RegisterView from "@/views/RegisterView.vue";
import RssView from "@/views/RssView.vue";
import TorrentDetailView from "@/views/TorrentDetailView.vue";
import TorrentListView from "@/views/TorrentListView.vue";
import UploadTorrentView from "@/views/UploadTorrentView.vue";
import { pinia } from "@/stores";
import { useAuthStore } from "@/stores/auth";


declare module "vue-router" {
  interface RouteMeta {
    title?: string;
    titleKey?: string;
    requiresAuth?: boolean;
    guestOnly?: boolean;
    roles?: Array<"admin" | "uploader" | "user">;
    transition?: string;
    previewProfile?: boolean;
  }
}


const routes = [
  {
    path: "/login",
    component: LoginView,
    meta: { titleKey: "routes.login", guestOnly: true, transition: "page-fade" },
  },
  {
    path: "/register",
    component: RegisterView,
    meta: { titleKey: "routes.register", guestOnly: true, transition: "page-fade" },
  },
  {
    path: "/",
    component: AppShell,
    children: [
      {
        path: "",
        redirect: () => {
          const authStore = useAuthStore(pinia);
          authStore.restoreSession();
          return authStore.isAuthenticated ? "/torrents" : "/login";
        },
      },
      {
        path: "torrents",
        component: TorrentListView,
        meta: { titleKey: "routes.torrents", transition: "page-fade" },
      },
      {
        path: "torrents/:id",
        component: TorrentDetailView,
        meta: { titleKey: "routes.torrentDetail", transition: "page-slide" },
      },
      {
        path: "upload",
        component: UploadTorrentView,
        meta: { titleKey: "routes.upload", requiresAuth: true, roles: ["admin", "uploader"] },
      },
      {
        path: "profile",
        component: ProfileView,
        meta: { titleKey: "routes.profile", requiresAuth: true },
      },
      {
        path: "profile-preview",
        component: ProfileView,
        meta: { titleKey: "routes.profilePreview", previewProfile: true, transition: "page-fade" },
      },
      {
        path: "rss",
        component: RssView,
        meta: { titleKey: "routes.rss", requiresAuth: true },
      },
      {
        path: "admin",
        component: AdminEntryView,
        meta: { titleKey: "routes.admin", requiresAuth: true, roles: ["admin"] },
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    component: NotFoundView,
    meta: { titleKey: "routes.notFound" },
  },
];


export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    return { top: 0 };
  },
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore(pinia);
  authStore.restoreSession();

  if (authStore.token && !authStore.user) {
    await authStore.ensureUser();
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return "/torrents";
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return `/login?redirect=${encodeURIComponent(to.fullPath)}`;
  }

  if (to.meta.roles?.length) {
    if (!authStore.user) {
      return "/login";
    }
    if (!to.meta.roles.includes(authStore.user.role)) {
      return "/torrents";
    }
  }

  return true;
});
