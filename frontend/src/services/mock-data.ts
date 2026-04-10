import type { CurrentUser } from '@/types/auth';
import type {
  AdminDashboardStats,
  AdminUser,
  Announcement,
  AuditLog,
  SaveSiteSettingsPayload,
  SiteSettings,
  TrackerSyncLog,
  TrackerSyncLogFilters,
  TrackerSyncOverview,
  TrackerSyncReleaseDetail,
  TrackerSyncUserDetail,
  UpdateUserPayload,
} from '@/types/admin';
import type { Category, DownloadRecord, Release, Tag } from '@/types/release';
import type { SiteTheme } from '@/types/theme';
import { DEFAULT_LOGIN_BACKGROUND_CSS } from '@/utils/site-branding';

const createPasskey = () => Math.random().toString(36).slice(2).padEnd(32, 'x').slice(0, 32);
const createApiToken = () => `${createPasskey()}${createPasskey()}`;
const createInitialPassword = () => `Temp${Math.random().toString(36).slice(2, 8)}!9`;

function nowIso() {
  return new Date().toISOString();
}

function maybeCreateObjectUrl(file?: File | null) {
  if (!file || typeof URL === 'undefined' || typeof URL.createObjectURL !== 'function') {
    return '';
  }

  return URL.createObjectURL(file);
}

export const categories: Category[] = [
  { id: 1, name: '动画', slug: 'anime', sortOrder: 1, isActive: true },
  { id: 2, name: '日剧', slug: 'jdrama', sortOrder: 2, isActive: true },
  { id: 3, name: '综艺', slug: 'variety', sortOrder: 3, isActive: true },
];

export const tags: Tag[] = [
  { id: 1, name: '1080p', slug: '1080p' },
  { id: 2, name: '简中', slug: 'chs' },
  { id: 3, name: '繁中', slug: 'cht' },
  { id: 4, name: '双语', slug: 'bilingual' },
];

export const users: AdminUser[] = [
  {
    id: 1,
    username: 'admin',
    displayName: '站务总控',
    email: 'admin@subtitle.local',
    role: 'admin',
    status: 'active',
    passkey: createPasskey(),
    lastLoginAt: '2026-04-10T10:20:00+08:00',
    joinedAt: '2025-11-15T10:00:00+08:00',
    createdReleaseCount: 3,
    trackerSync: {
      status: 'success',
      message: '用户状态与 passkey 已同步到 XBT。',
      updatedAt: '2026-04-10T10:18:00+08:00',
    },
    xbtUser: {
      state: 'enabled',
      canLeech: true,
      downloaded: 428000000000,
      uploaded: 1950000000000,
      completed: 312,
    },
  },
  {
    id: 2,
    username: 'uploader',
    displayName: '片源搬运组',
    email: 'uploader@subtitle.local',
    role: 'uploader',
    status: 'active',
    passkey: createPasskey(),
    lastLoginAt: '2026-04-10T09:40:00+08:00',
    joinedAt: '2025-12-01T09:10:00+08:00',
    createdReleaseCount: 6,
    trackerSync: {
      status: 'success',
      message: '用户状态与 passkey 已同步到 XBT。',
      updatedAt: '2026-04-10T09:36:00+08:00',
    },
    xbtUser: {
      state: 'enabled',
      canLeech: true,
      downloaded: 156000000000,
      uploaded: 820000000000,
      completed: 144,
    },
  },
  {
    id: 3,
    username: 'user',
    displayName: '普通成员',
    email: 'user@subtitle.local',
    role: 'user',
    status: 'active',
    passkey: createPasskey(),
    lastLoginAt: '2026-04-10T08:30:00+08:00',
    joinedAt: '2026-01-03T11:10:00+08:00',
    createdReleaseCount: 0,
    trackerSync: {
      status: 'success',
      message: '用户状态与 passkey 已同步到 XBT。',
      updatedAt: '2026-04-10T08:28:00+08:00',
    },
    xbtUser: {
      state: 'enabled',
      canLeech: true,
      downloaded: 92000000000,
      uploaded: 44000000000,
      completed: 28,
    },
  },
];

function userSummary(userId: number) {
  const user = users.find((item) => item.id === userId);
  if (!user) {
    throw new Error('User not found.');
  }

  return {
    id: user.id,
    username: user.username,
    displayName: user.displayName,
    role: user.role,
  } as const;
}

