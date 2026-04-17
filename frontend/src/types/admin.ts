import type { CurrentUser } from './auth';

export type SyncStatus = 'success' | 'warning' | 'failed';
export type AnnouncementStatus = 'online' | 'draft' | 'offline';
export type LoginBackgroundType = 'api' | 'file' | 'css';
export type InviteCodeStatus = 'available' | 'used' | 'expired' | 'revoked';

export interface AdminUser extends CurrentUser {
  createdReleaseCount: number;
  initialPassword?: string;
}

export interface ApiTokenPayload {
  apiToken: string;
}

export interface Announcement {
  id: number;
  title: string;
  content: string;
  status: AnnouncementStatus;
  audience: 'all' | 'uploader' | 'admin';
  updatedAt: string;
}

export interface AuditLog {
  id: number;
  actorName: string;
  action: string;
  targetType: string;
  targetName: string;
  createdAt: string;
  detail: string;
}

export interface AdminDashboardStats {
  userCount: number;
  releaseCount: number;
  activeReleaseCount: number;
  draftReleaseCount: number;
  activeAnnouncementCount: number;
}

export interface SiteSettings {
  siteName: string;
  siteDescription: string;
  loginNotice: string;
  allowPublicRegistration: boolean;
  rssBasePath: string;
  downloadNotice: string;
  siteIconUrl: string;
  siteIconFileUrl: string;
  siteIconResolvedUrl: string;
  loginBackgroundType: LoginBackgroundType;
  loginBackgroundApiUrl: string;
  loginBackgroundFileUrl: string;
  loginBackgroundResolvedUrl: string;
  loginBackgroundCss: string;
}

export interface InviteCode {
  id: number;
  code: string;
  note: string;
  status: InviteCodeStatus;
  isActive: boolean;
  createdByName: string;
  usedByName: string | null;
  createdAt: string;
  usedAt: string | null;
  expiresAt: string | null;
  canRevoke: boolean;
}

export interface CreateInviteCodesPayload {
  count: number;
  note?: string;
  expiresAt?: string | null;
}

export interface SaveSiteSettingsPayload {
  siteName: string;
  siteDescription: string;
  loginNotice: string;
  allowPublicRegistration: boolean;
  rssBasePath: string;
  downloadNotice: string;
  siteIconUrl: string;
  siteIconFile?: File | null;
  clearSiteIconFile?: boolean;
  loginBackgroundType: LoginBackgroundType;
  loginBackgroundApiUrl: string;
  loginBackgroundFile?: File | null;
  clearLoginBackgroundFile?: boolean;
  loginBackgroundCss: string;
}

export interface RssOverview {
  generalFeed: string;
  recentReleaseTitles: string[];
}

export interface CreateUserPayload {
  username: string;
  displayName: string;
  email: string;
  role: 'admin' | 'uploader' | 'user';
  password?: string;
}

export interface UpdateUserPayload {
  displayName: string;
  email: string;
  role: 'admin' | 'uploader' | 'user';
}

export interface ToggleUserStatusPayload {
  userId: number;
  nextStatus: 'active' | 'disabled';
}
