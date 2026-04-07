import type { PaginatedResponse, UserRole, UserStatus } from "@/types";
import type { SiteSettings } from "@/api/site";

import { apiRequest } from "./http";


export interface AdminUserItem {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
}


export interface AdminUserUpdatePayload {
  role?: UserRole;
  status?: UserStatus;
}


export interface AdminCategoryItem {
  id: number;
  name: string;
  slug: string;
  sort_order: number;
  is_enabled: boolean;
  created_at: string;
}


export interface AdminCategoryPayload {
  name: string;
  slug: string;
  sort_order: number;
  is_enabled: boolean;
}


export interface AdminTorrentItem {
  id: number;
  name: string;
  category_id: number;
  category: string;
  owner: string;
  info_hash: string;
  is_visible: boolean;
  is_free: boolean;
  created_at: string;
}


export interface AdminTorrentListParams {
  keyword?: string;
  category_id?: number;
  is_visible?: boolean;
  page?: number;
  page_size?: number;
}


export interface AdminTorrentUpdatePayload {
  category_id?: number;
  is_visible?: boolean;
  is_free?: boolean;
}


export interface AdminTrackerSyncResult {
  user_stats_updated: number;
  torrent_stats_updated: number;
  skipped: boolean;
  message: string;
}


export interface AdminAuditLogActor {
  id: number;
  username: string;
}


export interface AdminAuditLogItem {
  id: number;
  actor_id: number | null;
  actor: AdminAuditLogActor | null;
  action: string;
  target_type: string;
  target_id: number | null;
  details: Record<string, unknown> | null;
  ip: string | null;
  created_at: string;
}


export function listAdminUsers(): Promise<PaginatedResponse<AdminUserItem>> {
  return apiRequest<PaginatedResponse<AdminUserItem>>("/admin/users?page_size=50");
}


export function updateAdminUser(userId: number, payload: AdminUserUpdatePayload): Promise<AdminUserItem> {
  return apiRequest<AdminUserItem>(`/admin/users/${userId}`, {
    method: "PATCH",
    body: payload,
  });
}


export function listAdminCategories(): Promise<AdminCategoryItem[]> {
  return apiRequest<AdminCategoryItem[]>("/admin/categories");
}


export function createAdminCategory(payload: AdminCategoryPayload): Promise<AdminCategoryItem> {
  return apiRequest<AdminCategoryItem>("/admin/categories", {
    method: "POST",
    body: payload,
  });
}


export function updateAdminCategory(
  categoryId: number,
  payload: Partial<AdminCategoryPayload>,
): Promise<AdminCategoryItem> {
  return apiRequest<AdminCategoryItem>(`/admin/categories/${categoryId}`, {
    method: "PATCH",
    body: payload,
  });
}


export function listAdminTorrents(params: AdminTorrentListParams = {}): Promise<PaginatedResponse<AdminTorrentItem>> {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("page_size", String(params.page_size ?? 20));
  if (params.keyword) {
    query.set("keyword", params.keyword);
  }
  if (params.category_id) {
    query.set("category_id", String(params.category_id));
  }
  if (params.is_visible !== undefined) {
    query.set("is_visible", String(params.is_visible));
  }
  return apiRequest<PaginatedResponse<AdminTorrentItem>>(`/admin/torrents?${query.toString()}`);
}


export function updateAdminTorrent(
  torrentId: number,
  payload: AdminTorrentUpdatePayload,
): Promise<AdminTorrentItem> {
  return apiRequest<AdminTorrentItem>(`/admin/torrents/${torrentId}`, {
    method: "PATCH",
    body: payload,
  });
}


export function getAdminSiteSettings(): Promise<SiteSettings> {
  return apiRequest<SiteSettings>("/admin/site-settings");
}


export function updateAdminSiteSettings(site_name: string): Promise<SiteSettings> {
  return apiRequest<SiteSettings>("/admin/site-settings", {
    method: "PATCH",
    body: {
      site_name,
    },
  });
}


export function runTrackerSync(): Promise<AdminTrackerSyncResult> {
  return apiRequest<AdminTrackerSyncResult>("/admin/tracker/sync", {
    method: "POST",
  });
}


export function listAdminAuditLogs(pageSize = 10): Promise<PaginatedResponse<AdminAuditLogItem>> {
  return apiRequest<PaginatedResponse<AdminAuditLogItem>>(`/admin/audit-logs?page_size=${pageSize}`);
}