export const releases: Release[] = [
  {
    id: 101,
    title: '孤独摇滚 TV 01-12 合集',
    subtitle: 'BDRip 1080p 简繁外挂',
    description: '站内首页卡片、列表页和详情页都使用这一条数据做演示。',
    category: categories[0],
    tags: [tags[0], tags[1], tags[2]],
    status: 'published',
    sizeBytes: 38420000000,
    infohash: '4df4010a4af5f6082705df0ea5c79d0fceba9f10',
    publishedAt: '2026-04-10T09:15:00+08:00',
    updatedAt: '2026-04-10T09:40:00+08:00',
    createdBy: userSummary(2),
    files: [{ path: '[SubGroup]/Bocchi/S01E01.mkv', sizeBytes: 3120000000 }],
    downloadCount: 74,
    completionCount: 23,
    activePeers: 9,
    trackerSync: {
      status: 'success',
      message: '资源白名单状态已同步到 XBT。',
      updatedAt: '2026-04-10T09:16:00+08:00',
    },
    xbtFile: {
      state: 'whitelisted',
      seeders: 9,
      leechers: 2,
      completed: 23,
      createdAt: '2026-04-10T09:15:00+08:00',
      updatedAt: '2026-04-10T09:16:00+08:00',
    },
  },
  {
    id: 102,
    title: 'Last Mile 电影版',
    subtitle: 'WEB-DL 1080p 双语字幕',
    description: '电影类资源示例。',
    category: categories[1],
    tags: [tags[0], tags[3]],
    status: 'published',
    sizeBytes: 8420000000,
    infohash: '2f14010a4af5f6082705df0ea5c79d0fceba9f98',
    publishedAt: '2026-04-09T19:20:00+08:00',
    updatedAt: '2026-04-09T19:22:00+08:00',
    createdBy: userSummary(2),
    files: [{ path: 'Last.Mile.2026.1080p.WEB-DL.mkv', sizeBytes: 8420000000 }],
    downloadCount: 46,
    completionCount: 17,
    activePeers: 7,
    trackerSync: {
      status: 'success',
      message: '资源白名单状态已同步到 XBT。',
      updatedAt: '2026-04-09T19:21:00+08:00',
    },
    xbtFile: {
      state: 'whitelisted',
      seeders: 7,
      leechers: 1,
      completed: 17,
      createdAt: '2026-04-09T19:20:00+08:00',
      updatedAt: '2026-04-09T19:21:00+08:00',
    },
  },
  {
    id: 103,
    title: '春季新番打包',
    subtitle: '归档用隐藏条目',
    description: '后台资源管理页里的隐藏状态样例。',
    category: categories[0],
    tags: [tags[0]],
    status: 'hidden',
    sizeBytes: 12500000000,
    infohash: '7f14010a4af5f6082705df0ea5c79d0fceba9f24',
    publishedAt: '2026-04-08T17:30:00+08:00',
    updatedAt: '2026-04-10T08:15:00+08:00',
    createdBy: userSummary(1),
    files: [{ path: 'Archive/Spring/Title-01.mkv', sizeBytes: 6000000000 }],
    downloadCount: 11,
    completionCount: 4,
    activePeers: 0,
    trackerSync: {
      status: 'success',
      message: '资源已从 XBT 白名单中移除。',
      updatedAt: '2026-04-10T08:15:00+08:00',
    },
    xbtFile: {
      state: 'deleted',
      seeders: 0,
      leechers: 0,
      completed: 4,
      createdAt: '2026-04-08T17:30:00+08:00',
      updatedAt: '2026-04-10T08:15:00+08:00',
    },
  },
];

export const downloadLogs: DownloadRecord[] = [
  {
    id: 9001,
    releaseId: 101,
    releaseTitle: '孤独摇滚 TV 01-12 合集',
    downloadedAt: '2026-04-10T11:03:00+08:00',
    downloaderId: 3,
    downloaderName: '普通成员',
  },
  {
    id: 9002,
    releaseId: 102,
    releaseTitle: 'Last Mile 电影版',
    downloadedAt: '2026-04-10T09:38:00+08:00',
    downloaderId: 3,
    downloaderName: '普通成员',
  },
];

