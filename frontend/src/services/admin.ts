import type {
  AdminDashboardStats,
  AdminUser,
  Announcement,
  AuditLog,
  CreateUserPayload,
  SiteSettings,
  ToggleUserStatusPayload,
} from '@/types/admin';
import type { Category, Release, Tag } from '@/types/release';
import { mockRequest } from './api';
import {
  announcements,
  appendAuditLog,
  appendTrackerSyncLog,
  auditLogs,
  categories,
  createUserRecord,
  getDashboardStats,
  getUserById,
  releases,
  resetPasskey,
  saveAnnouncement,
  saveCategory,
  saveSettings,
  saveTag,
  siteSettings,
  tags,
  toggleUserStatus,
  users,
} from './mock-data';

export async function getAdminDashboard(): Promise<{
  stats: AdminDashboardStats;
  latestUsers: AdminUser[];
  latestReleases: Release[];
}> {
  return mockRequest(() => ({
    stats: getDashboardStats(),
    latestUsers: users.slice(0, 4),
    latestReleases: releases.slice(0, 4),
  }));
}

export async function listUsers(query = ''): Promise<AdminUser[]> {
  return mockRequest(() => {
    if (!query.trim()) return users;
    const keyword = query.trim().toLowerCase();
    return users.filter((item) =>
      [item.username, item.displayName, item.email, item.role].some((field) => field.toLowerCase().includes(keyword)),
    );
  });
}

export async function getUserDetail(userId: number): Promise<AdminUser | null> {
  return mockRequest(() => getUserById(userId) ?? null);
}

export async function createUser(payload: CreateUserPayload): Promise<AdminUser> {
  return mockRequest(() => {
    const user = createUserRecord(payload);
    appendAuditLog({
      actorName: '站务总控',
      action: '创建用户',
      targetType: '用户',
      targetName: user.username,
      detail: `角色：${user.role}`,
    });
    return user;
  });
}

export async function changeUserStatus(payload: ToggleUserStatusPayload): Promise<AdminUser> {
  return mockRequest(() => {
    const user = toggleUserStatus(payload.userId, payload.nextStatus);
    appendAuditLog({
      actorName: '站务总控',
      action: payload.nextStatus === 'active' ? '启用用户' : '禁用用户',
      targetType: '用户',
      targetName: user.username,
      detail: `状态切换为 ${payload.nextStatus}`,
    });
    appendTrackerSyncLog({
      scope: 'user',
      targetName: user.username,
      status: 'success',
      message: '用户状态已同步到 XBT',
    });
    return user;
  });
}

export async function resetUserPasskey(userId: number): Promise<AdminUser> {
  return mockRequest(() => {
    const user = resetPasskey(userId);
    appendAuditLog({
      actorName: '站务总控',
      action: '重置 passkey',
      targetType: '用户',
      targetName: user.username,
      detail: '管理员手动触发重置。',
    });
    return user;
  });
}

export async function listAnnouncements(): Promise<Announcement[]> {
  return mockRequest(() => announcements);
}

export async function listVisibleAnnouncements(): Promise<Announcement[]> {
  return mockRequest(() => announcements.filter((item) => item.status === 'online'));
}

export async function saveAnnouncementItem(
  payload: Pick<Announcement, 'title' | 'content' | 'status' | 'audience'> & Partial<Announcement>,
): Promise<Announcement> {
  return mockRequest(() => saveAnnouncement(payload));
}

export async function listCategoriesAdmin(): Promise<Category[]> {
  return mockRequest(() => categories);
}

export async function saveCategoryItem(payload: Pick<Category, 'name' | 'slug'> & Partial<Category>): Promise<Category> {
  return mockRequest(() => saveCategory(payload));
}

export async function listTagsAdmin(): Promise<Tag[]> {
  return mockRequest(() => tags);
}

export async function saveTagItem(payload: Pick<Tag, 'name' | 'slug'> & Partial<Tag>): Promise<Tag> {
  return mockRequest(() => saveTag(payload));
}

export async function listAuditLogs(): Promise<AuditLog[]> {
  return mockRequest(() => auditLogs);
}

export async function getSettings(): Promise<SiteSettings> {
  return mockRequest(() => siteSettings);
}

export async function saveSiteSettings(payload: SiteSettings): Promise<SiteSettings> {
  return mockRequest(() => saveSettings(payload));
}
