import type { RouteRecordRaw } from 'vue-router';
import AdminLayout from '@/layouts/AdminLayout.vue';
import AuthLayout from '@/layouts/AuthLayout.vue';
import SiteLayout from '@/layouts/SiteLayout.vue';
import LoginView from '@/views/auth/LoginView.vue';
import AdminAnnouncementsView from '@/views/admin/AdminAnnouncementsView.vue';
import AdminAuditLogsView from '@/views/admin/AdminAuditLogsView.vue';
import AdminCategoriesView from '@/views/admin/AdminCategoriesView.vue';
import AdminDashboardView from '@/views/admin/AdminDashboardView.vue';
import AdminReleasesView from '@/views/admin/AdminReleasesView.vue';
import AdminSettingsView from '@/views/admin/AdminSettingsView.vue';
import AdminTagsView from '@/views/admin/AdminTagsView.vue';
import AdminTrackerSyncView from '@/views/admin/AdminTrackerSyncView.vue';
import AdminUserDetailView from '@/views/admin/AdminUserDetailView.vue';
import AdminUsersView from '@/views/admin/AdminUsersView.vue';
import EditMyReleaseView from '@/views/upload/EditMyReleaseView.vue';
import MyReleasesView from '@/views/upload/MyReleasesView.vue';
import UploadView from '@/views/upload/UploadView.vue';
import CategoryView from '@/views/site/CategoryView.vue';
import HomeView from '@/views/site/HomeView.vue';
import MeView from '@/views/site/MeView.vue';
import MyDownloadsView from '@/views/site/MyDownloadsView.vue';
import ReleaseDetailView from '@/views/site/ReleaseDetailView.vue';
import ReleaseListView from '@/views/site/ReleaseListView.vue';
import RssView from '@/views/site/RssView.vue';
import TagView from '@/views/site/TagView.vue';
import ErrorView from '@/views/system/ErrorView.vue';
import ForbiddenView from '@/views/system/ForbiddenView.vue';
import NotFoundView from '@/views/system/NotFoundView.vue';

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    component: AuthLayout,
    children: [{ path: '', name: 'login', component: LoginView, meta: { guestOnly: true, title: '登录' } }],
  },
  {
    path: '/403',
    component: AuthLayout,
    children: [{ path: '', name: 'forbidden', component: ForbiddenView, meta: { title: '无权限' } }],
  },
  {
    path: '/404',
    component: AuthLayout,
    children: [{ path: '', name: 'not-found', component: NotFoundView, meta: { title: '页面不存在' } }],
  },
  {
    path: '/500',
    component: AuthLayout,
    children: [{ path: '', name: 'error', component: ErrorView, meta: { title: '系统错误' } }],
  },
  {
    path: '/',
    component: SiteLayout,
    children: [
      { path: '', name: 'home', component: HomeView, meta: { requiresAuth: true, title: '首页' } },
      { path: 'releases', name: 'release-list', component: ReleaseListView, meta: { requiresAuth: true, title: '资源列表' } },
      { path: 'releases/:id', name: 'release-detail', component: ReleaseDetailView, meta: { requiresAuth: true, title: '资源详情' } },
      { path: 'categories/:slug', name: 'category-detail', component: CategoryView, meta: { requiresAuth: true, title: '分类页' } },
      { path: 'tags/:slug', name: 'tag-detail', component: TagView, meta: { requiresAuth: true, title: '标签页' } },
      { path: 'rss', name: 'rss', component: RssView, meta: { requiresAuth: true, title: 'RSS' } },
      { path: 'me', name: 'me', component: MeView, meta: { requiresAuth: true, title: '我的账户' } },
      { path: 'me/downloads', name: 'my-downloads', component: MyDownloadsView, meta: { requiresAuth: true, title: '我的下载' } },
      { path: 'upload', name: 'upload', component: UploadView, meta: { requiresAuth: true, roles: ['uploader', 'admin'], title: '上传资源' } },
      { path: 'my/releases', name: 'my-releases', component: MyReleasesView, meta: { requiresAuth: true, roles: ['uploader', 'admin'], title: '我的发布' } },
      { path: 'my/releases/:id/edit', name: 'my-release-edit', component: EditMyReleaseView, meta: { requiresAuth: true, roles: ['uploader', 'admin'], title: '编辑资源' } },
    ],
  },
  {
    path: '/admin',
    component: AdminLayout,
    children: [
      { path: '', name: 'admin-dashboard', component: AdminDashboardView, meta: { requiresAuth: true, roles: ['admin'], title: '后台首页' } },
      { path: 'users', name: 'admin-users', component: AdminUsersView, meta: { requiresAuth: true, roles: ['admin'], title: '用户管理' } },
      { path: 'users/:id', name: 'admin-user-detail', component: AdminUserDetailView, meta: { requiresAuth: true, roles: ['admin'], title: '用户详情' } },
      { path: 'releases', name: 'admin-releases', component: AdminReleasesView, meta: { requiresAuth: true, roles: ['admin'], title: '资源管理' } },
      { path: 'categories', name: 'admin-categories', component: AdminCategoriesView, meta: { requiresAuth: true, roles: ['admin'], title: '分类管理' } },
      { path: 'tags', name: 'admin-tags', component: AdminTagsView, meta: { requiresAuth: true, roles: ['admin'], title: '标签管理' } },
      { path: 'announcements', name: 'admin-announcements', component: AdminAnnouncementsView, meta: { requiresAuth: true, roles: ['admin'], title: '公告管理' } },
      { path: 'tracker-sync', name: 'admin-tracker-sync', component: AdminTrackerSyncView, meta: { requiresAuth: true, roles: ['admin'], title: 'XBT 同步' } },
      { path: 'audit-logs', name: 'admin-audit-logs', component: AdminAuditLogsView, meta: { requiresAuth: true, roles: ['admin'], title: '审计日志' } },
      { path: 'settings', name: 'admin-settings', component: AdminSettingsView, meta: { requiresAuth: true, roles: ['admin'], title: '系统设置' } },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
  },
];