export const announcements: Announcement[] = [
  {
    id: 1,
    title: '推荐关闭 DHT / PEX',
    content: '站内推荐 qBittorrent 关闭 DHT / PEX，仅保留私有 tracker。',
    status: 'online',
    audience: 'all',
    updatedAt: '2026-04-10T09:00:00+08:00',
  },
  {
    id: 2,
    title: '上传前请确认 private 标记',
    content: '新发布 torrent 必须包含 private=1。',
    status: 'online',
    audience: 'uploader',
    updatedAt: '2026-04-09T18:30:00+08:00',
  },
];

export const trackerSyncLogs: TrackerSyncLog[] = [
  {
    id: 1,
    scope: 'full',
    targetName: '全量同步',
    status: 'success',
    message: '用户与资源镜像已经与 XBT 对齐。',
    updatedAt: '2026-04-10T08:20:00+08:00',
    userId: null,
    releaseId: null,
    retryable: true,
  },
  {
    id: 2,
    scope: 'release',
    targetName: releases[0].title,
    status: 'success',
    message: '资源白名单状态已同步到 XBT。',
    updatedAt: '2026-04-10T09:16:00+08:00',
    userId: null,
    releaseId: 101,
    retryable: true,
  },
  {
    id: 3,
    scope: 'user',
    targetName: users[2].username,
    status: 'warning',
    message: '等待下一轮 tracker 数据刷新。',
    updatedAt: '2026-04-10T08:28:00+08:00',
    userId: 3,
    releaseId: null,
    retryable: true,
  },
];

export const auditLogs: AuditLog[] = [
  {
    id: 1,
    actorName: '站务总控',
    action: '重置 passkey',
    targetType: '用户',
    targetName: 'user',
    createdAt: '2026-04-10T08:30:00+08:00',
    detail: '因安全策略执行了人工重置。',
  },
  {
    id: 2,
    actorName: '片源搬运组',
    action: '发布资源',
    targetType: '资源',
    targetName: releases[0].title,
    createdAt: '2026-04-10T09:15:00+08:00',
    detail: '上传 torrent 并补充了资源说明。',
  },
];

export const siteSettings: SiteSettings = {
  siteName: '字幕组分流站',
  siteDescription: '内部资源浏览、下载与 RSS 订阅入口',
  loginNotice: '仅限内部成员使用，不开放公开注册。',
  rssBasePath: 'https://tracker.subtitle.local/rss',
  downloadNotice: '种子文件包含个人身份信息，请勿外传。',
  siteIconUrl: '',
  siteIconFileUrl: '',
  siteIconResolvedUrl: '',
  loginBackgroundType: 'css',
  loginBackgroundApiUrl: '',
  loginBackgroundFileUrl: '',
  loginBackgroundResolvedUrl: '',
  loginBackgroundCss: DEFAULT_LOGIN_BACKGROUND_CSS,
};

function defaultTheme(): SiteTheme {
  return {
    mode: 'system',
    customCss: '',
  };
}

export const userThemes: Record<number, SiteTheme> = {
  1: defaultTheme(),
  2: defaultTheme(),
  3: defaultTheme(),
};

export const userApiTokens: Record<number, string> = users.reduce((accumulator, user) => {
  accumulator[user.id] = createApiToken();
  return accumulator;
}, {} as Record<number, string>);

export function getUserById(userId: number): AdminUser | undefined {
  return users.find((item) => item.id === userId);
}

export function getUserByUsername(username: string): AdminUser | undefined {
  return users.find((item) => item.username.toLowerCase() === username.toLowerCase());
}

function getReleaseById(releaseId: number): Release | undefined {
  return releases.find((item) => item.id === releaseId);
}

function createTrackerSyncSnapshot(status: 'success' | 'warning' | 'failed', message: string) {
  return {
    status,
    message,
    updatedAt: nowIso(),
  } as const;
}

function createXbtFileSnapshot(status: Release['status'], completed = 0, activePeers = 0, publishedAt?: string) {
  const timestamp = nowIso();

  if (status === 'published') {
    return {
      state: 'whitelisted' as const,
      seeders: activePeers,
      leechers: 0,
      completed,
      createdAt: publishedAt ?? timestamp,
      updatedAt: timestamp,
    };
  }

  if (status === 'hidden') {
    return {
      state: 'deleted' as const,
      seeders: 0,
      leechers: 0,
      completed,
      createdAt: publishedAt ?? timestamp,
      updatedAt: timestamp,
    };
  }

  return {
    state: 'missing' as const,
    seeders: null,
    leechers: null,
    completed: null,
    createdAt: null,
    updatedAt: null,
  };
}

