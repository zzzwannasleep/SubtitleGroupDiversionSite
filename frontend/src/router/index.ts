import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

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


const AppShell = () => import("@/layouts/AppShell.vue");
const AdminEntryView = () => import("@/views/AdminEntryView.vue");
const LoginView = () => import("@/views/LoginView.vue");
const NotFoundView = () => import("@/views/NotFoundView.vue");
const ProfileView = () => import("@/views/ProfileView.vue");
const RegisterView = () => import("@/views/RegisterView.vue");
const RssView = () => import("@/views/RssView.vue");
const TorrentDetailView = () => import("@/views/TorrentDetailView.vue");
const TorrentListView = () => import("@/views/TorrentListView.vue");
const UploadTorrentView = () => import("@/views/UploadTorrentView.vue");


const routes: RouteRecordRaw[] = [
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
