import type {
  AdminDashboardStats,
  AdminUser,
  Announcement,
  AuditLog,
  CreateInviteCodesPayload,
  CreateUserPayload,
  InviteCode,
  SaveSiteSettingsPayload,
  SiteSettings,
  ToggleUserStatusPayload,
  UpdateUserPayload,
} from '@/types/admin';
import type { CurrentUser, UserRole, UserStatus } from '@/types/auth';
import type { Category, Release, Tag } from '@/types/release';
import { apiRequest, isApiError } from './api';
import {
  announcements,
  appendAuditLog,
  appendTrackerSyncLog,
  auditLogs,
  categories,
  createInviteCodeRecords,
  createUserRecord,
  getDashboardStats,
  inviteCodes,
  getUserById,
  releases,
  revokeInviteCodeRecord,
  resetPasskey,
  saveAnnouncement,
  saveCategory,
  saveSettings,
  saveTag,
  siteSettings,
  tags,
  toggleUserStatus,
  updateUserRecord,
  users,
} from './mock-data';
import { mockResolve, useMockApi } from './runtime';

interface ListUsersOptions {
  keyword?: string;
  role?: UserRole;
  status?: UserStatus;
}

export async function getAdminDashboard(): Promise<{
  stats: AdminDashboardStats;
  latestUsers: AdminUser[];
  latestReleases: Release[];
}> {
  if (useMockApi()) {
    return mockResolve(() => ({
      stats: getDashboardStats(),
      latestUsers: users.slice(0, 4),
      latestReleases: releases.slice(0, 4),
    }));
  }

  return apiRequest('/api/admin/dashboard/');
}

export async function listUsers(filters: ListUsersOptions | string = {}): Promise<AdminUser[]> {
  const normalized =
    typeof filters === 'string'
      ? { keyword: filters }
      : filters;

  if (useMockApi()) {
    return mockResolve(() => {
      const keyword = normalized.keyword?.trim().toLowerCase() ?? '';

      return users.filter((item) =>
        (!keyword ||
          [item.username, item.displayName, item.email, item.role].some((field) =>
            field.toLowerCase().includes(keyword),
          )) &&
        (!normalized.role || item.role === normalized.role) &&
        (!normalized.status || item.status === normalized.status),
      );
    });
  }

  return apiRequest<AdminUser[]>('/api/admin/users/', {
    query: {
      q: normalized.keyword?.trim() || undefined,
      role: normalized.role,
      status: normalized.status,
    },
  });
}