function applyUserTrackerSnapshot(user: AdminUser, message?: string) {
  user.trackerSync = createTrackerSyncSnapshot(
    user.status === 'active' ? 'success' : 'warning',
    message ?? (user.status === 'active' ? '用户状态与 passkey 已同步到 XBT。' : '用户在 XBT 中已被禁用。'),
  );
  user.xbtUser = {
    state: user.status === 'active' ? 'enabled' : 'disabled',
    canLeech: user.status === 'active',
    downloaded: user.xbtUser?.downloaded ?? 0,
    uploaded: user.xbtUser?.uploaded ?? 0,
    completed: user.xbtUser?.completed ?? 0,
  };
}

function applyReleaseTrackerSnapshot(release: Release) {
  release.updatedAt = nowIso();
  release.trackerSync =
    release.status === 'published'
      ? createTrackerSyncSnapshot('success', '资源白名单状态已同步到 XBT。')
      : release.status === 'hidden'
        ? createTrackerSyncSnapshot('success', '资源已从 XBT 白名单中移除。')
        : createTrackerSyncSnapshot('warning', '资源尚未发布，暂不写入 XBT。');
  release.xbtFile = createXbtFileSnapshot(
    release.status,
    release.completionCount,
    release.activePeers,
    release.publishedAt,
  );
}

function buildTrackerSyncLog(
  log: Omit<TrackerSyncLog, 'id' | 'updatedAt' | 'retryable'> & Partial<Pick<TrackerSyncLog, 'retryable'>>,
): TrackerSyncLog {
  return {
    id: Date.now(),
    updatedAt: nowIso(),
    retryable: log.retryable ?? true,
    ...log,
  };
}

export function appendAuditLog(action: Omit<AuditLog, 'id' | 'createdAt'>): AuditLog {
  const item: AuditLog = {
    id: Date.now(),
    createdAt: nowIso(),
    ...action,
  };
  auditLogs.unshift(item);
  return item;
}

export function appendTrackerSyncLog(
  log: Omit<TrackerSyncLog, 'id' | 'updatedAt' | 'retryable'> & Partial<Pick<TrackerSyncLog, 'retryable'>>,
): TrackerSyncLog {
  const item = buildTrackerSyncLog(log);
  trackerSyncLogs.unshift(item);
  return item;
}

export function getCurrentUserApiToken(userId: number): string {
  if (!getUserById(userId)) {
    throw new Error('用户不存在');
  }

  if (!userApiTokens[userId]) {
    userApiTokens[userId] = createApiToken();
  }

  return userApiTokens[userId];
}

export function resetUserApiToken(userId: number): string {
  if (!getUserById(userId)) {
    throw new Error('用户不存在');
  }

  userApiTokens[userId] = createApiToken();
  return userApiTokens[userId];
}

export function updateUserRecord(userId: number, patch: Partial<UpdateUserPayload>): AdminUser {
  const user = getUserById(userId);
  if (!user) {
    throw new Error('用户不存在');
  }

  Object.assign(user, patch);
  return user;
}

export function resetPasskey(userId: number): AdminUser {
  const user = getUserById(userId);
  if (!user) {
    throw new Error('用户不存在');
  }

  user.passkey = createPasskey();
  applyUserTrackerSnapshot(user, 'passkey 已重置并同步到 XBT。');
  appendTrackerSyncLog({
    scope: 'user',
    targetName: user.username,
    status: user.trackerSync?.status ?? 'success',
    message: user.trackerSync?.message ?? 'passkey 已重置并同步到 XBT。',
    userId: user.id,
    releaseId: null,
  });
  return user;
}

