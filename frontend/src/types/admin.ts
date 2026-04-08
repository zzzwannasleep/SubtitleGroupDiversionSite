import type { CurrentUser, UserRole, UserStatus } from './auth';

export type SyncStatus = 'success' | 'warning' | 'failed';
export type AnnouncementStatus = 'online' | 'draft' | 'offline';
export type XbtUserState = 'enabled' | 'disabled' | 'missing' | 'unavailable';

export interface TrackerSyncSnapshot {
  status: SyncStatus;
  message: string;
  updatedAt: string;
}

export interface XbtUserSnapshot {
  state: XbtUserState;
  canLeech: boolean | null;
  downloaded: number | null;
  uploaded: number | null;
  completed: number | null;
}

export interface AdminUser extends CurrentUser {
  createdReleaseCount: number;
  initialPassword?: string;
  trackerSync?: TrackerSyncSnapshot | null;
  xbtUser?: XbtUserSnapshot | null;
}

export interface Announcement {
  id: number;
  title: string;
  content: string;
  status: AnnouncementStatus;
  audience: 'all' | 'uploader' | 'admin';
  updatedAt: string;
}

export interface TrackerSyncLog {
  id: number;
  scope: 'user' | 'release' | 'full';
  targetName: string;
  status: SyncStatus;
  message: string;
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
  pendingSyncCount: number;
  activeAnnouncementCount: number;
}

export interface SiteSettings {
  siteName: string;
  siteDescription: string;
  loginNotice: string;
  rssBasePath: string;
  downloadNotice: string;
}

export interface RssFeedLink {
  label: string;
  url: string;
}

export interface RssOverview {
  generalFeed: string;
  categoryFeeds: RssFeedLink[];
  tagFeeds: RssFeedLink[];
  recentReleaseTitles: string[];
}

export interface CreateUserPayload {
  username: string;
  displayName: string;
  email: string;
  role: UserRole;
}

export interface ToggleUserStatusPayload {
  userId: number;
  nextStatus: UserStatus;
}