export async function getUserDetail(userId: number): Promise<AdminUser | null> {
  if (useMockApi()) {
    return mockResolve(() => getUserById(userId) ?? null);
  }

  try {
    return await apiRequest<AdminUser>(`/api/admin/users/${userId}/`);
  } catch (error) {
    if (isApiError(error) && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function updateUser(
  userId: number,
  payload: Partial<UpdateUserPayload>,
  method: 'PUT' | 'PATCH' = 'PATCH',
): Promise<AdminUser> {
  if (useMockApi()) {
    return mockResolve(() => {
      const user = updateUserRecord(userId, payload);
      appendAuditLog({
        actorName: '站务总控',
        action: '更新用户',
        targetType: '用户',
        targetName: user.username,
        detail: `已更新字段：${Object.keys(payload).join('、') || '基础资料'}`,
      });
      return user;
    });
  }

  return apiRequest<AdminUser>(`/api/admin/users/${userId}/`, {
    method,
    body: payload,
  });
}

export async function createUser(payload: CreateUserPayload): Promise<AdminUser> {
  if (useMockApi()) {
    return mockResolve(() => {
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

  return apiRequest<AdminUser>('/api/admin/users/', {
    method: 'POST',
    body: payload,
  });
}

export async function changeUserStatus(payload: ToggleUserStatusPayload): Promise<AdminUser> {
  if (useMockApi()) {
    return mockResolve(() => {
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
        userId: user.id,
        releaseId: null,
      });
      return user;
    });
  }

  return apiRequest<AdminUser>(`/api/admin/users/${payload.userId}/status/`, {
    method: 'POST',
    body: { nextStatus: payload.nextStatus },
  });
}

export async function resetUserPasskey(userId: number): Promise<AdminUser> {
  if (useMockApi()) {
    return mockResolve(() => {
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

  return apiRequest<AdminUser>(`/api/admin/users/${userId}/reset-passkey/`, {
    method: 'POST',
  });
}

export async function listInviteCodes(): Promise<InviteCode[]> {
  if (useMockApi()) {
    return mockResolve(() => inviteCodes.map((item) => ({ ...item })));
  }

  return apiRequest<InviteCode[]>('/api/admin/invite-codes/');
}

export async function createInviteCodes(payload: CreateInviteCodesPayload): Promise<InviteCode[]> {
  if (useMockApi()) {
    return mockResolve(() => {
      const created = createInviteCodeRecords(payload);
      appendAuditLog({
        actorName: '站务总控',
        action: '生成邀请码',
        targetType: '邀请码',
        targetName: `${created.length} 个邀请码`,
        detail: payload.note?.trim() ? `备注：${payload.note.trim()}` : '未填写备注',
      });
      return created;
    });
  }

  return apiRequest<InviteCode[]>('/api/admin/invite-codes/', {
    method: 'POST',
    body: payload,
  });
}

export async function revokeInviteCode(inviteCodeId: number): Promise<InviteCode> {
  if (useMockApi()) {
    return mockResolve(() => {
      const inviteCode = revokeInviteCodeRecord(inviteCodeId);
      appendAuditLog({
        actorName: '站务总控',
        action: '停用邀请码',
        targetType: '邀请码',
        targetName: inviteCode.code,
        detail: '管理员在后台手动停用了该邀请码。',
      });
      return inviteCode;
    });
  }

  return apiRequest<InviteCode>(`/api/admin/invite-codes/${inviteCodeId}/revoke/`, {
    method: 'POST',
  });
}

export async function listAnnouncements(): Promise<Announcement[]> {
  if (useMockApi()) {
    return mockResolve(() => announcements);
  }

  return apiRequest<Announcement[]>('/api/admin/announcements/');
}

export async function listVisibleAnnouncements(user?: CurrentUser | null): Promise<Announcement[]> {
  if (useMockApi()) {
    return mockResolve(() =>
      announcements.filter((item) => {
        if (item.status !== 'online') return false;
        if (item.audience === 'all') return true;
        if (!user) return false;
        if (user.role === 'admin') return true;
        return item.audience === user.role;
      }),
    );
  }

  return apiRequest<Announcement[]>('/api/announcements/visible/', {
    query: user ? { role: user.role } : undefined,
  });
}

export async function saveAnnouncementItem(
  payload: Pick<Announcement, 'title' | 'content' | 'status' | 'audience'> & Partial<Announcement>,
): Promise<Announcement> {
  if (useMockApi()) {
    return mockResolve(() => saveAnnouncement(payload));
  }

  return apiRequest<Announcement>('/api/admin/announcements/', {
    method: 'POST',
    body: {
      title: payload.title,
      content: payload.content,
      status: payload.status,
      audience: payload.audience,
    },
  });
}

export async function listCategoriesAdmin(): Promise<Category[]> {
  if (useMockApi()) {
    return mockResolve(() => categories);
  }

  return apiRequest<Category[]>('/api/admin/categories/');
}

export async function saveCategoryItem(payload: Pick<Category, 'name' | 'slug'> & Partial<Category>): Promise<Category> {
  if (useMockApi()) {
    return mockResolve(() => saveCategory(payload));
  }

  return apiRequest<Category>('/api/admin/categories/', {
    method: 'POST',
    body: payload,
  });
}

export async function listTagsAdmin(): Promise<Tag[]> {
  if (useMockApi()) {
    return mockResolve(() => tags);
  }

  return apiRequest<Tag[]>('/api/admin/tags/');
}

export async function saveTagItem(payload: Pick<Tag, 'name' | 'slug'> & Partial<Tag>): Promise<Tag> {
  if (useMockApi()) {
    return mockResolve(() => saveTag(payload));
  }

  return apiRequest<Tag>('/api/admin/tags/', {
    method: 'POST',
    body: payload,
  });
}

export async function listAuditLogs(): Promise<AuditLog[]> {
  if (useMockApi()) {
    return mockResolve(() => auditLogs);
  }

  return apiRequest<AuditLog[]>('/api/admin/audit-logs/');
}

export async function getSettings(): Promise<SiteSettings> {
  if (useMockApi()) {
    return mockResolve(() => siteSettings);
  }

  return apiRequest<SiteSettings>('/api/admin/settings/');
}

export async function getPublicSiteSettings(): Promise<SiteSettings> {
  if (useMockApi()) {
    return mockResolve(() => siteSettings);
  }

  return apiRequest<SiteSettings>('/api/site-settings/');
}

export async function saveSiteSettings(payload: SaveSiteSettingsPayload): Promise<SiteSettings> {
  if (useMockApi()) {
    return mockResolve(() => saveSettings(payload));
  }

  const formData = new FormData();
  formData.append('siteName', payload.siteName);
  formData.append('siteDescription', payload.siteDescription);
  formData.append('loginNotice', payload.loginNotice);
  formData.append('allowPublicRegistration', String(payload.allowPublicRegistration));
  formData.append('rssBasePath', payload.rssBasePath);
  formData.append('downloadNotice', payload.downloadNotice);
  formData.append('siteIconUrl', payload.siteIconUrl);
  formData.append('loginBackgroundType', payload.loginBackgroundType);
  formData.append('loginBackgroundApiUrl', payload.loginBackgroundApiUrl);
  formData.append('loginBackgroundCss', payload.loginBackgroundCss);

  if (payload.siteIconFile) {
    formData.append('siteIconFile', payload.siteIconFile);
  }

  if (payload.loginBackgroundFile) {
    formData.append('loginBackgroundFile', payload.loginBackgroundFile);
  }

  if (payload.clearSiteIconFile) {
    formData.append('clearSiteIconFile', 'true');
  }

  if (payload.clearLoginBackgroundFile) {
    formData.append('clearLoginBackgroundFile', 'true');
  }

  return apiRequest<SiteSettings>('/api/admin/settings/', {
    method: 'PUT',
    body: formData,
  });
}