export function createReleaseFromPayload(payload: {
  title: string;
  subtitle: string;
  description: string;
  categorySlug: string;
  tagSlugs: string[];
  torrentFileName?: string;
  createdBy: CurrentUser;
  status?: 'draft' | 'published' | 'hidden';
}): Release {
  const category = categories.find((item) => item.slug === payload.categorySlug) ?? categories[0];
  const releaseTags = tags.filter((item) => payload.tagSlugs.includes(item.slug));
  const createdAt = nowIso();
  const release: Release = {
    id: Date.now(),
    title: payload.title,
    subtitle: payload.subtitle,
    description: payload.description,
    category,
    tags: releaseTags,
    status: payload.status ?? 'published',
    sizeBytes: 9800000000,
    infohash: createPasskey().slice(0, 32),
    publishedAt: createdAt,
    updatedAt: createdAt,
    createdBy: {
      id: payload.createdBy.id,
      username: payload.createdBy.username,
      displayName: payload.createdBy.displayName,
      role: payload.createdBy.role,
    },
    files: [{ path: payload.torrentFileName ?? 'new-upload.torrent', sizeBytes: 9800000000 }],
    downloadCount: 0,
    completionCount: 0,
    activePeers: 0,
    trackerSync: null,
    xbtFile: null,
  };

  applyReleaseTrackerSnapshot(release);
  releases.unshift(release);
  return release;
}

export function updateReleaseData(
  releaseId: number,
  patch: Partial<Pick<Release, 'title' | 'subtitle' | 'description' | 'status'>>,
): Release {
  const release = getReleaseById(releaseId);
  if (!release) {
    throw new Error('资源不存在');
  }

  Object.assign(release, patch, { updatedAt: nowIso() });
  if (patch.status) {
    applyReleaseTrackerSnapshot(release);
  }
  return release;
}

export function updateReleaseVisibility(releaseId: number, status: 'published' | 'hidden'): Release {
  const release = updateReleaseData(releaseId, { status });
  appendTrackerSyncLog({
    scope: 'release',
    targetName: release.title,
    status: release.trackerSync?.status ?? 'success',
    message: release.trackerSync?.message ?? '资源状态已更新。',
    userId: null,
    releaseId: release.id,
  });
  return release;
}

export function createUserRecord(payload: {
  username: string;
  displayName: string;
  email: string;
  role: 'admin' | 'uploader' | 'user';
  password?: string;
}): AdminUser {
  const now = nowIso();
  const generatedPassword = payload.password ? undefined : createInitialPassword();
  const user: AdminUser = {
    id: Date.now(),
    username: payload.username,
    displayName: payload.displayName,
    email: payload.email,
    role: payload.role,
    status: 'active',
    passkey: createPasskey(),
    lastLoginAt: now,
    joinedAt: now,
    createdReleaseCount: 0,
    trackerSync: {
      status: 'success',
      message: '用户状态与 passkey 已同步到 XBT。',
      updatedAt: now,
    },
    xbtUser: {
      state: 'enabled',
      canLeech: true,
      downloaded: 0,
      uploaded: 0,
      completed: 0,
    },
    initialPassword: generatedPassword,
  };
  users.unshift(user);
  userApiTokens[user.id] = createApiToken();
  userThemes[user.id] = defaultTheme();
  return user;
}

export function toggleUserStatus(userId: number, nextStatus: 'active' | 'disabled'): AdminUser {
  const user = getUserById(userId);
  if (!user) {
    throw new Error('用户不存在');
  }

  user.status = nextStatus;
  applyUserTrackerSnapshot(user);
  return user;
}

export function saveCategory(payload: Pick<Category, 'name' | 'slug'> & Partial<Category>): Category {
  if (payload.id) {
    const current = categories.find((item) => item.id === payload.id);
    if (!current) {
      throw new Error('分类不存在');
    }
    Object.assign(current, payload);
    return current;
  }

  const item: Category = {
    id: Date.now(),
    name: payload.name,
    slug: payload.slug,
    sortOrder: payload.sortOrder ?? categories.length + 1,
    isActive: payload.isActive ?? true,
  };
  categories.push(item);
  return item;
}

export function saveTag(payload: Pick<Tag, 'name' | 'slug'> & Partial<Tag>): Tag {
  if (payload.id) {
    const current = tags.find((item) => item.id === payload.id);
    if (!current) {
      throw new Error('标签不存在');
    }
    Object.assign(current, payload);
    return current;
  }

  const item: Tag = {
    id: Date.now(),
    name: payload.name,
    slug: payload.slug,
  };
  tags.push(item);
  return item;
}

