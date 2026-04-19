import type { CurrentUser } from '@/types/auth';
import type {
  AdminDashboardStats,
  AdminUser,
  Announcement,
  AuditLog,
  CreateInviteCodesPayload,
  InviteCode,
  SaveSiteSettingsPayload,
  SiteSettings,
  UpdateUserPayload,
} from '@/types/admin';
import type { Category, DownloadRecord, Release, Tag } from '@/types/release';
import type { SiteTheme } from '@/types/theme';
import { DEFAULT_LOGIN_BACKGROUND_CSS } from '@/utils/site-branding';

const inviteCodeAlphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

function createSecretToken() {
  return Math.random().toString(36).slice(2).padEnd(32, 'x').slice(0, 32);
}

function createApiToken() {
  return `${createSecretToken()}${createSecretToken()}`;
}

function createInitialPassword() {
  return `Temp${Math.random().toString(36).slice(2, 8)}!9`;
}

function createInfohash() {
  return Array.from({ length: 40 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
}

function createInviteCodeValue() {
  const raw = Array.from(
    { length: 12 },
    () => inviteCodeAlphabet[Math.floor(Math.random() * inviteCodeAlphabet.length)],
  ).join('');
  return [raw.slice(0, 4), raw.slice(4, 8), raw.slice(8, 12)].join('-');
}

function normalizeInviteCode(value: string) {
  const compact = value.toUpperCase().replace(/[^A-Z0-9]/g, '');
  return [compact.slice(0, 4), compact.slice(4, 8), compact.slice(8, 12)].filter(Boolean).join('-');
}

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
    lastLoginAt: '2026-04-10T10:20:00+08:00',
    joinedAt: '2025-11-15T10:00:00+08:00',
    createdReleaseCount: 3,
  },
  {
    id: 2,
    username: 'uploader',
    displayName: '片源搬运组',
    email: 'uploader@subtitle.local',
    role: 'uploader',
    status: 'active',
    lastLoginAt: '2026-04-10T09:40:00+08:00',
    joinedAt: '2025-12-01T09:10:00+08:00',
    createdReleaseCount: 6,
  },
  {
    id: 3,
    username: 'user',
    displayName: '普通成员',
    email: 'user@subtitle.local',
    role: 'user',
    status: 'active',
    lastLoginAt: '2026-04-10T08:30:00+08:00',
    joinedAt: '2026-01-03T11:10:00+08:00',
    createdReleaseCount: 0,
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
    subtitle: 'BDRip 1080p 简繁外挂字幕',
    description: '首页、列表页和详情页都使用这条数据做演示。',
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
  },
  {
    id: 102,
    title: 'Last Mile 电影版',
    subtitle: 'WEB-DL 1080p 双语字幕',
    description: '电影资源示例。',
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
  },
  {
    id: 103,
    title: '春季新番打包',
    subtitle: '归档用隐藏条目',
    description: '后台资源管理页里的隐藏状态示例。',
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
    title: '建议关闭 DHT / PEX',
    content: '站内建议在下载器中关闭 DHT / PEX，减少无关连接干扰。',
    status: 'online',
    audience: 'all',
    updatedAt: '2026-04-10T09:00:00+08:00',
  },
  {
    id: 2,
    title: '上传前请确认资源信息',
    content: '发布页面现在直接接收 torrent 文件，请在上传前确认文件内容和命名无误。',
    status: 'online',
    audience: 'uploader',
    updatedAt: '2026-04-09T18:30:00+08:00',
  },
];

