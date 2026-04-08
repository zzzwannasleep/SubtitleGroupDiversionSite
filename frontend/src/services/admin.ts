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
import { apiRequest, isApiError } from './api';

export async function getAdminDashboard(): Promise<{
  stats: AdminDashboardStats;
  latestUsers: AdminUser[];
  latestReleases: Release[];
}> {
  return apiRequest('/api/admin/dashboard/');
}

export async function listUsers(query = ''): Promise<AdminUser[]> {
  return apiRequest<AdminUser[]>('/api/admin/users/', {
    query: { q: query.trim() || undefined },
  });
}

export async function getUserDetail(userId: number): Promise<AdminUser | null> {
  try {
    return await apiRequest<AdminUser>(`/api/admin/users/${userId}/`);
  } catch (error) {
    if (isApiError(error) && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function createUser(payload: CreateUserPayload): Promise<AdminUser> {
  return apiRequest<AdminUser>('/api/admin/users/', {
    method: 'POST',
    body: payload,
  });
}

export async function changeUserStatus(payload: ToggleUserStatusPayload): Promise<AdminUser> {
  return apiRequest<AdminUser>(`/api/admin/users/${payload.userId}/status/`, {
    method: 'POST',
    body: { nextStatus: payload.nextStatus },
  });
}

export async function resetUserPasskey(userId: number): Promise<AdminUser> {
  return apiRequest<AdminUser>(`/api/admin/users/${userId}/reset-passkey/`, {
    method: 'POST',
  });
}

export async function listAnnouncements(): Promise<Announcement[]> {
  return apiRequest<Announcement[]>('/api/admin/announcements/');
}

export async function listVisibleAnnouncements(): Promise<Announcement[]> {
  return apiRequest<Announcement[]>('/api/announcements/visible/');
}

export async function saveAnnouncementItem(
  payload: Pick<Announcement, 'title' | 'content' | 'status' | 'audience'> & Partial<Announcement>,
): Promise<Announcement> {
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
  return apiRequest<Category[]>('/api/admin/categories/');
}

export async function saveCategoryItem(payload: Pick<Category, 'name' | 'slug'> & Partial<Category>): Promise<Category> {
  return apiRequest<Category>('/api/admin/categories/', {
    method: 'POST',
    body: payload,
  });
}

export async function listTagsAdmin(): Promise<Tag[]> {
  return apiRequest<Tag[]>('/api/admin/tags/');
}

export async function saveTagItem(payload: Pick<Tag, 'name' | 'slug'> & Partial<Tag>): Promise<Tag> {
  return apiRequest<Tag>('/api/admin/tags/', {
    method: 'POST',
    body: payload,
  });
}

export async function listAuditLogs(): Promise<AuditLog[]> {
  return apiRequest<AuditLog[]>('/api/admin/audit-logs/');
}

export async function getSettings(): Promise<SiteSettings> {
  return apiRequest<SiteSettings>('/api/admin/settings/');
}

export async function saveSiteSettings(payload: SiteSettings): Promise<SiteSettings> {
  return apiRequest<SiteSettings>('/api/admin/settings/', {
    method: 'PUT',
    body: payload,
  });
}