export function saveAnnouncement(
  payload: Pick<Announcement, 'title' | 'content' | 'status' | 'audience'> & Partial<Announcement>,
): Announcement {
  if (payload.id) {
    const current = announcements.find((item) => item.id === payload.id);
    if (!current) {
      throw new Error('公告不存在');
    }
    Object.assign(current, payload, { updatedAt: nowIso() });
    return current;
  }

  const item: Announcement = {
    id: Date.now(),
    title: payload.title,
    content: payload.content,
    status: payload.status,
    audience: payload.audience,
    updatedAt: nowIso(),
  };
  announcements.unshift(item);
  return item;
}

export function saveSettings(payload: SaveSiteSettingsPayload): SiteSettings {
  const siteIconFileUrl = payload.clearSiteIconFile
    ? ''
    : payload.siteIconFile
      ? maybeCreateObjectUrl(payload.siteIconFile)
      : siteSettings.siteIconFileUrl;
  const loginBackgroundFileUrl = payload.clearLoginBackgroundFile
    ? ''
    : payload.loginBackgroundFile
      ? maybeCreateObjectUrl(payload.loginBackgroundFile)
      : siteSettings.loginBackgroundFileUrl;

  Object.assign(siteSettings, {
    siteName: payload.siteName,
    siteDescription: payload.siteDescription,
    loginNotice: payload.loginNotice,
    rssBasePath: payload.rssBasePath,
    downloadNotice: payload.downloadNotice,
    siteIconUrl: payload.siteIconUrl,
    siteIconFileUrl,
    siteIconResolvedUrl: siteIconFileUrl || payload.siteIconUrl,
    loginBackgroundType: payload.loginBackgroundType,
    loginBackgroundApiUrl: payload.loginBackgroundApiUrl,
    loginBackgroundFileUrl,
    loginBackgroundResolvedUrl:
      payload.loginBackgroundType === 'file'
        ? loginBackgroundFileUrl
        : payload.loginBackgroundType === 'api'
          ? payload.loginBackgroundApiUrl
          : '',
    loginBackgroundCss: payload.loginBackgroundCss,
  });

  return siteSettings;
}

export function getThemeRecord(userId: number): SiteTheme {
  if (!userThemes[userId]) {
    userThemes[userId] = defaultTheme();
  }

  return userThemes[userId];
}

export function saveThemeRecord(userId: number, payload: SiteTheme): SiteTheme {
  Object.assign(getThemeRecord(userId), payload);
  return getThemeRecord(userId);
}

export function listTrackerSyncLogRecords(filters: TrackerSyncLogFilters = {}): TrackerSyncLog[] {
  const keyword = filters.q?.trim().toLowerCase() ?? '';
  const limit = Math.min(Math.max(filters.limit ?? 100, 1), 200);

  return trackerSyncLogs
    .filter((item) => {
      if (filters.scope && item.scope !== filters.scope) return false;
      if (filters.status && item.status !== filters.status) return false;
      if (filters.userId !== undefined && item.userId !== filters.userId) return false;
      if (filters.releaseId !== undefined && item.releaseId !== filters.releaseId) return false;
      if (keyword) {
        return [item.targetName, item.message].some((field) => field.toLowerCase().includes(keyword));
      }
      return true;
    })
    .slice(0, limit);
}

export function getDashboardStats(): AdminDashboardStats {
  return {
    userCount: users.length,
    releaseCount: releases.length,
    activeReleaseCount: releases.filter((item) => item.status === 'published').length,
    pendingSyncCount: trackerSyncLogs.filter((item) => item.status !== 'success').length,
    activeAnnouncementCount: announcements.filter((item) => item.status === 'online').length,
  };
}

export function getTrackerSyncOverview(): TrackerSyncOverview {
  const successLogs = trackerSyncLogs.filter((item) => item.status === 'success');
  const warningLogs = trackerSyncLogs.filter((item) => item.status === 'warning');
  const failedLogs = trackerSyncLogs.filter((item) => item.status === 'failed');

  return {
    summary: {
      xbtSyncEnabled: true,
      xbtDatabaseAlias: 'default',
      totalLogs: trackerSyncLogs.length,
      successCount: successLogs.length,
      warningCount: warningLogs.length,
      failedCount: failedLogs.length,
      pendingCount: warningLogs.length + failedLogs.length,
      lastSuccessAt: successLogs[0]?.updatedAt ?? null,
      lastFailureAt: failedLogs[0]?.updatedAt ?? null,
      lastFullSyncAt: trackerSyncLogs.find((item) => item.scope === 'full')?.updatedAt ?? null,
    },
    latestLogs: trackerSyncLogs.slice(0, 20),
    failedLogs: failedLogs.slice(0, 10),
  };
}

