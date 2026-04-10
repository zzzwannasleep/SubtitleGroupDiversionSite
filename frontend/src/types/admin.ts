import type { CurrentUser, UserRole, UserStatus } from './auth';
import type { ReleaseStatus, XbtFileSnapshot } from './release';

export type SyncStatus = 'success' | 'warning' | 'failed';
export type AnnouncementStatus = 'online' | 'draft' | 'offline';
export type XbtUserState = 'enabled' | 'disabled' | 'missing' | 'unavailable';
export type LoginBackgroundType = 'api' | 'file' | 'css';

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

export interface TrackerSyncLog {
  id: number;
  scope: 'user' | 'release' | 'full';
  targetName: string;
  status: SyncStatus;
  message: string;
  updatedAt: string;
  userId: number | null;
  releaseId: number | null;
  retryable: boolean;
}

export interface TrackerSyncLogFilters {
  scope?: TrackerSyncLog['scope'];
  status?: SyncStatus;
  userId?: number;
  releaseId?: number;
  q?: string;
  limit?: number;
}

export interface TrackerSyncOverviewSummary {
  xbtSyncEnabled: boolean;
  xbtDatabaseAlias: string;
  totalLogs: number;
  successCount: number;
  warningCount: number;
  failedCount: number;
  pendingCount: number;
  lastSuccessAt: string | null;
  lastFailureAt: string | null;
  lastFullSyncAt: string | null;
}

export interface TrackerSyncOverview {
  summary: TrackerSyncOverviewSummary;
  latestLogs: TrackerSyncLog[];
  failedLogs: TrackerSyncLog[];
}

export interface TrackerSyncUserTarget {
  id: number;
  username: string;
  displayName: string;
  role: UserRole;
  status: UserStatus;
  passkey: string;
}

export interface TrackerSyncUserDetail {
  user: TrackerSyncUserTarget;
  trackerSync: TrackerSyncSnapshot | null;
  xbtUser: XbtUserSnapshot;
  recentLogs: TrackerSyncLog[];
}

export interface TrackerSyncReleaseTarget {
  id: number;
  title: string;
  status: ReleaseStatus;
  infohash: string;
  publishedAt: string;
  createdById: number;
}

export interface TrackerSyncReleaseDetail {
  release: TrackerSyncReleaseTarget;
  trackerSync: TrackerSyncSnapshot | null;
  xbtFile: XbtFileSnapshot;
  recentLogs: TrackerSyncLog[];
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
  siteIconUrl: string;
  siteIconFileUrl: string;
  siteIconResolvedUrl: string;
  loginBackgroundType: LoginBackgroundType;
  loginBackgroundApiUrl: string;
  loginBackgroundFileUrl: string;
  loginBackgroundResolvedUrl: string;
  loginBackgroundCss: string;
}

export interface SaveSiteSettingsPayload {
  siteName: string;
  siteDescription: string;
  loginNotice: string;
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
  password?: string;
}

export interface UpdateUserPayload {
  displayName: string;
  email: string;
  role: UserRole;
}

export interface ToggleUserStatusPayload {
  userId: number;
  nextStatus: UserStatus;
}
