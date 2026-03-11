import type { PaginatedResponse } from "@/types";
import type { SiteSettings } from "@/api/site";

import { apiRequest } from "./http";


export interface AdminUserItem {
  id: number;
  username: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
}

export interface AdminTrackerSyncResult {
  user_stats_updated: number;
  torrent_stats_updated: number;
  skipped: boolean;
  message: string;
}


export function listAdminUsers(): Promise<PaginatedResponse<AdminUserItem>> {
  return apiRequest<PaginatedResponse<AdminUserItem>>("/admin/users");
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