export function getTrackerSyncUserDetail(userId: number): TrackerSyncUserDetail | null {
  const user = getUserById(userId);
  if (!user) {
    return null;
  }

  return {
    user: {
      id: user.id,
      username: user.username,
      displayName: user.displayName,
      role: user.role,
      status: user.status,
      passkey: user.passkey,
    },
    trackerSync: user.trackerSync ?? null,
    xbtUser: user.xbtUser ?? {
      state: 'missing',
      canLeech: null,
      downloaded: null,
      uploaded: null,
      completed: null,
    },
    recentLogs: trackerSyncLogs.filter((item) => item.scope === 'user' && item.userId === user.id).slice(0, 10),
  };
}

export function getTrackerSyncReleaseDetail(releaseId: number): TrackerSyncReleaseDetail | null {
  const release = getReleaseById(releaseId);
  if (!release) {
    return null;
  }

  return {
    release: {
      id: release.id,
      title: release.title,
      status: release.status,
      infohash: release.infohash,
      publishedAt: release.publishedAt,
      createdById: release.createdBy.id,
    },
    trackerSync: release.trackerSync ?? null,
    xbtFile: release.xbtFile ?? {
      state: 'missing',
      seeders: null,
      leechers: null,
      completed: null,
      createdAt: null,
      updatedAt: null,
    },
    recentLogs: trackerSyncLogs
      .filter((item) => item.scope === 'release' && item.releaseId === release.id)
      .slice(0, 10),
  };
}

export function runUserTrackerSync(userId: number): TrackerSyncLog {
  const user = getUserById(userId);
  if (!user) {
    throw new Error('用户不存在');
  }

  applyUserTrackerSnapshot(user);
  return appendTrackerSyncLog({
    scope: 'user',
    targetName: user.username,
    status: user.trackerSync?.status ?? 'success',
    message: user.trackerSync?.message ?? '用户状态已同步。',
    userId: user.id,
    releaseId: null,
  });
}

export function runReleaseTrackerSync(releaseId: number): TrackerSyncLog {
  const release = getReleaseById(releaseId);
  if (!release) {
    throw new Error('资源不存在');
  }

  applyReleaseTrackerSnapshot(release);
  return appendTrackerSyncLog({
    scope: 'release',
    targetName: release.title,
    status: release.trackerSync?.status ?? 'success',
    message: release.trackerSync?.message ?? '资源状态已同步。',
    userId: null,
    releaseId: release.id,
  });
}

export function runFullTrackerSyncLog(): TrackerSyncLog {
  users.forEach((user) => applyUserTrackerSnapshot(user));
  releases.forEach((release) => applyReleaseTrackerSnapshot(release));

  return appendTrackerSyncLog({
    scope: 'full',
    targetName: '全量同步',
    status: 'success',
    message: '已按用户状态和资源状态重新写入 XBT 镜像。',
    userId: null,
    releaseId: null,
  });
}

export function retryTrackerSyncLogById(logId: number): TrackerSyncLog {
  const sourceLog = trackerSyncLogs.find((item) => item.id === logId);
  if (!sourceLog) {
    throw new Error('同步日志不存在');
  }

  if (sourceLog.scope === 'full') {
    return runFullTrackerSyncLog();
  }

  if (sourceLog.scope === 'user' && sourceLog.userId !== null) {
    return runUserTrackerSync(sourceLog.userId);
  }

  if (sourceLog.scope === 'release' && sourceLog.releaseId !== null) {
    return runReleaseTrackerSync(sourceLog.releaseId);
  }

  return appendTrackerSyncLog({
    scope: sourceLog.scope,
    targetName: sourceLog.targetName,
    status: 'warning',
    message: '原始日志缺少可重试目标，已跳过。',
    userId: sourceLog.userId,
    releaseId: sourceLog.releaseId,
  });
}
