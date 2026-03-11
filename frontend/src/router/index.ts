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
    requiresAuth?: boolean;
    guestOnly?: boolean;
    roles?: Array<"admin" | "uploader" | "user">;
    transition?: string;
  }
}


const routes = [
  {
    path: "/login",
    component: LoginView,
    meta: { title: "Login", guestOnly: true, transition: "page-fade" },
  },
  {
    path: "/register",
    component: RegisterView,
    meta: { title: "Register", guestOnly: true, transition: "page-fade" },
  },
  {
    path: "/",
    component: AppShell,
    children: [
      {
        path: "",
        redirect: "/torrents",
      },
      {
        path: "torrents",
        component: TorrentListView,
        meta: { title: "Torrents", transition: "page-fade" },
      },
      {
        path: "torrents/:id",
        component: TorrentDetailView,
        meta: { title: "Torrent Detail", transition: "page-slide" },
      },
      {
        path: "upload",
        component: UploadTorrentView,
        meta: { title: "Upload", requiresAuth: true, roles: ["admin", "uploader"] },
      },
      {
        path: "profile",
        component: ProfileView,
        meta: { title: "Profile", requiresAuth: true },
      },
      {
        path: "rss",
        component: RssView,
        meta: { title: "RSS", requiresAuth: true },
      },
      {
        path: "admin",
        component: AdminEntryView,
        meta: { title: "Admin", requiresAuth: true, roles: ["admin"] },
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    component: NotFoundView,
    meta: { title: "Not Found" },
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

router.afterEach((to) => {
  document.title = `${to.meta.title ?? "PT Platform"} | PT Platform`;
});