export const auditLogs: AuditLog[] = [
  {
    id: 1,
    actorName: '站务总控',
    action: '重置 API token',
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
  loginPageCss: '',
  siteName: '字幕组分流站',
  siteDescription: '内部资源浏览、下载与 RSS 订阅入口',
  loginNotice: '仅限内部成员使用，不开放公开注册。',
  allowPublicRegistration: false,
  rssBasePath: '/rss',
  downloadNotice: '请勿外传站内资源链接与 torrent 文件。',
  siteIconUrl: '',
  siteIconFileUrl: '',
  siteIconResolvedUrl: '',
  loginBackgroundType: 'css',
  loginBackgroundApiUrl: '',
  loginBackgroundFileUrl: '',
  loginBackgroundResolvedUrl: '',
  loginBackgroundCss: DEFAULT_LOGIN_BACKGROUND_CSS,
};

export const inviteCodes: InviteCode[] = [
  {
    id: 7001,
    code: 'M9QF-7K2A-XP4L',
    note: '四月新成员',
    status: 'available',
    isActive: true,
    createdByName: users[0].displayName,
    usedByName: null,
    createdAt: '2026-04-10T09:30:00+08:00',
    usedAt: null,
    expiresAt: '2026-05-01T00:00:00+08:00',
    canRevoke: true,
  },
  {
    id: 7002,
    code: 'N3TR-4Y6P-W8QK',
    note: '上传组备用',
    status: 'used',
    isActive: false,
    createdByName: users[0].displayName,
    usedByName: users[2].displayName,
    createdAt: '2026-04-03T12:00:00+08:00',
    usedAt: '2026-04-05T18:20:00+08:00',
    expiresAt: null,
    canRevoke: false,
  },
];

function defaultTheme(): SiteTheme {
  return {
    mode: 'system',
    customCss: '',
  };
}

const userThemes: Record<number, SiteTheme> = {
  1: defaultTheme(),
  2: defaultTheme(),
  3: defaultTheme(),
};

const userApiTokens: Record<number, string> = users.reduce((accumulator, user) => {
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

export function appendAuditLog(action: Omit<AuditLog, 'id' | 'createdAt'>): AuditLog {
  const item: AuditLog = {
    id: Date.now(),
    createdAt: nowIso(),
    ...action,
  };
  auditLogs.unshift(item);
  return item;
}

export function getCurrentUserApiToken(userId: number): string {
  if (!getUserById(userId)) {
    throw new Error('用户不存在。');
  }

  if (!userApiTokens[userId]) {
    userApiTokens[userId] = createApiToken();
  }

  return userApiTokens[userId];
}

export function resetUserApiToken(userId: number): string {
  if (!getUserById(userId)) {
    throw new Error('用户不存在。');
  }

  userApiTokens[userId] = createApiToken();
  return userApiTokens[userId];
}

export function updateUserRecord(userId: number, patch: Partial<UpdateUserPayload>): AdminUser {
  const user = getUserById(userId);
  if (!user) {
    throw new Error('用户不存在。');
  }

  Object.assign(user, patch);
  return user;
}

export function createReleaseFromPayload(payload: {
  title?: string;
  subtitle?: string;
  description?: string;
  categorySlug?: string;
  tagSlugs: string[];
  torrentFileName?: string;
  createdBy: CurrentUser;
  status?: 'draft' | 'published' | 'hidden';
}): Release {
  function filenameStem(name: string): string {
    const normalized = name.replace(/\\/g, '/');
    const base = normalized.split('/').pop() ?? name;
    const dot = base.lastIndexOf('.');
    if (dot <= 0) return base;
    return base.slice(0, dot);
  }

  const torrentName = payload.torrentFileName ?? 'upload.torrent';
  const stem = torrentName.replace(/\.torrent$/i, '');
  const innerPath = stem.includes('/') ? stem.replace(/\\/g, '/') : `${stem}.mkv`;
  const simulatedInfoName = innerPath;
  const titleFromInfoName = filenameStem(simulatedInfoName) || stem || '新上传资源';
  const category = categories.find((item) => item.slug === payload.categorySlug) ?? categories[0];
  const releaseTags = tags.filter((item) => payload.tagSlugs.includes(item.slug));
  const createdAt = nowIso();
  const release: Release = {
    id: Date.now() + Math.floor(Math.random() * 1000),
    title: payload.title?.trim() || titleFromInfoName,
    subtitle: payload.subtitle ?? '',
    description: payload.description ?? '',
    category,
    tags: releaseTags,
    status: payload.status ?? 'published',
    sizeBytes: 9800000000,
    infohash: createInfohash(),
    publishedAt: createdAt,
    updatedAt: createdAt,
    createdBy: {
      id: payload.createdBy.id,
      username: payload.createdBy.username,
      displayName: payload.createdBy.displayName,
      role: payload.createdBy.role,
    },
    files: [{ path: innerPath, sizeBytes: 9800000000 }],
    downloadCount: 0,
    completionCount: 0,
    activePeers: 0,
  };

  releases.unshift(release);
  return release;
}

export function updateReleaseData(
  releaseId: number,
  patch: Partial<Pick<Release, 'title' | 'subtitle' | 'description' | 'status'>>,
): Release {
  const release = getReleaseById(releaseId);
  if (!release) {
    throw new Error('资源不存在。');
  }

  Object.assign(release, patch, { updatedAt: nowIso() });
  return release;
}

export function updateReleaseVisibility(releaseId: number, status: 'published' | 'hidden'): Release {
  return updateReleaseData(releaseId, { status });
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
    lastLoginAt: now,
    joinedAt: now,
    createdReleaseCount: 0,
    initialPassword: generatedPassword,
  };
  users.unshift(user);
  userApiTokens[user.id] = createApiToken();
  userThemes[user.id] = defaultTheme();
  return user;
}

function resolveInviteCodeStatus(inviteCode: InviteCode): InviteCode['status'] {
  if (inviteCode.usedAt) return 'used';
  if (!inviteCode.isActive) return 'revoked';
  if (inviteCode.expiresAt && new Date(inviteCode.expiresAt).getTime() <= Date.now()) return 'expired';
  return 'available';
}

function refreshInviteCodeRecord(inviteCode: InviteCode): InviteCode {
  inviteCode.status = resolveInviteCodeStatus(inviteCode);
  inviteCode.canRevoke = inviteCode.status === 'available';
  if (inviteCode.status !== 'available') {
    inviteCode.isActive = false;
  }
  return inviteCode;
}

export function createInviteCodeRecords(payload: CreateInviteCodesPayload): InviteCode[] {
  const createdAt = nowIso();
  const created = Array.from({ length: payload.count }, () =>
    refreshInviteCodeRecord({
      id: Date.now() + Math.floor(Math.random() * 1000),
      code: createInviteCodeValue(),
      note: payload.note?.trim() ?? '',
      status: 'available',
      isActive: true,
      createdByName: users[0]?.displayName ?? '站务系统',
      usedByName: null,
      createdAt,
      usedAt: null,
      expiresAt: payload.expiresAt ?? null,
      canRevoke: true,
    }),
  );

  inviteCodes.unshift(...created);
  return created;
}

export function validateInviteCodeRecord(rawCode: string): InviteCode {
  const normalized = normalizeInviteCode(rawCode);
  const inviteCode = inviteCodes.find((item) => item.code === normalized);

  if (!inviteCode) {
    throw new Error('邀请码不存在。');
  }

  refreshInviteCodeRecord(inviteCode);

  if (inviteCode.status === 'used') {
    throw new Error('邀请码已被使用。');
  }
  if (inviteCode.status === 'expired') {
    throw new Error('邀请码已过期。');
  }
  if (inviteCode.status === 'revoked') {
    throw new Error('邀请码已被停用。');
  }

  return inviteCode;
}

export function consumeInviteCodeRecord(rawCode: string, usedByName?: string | null): InviteCode {
  const inviteCode = validateInviteCodeRecord(rawCode);

  inviteCode.usedAt = nowIso();
  inviteCode.usedByName = usedByName ?? inviteCode.usedByName ?? '新成员';
  inviteCode.isActive = false;
  return refreshInviteCodeRecord(inviteCode);
}

export function revokeInviteCodeRecord(inviteCodeId: number): InviteCode {
  const inviteCode = inviteCodes.find((item) => item.id === inviteCodeId);
  if (!inviteCode) {
    throw new Error('邀请码不存在。');
  }

  refreshInviteCodeRecord(inviteCode);

  if (inviteCode.status === 'used') {
    throw new Error('已使用的邀请码无法停用。');
  }

  inviteCode.isActive = false;
  return refreshInviteCodeRecord(inviteCode);
}

export function toggleUserStatus(userId: number, nextStatus: 'active' | 'disabled'): AdminUser {
  const user = getUserById(userId);
  if (!user) {
    throw new Error('用户不存在。');
  }

  user.status = nextStatus;
  return user;
}

export function saveCategory(payload: Pick<Category, 'name' | 'slug'> & Partial<Category>): Category {
  if (payload.id) {
    const current = categories.find((item) => item.id === payload.id);
    if (!current) {
      throw new Error('分类不存在。');
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
      throw new Error('标签不存在。');
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
      throw new Error('公告不存在。');
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
    loginPageCss: payload.loginPageCss,
    loginNotice: payload.loginNotice,
    allowPublicRegistration: payload.allowPublicRegistration,
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

export function getDashboardStats(): AdminDashboardStats {
  return {
    userCount: users.length,
    releaseCount: releases.length,
    activeReleaseCount: releases.filter((item) => item.status === 'published').length,
    draftReleaseCount: releases.filter((item) => item.status === 'draft').length,
    activeAnnouncementCount: announcements.filter((item) => item.status === 'online').length,
  };
}
