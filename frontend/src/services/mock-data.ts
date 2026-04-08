import type { CurrentUser } from '@/types/auth';
import type {
  AdminDashboardStats,
  AdminUser,
  Announcement,
  AuditLog,
  SiteSettings,
  TrackerSyncLog,
} from '@/types/admin';
import type { Category, DownloadRecord, Release, Tag } from '@/types/release';

const createPasskey = () => Math.random().toString(36).slice(2).padEnd(32, 'x').slice(0, 32);

export const categories: Category[] = [
  { id: 1, name: '动画', slug: 'anime', sortOrder: 1, isActive: true },
  { id: 2, name: '日剧', slug: 'jdrama', sortOrder: 2, isActive: true },
  { id: 3, name: '综艺', slug: 'variety', sortOrder: 3, isActive: true },
  { id: 4, name: '纪录片', slug: 'documentary', sortOrder: 4, isActive: true },
];

export const tags: Tag[] = [
  { id: 1, name: '1080p', slug: '1080p' },
  { id: 2, name: '简中', slug: 'chs' },
  { id: 3, name: '繁中', slug: 'cht' },
  { id: 4, name: '双语', slug: 'bilingual' },
  { id: 5, name: '合集', slug: 'collection' },
  { id: 6, name: '完结', slug: 'finished' },
  { id: 7, name: 'WEB-DL', slug: 'web-dl' },
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
    lastLoginAt: '2026-04-08T14:20:00+08:00',
    joinedAt: '2025-11-15T10:00:00+08:00',
    createdReleaseCount: 8,
  },
  {
    id: 2,
    username: 'uploader',
    displayName: '片源搬运组',
    email: 'uploader@subtitle.local',
    role: 'uploader',
    status: 'active',
    passkey: createPasskey(),
    lastLoginAt: '2026-04-08T13:40:00+08:00',
    joinedAt: '2025-12-01T09:10:00+08:00',
    createdReleaseCount: 14,
  },
  {
    id: 3,
    username: 'user',
    displayName: '普通成员',
    email: 'user@subtitle.local',
    role: 'user',
    status: 'active',
    passkey: createPasskey(),
    lastLoginAt: '2026-04-08T11:10:00+08:00',
    joinedAt: '2026-01-03T11:10:00+08:00',
    createdReleaseCount: 0,
  },
  {
    id: 4,
    username: 'akari',
    displayName: '灯',
    email: 'akari@subtitle.local',
    role: 'uploader',
    status: 'active',
    passkey: createPasskey(),
    lastLoginAt: '2026-04-07T23:10:00+08:00',
    joinedAt: '2026-01-13T20:20:00+08:00',
    createdReleaseCount: 4,
  },
  {
    id: 5,
    username: 'watcher',
    displayName: '巡检员',
    email: 'watcher@subtitle.local',
    role: 'user',
    status: 'disabled',
    passkey: createPasskey(),
    lastLoginAt: '2026-04-05T19:40:00+08:00',
    joinedAt: '2026-02-10T18:00:00+08:00',
    createdReleaseCount: 0,
  },
];

const summary = (userId: number) => {
  const user = users.find((item) => item.id === userId)!;
  return { id: user.id, username: user.username, displayName: user.displayName, role: user.role };
};

export const releases: Release[] = [
  {
    id: 101,
    title: '孤独摇滚！TV 01-12 合集',
    subtitle: 'BDRip 1080p 简繁内封',
    description: '重封装合集版本，用来覆盖首页、详情页与 RSS 场景。',
    category: categories[0],
    tags: [tags[0], tags[1], tags[2], tags[4], tags[5]],
    status: 'published',
    sizeBytes: 38_420_000_000,
    infohash: '4df4010a4af5f6082705df0ea5c79d0fceba9f10',
    publishedAt: '2026-04-08T10:15:00+08:00',
    updatedAt: '2026-04-08T10:40:00+08:00',
    createdBy: summary(2),
    downloadCount: 74,
    completionCount: 23,
    activePeers: 9,
    files: [
      { path: '[SubGroup]/Bocchi/S01E01.mkv', sizeBytes: 3_120_000_000 },
      { path: '[SubGroup]/Bocchi/S01E12.mkv', sizeBytes: 3_250_000_000 },
    ],
  },
  {
    id: 102,
    title: 'Last Mile 电影版',
    subtitle: 'WEB-DL 1080p 双语字幕',
    description: '电影类资源样例。',
    category: categories[1],
    tags: [tags[0], tags[3], tags[6]],
    status: 'published',
    sizeBytes: 8_420_000_000,
    infohash: '2f14010a4af5f6082705df0ea5c79d0fceba9f98',
    publishedAt: '2026-04-07T19:20:00+08:00',
    updatedAt: '2026-04-07T19:22:00+08:00',
    createdBy: summary(4),
    downloadCount: 46,
    completionCount: 17,
    activePeers: 7,
    files: [{ path: 'Last.Mile.2026.1080p.WEB-DL.mkv', sizeBytes: 8_420_000_000 }],
  },
  {
    id: 103,
    title: '有吉木曜夜会 2026.04.03',
    subtitle: '录制版 1080p 简中',
    description: '综艺单集样例。',
    category: categories[2],
    tags: [tags[0], tags[1]],
    status: 'published',
    sizeBytes: 4_050_000_000,
    infohash: '3a64010a4af5f6082705df0ea5c79d0fceba9f77',
    publishedAt: '2026-04-06T22:05:00+08:00',
    updatedAt: '2026-04-06T22:09:00+08:00',
    createdBy: summary(2),
    downloadCount: 32,
    completionCount: 11,
    activePeers: 5,
    files: [{ path: 'Ariyoshi.Mokuyou.20260403.ts', sizeBytes: 4_050_000_000 }],
  },
  {
    id: 104,
    title: '深海列车 第二季',
    subtitle: 'TVRip 1080p 简中',
    description: '草稿状态样例。',
    category: categories[1],
    tags: [tags[0], tags[1]],
    status: 'draft',
    sizeBytes: 15_500_000_000,
    infohash: '6b94010a4af5f6082705df0ea5c79d0fceba9f44',
    publishedAt: '2026-04-05T13:10:00+08:00',
    updatedAt: '2026-04-05T13:18:00+08:00',
    createdBy: summary(2),
    downloadCount: 0,
    completionCount: 0,
    activePeers: 0,
    files: [{ path: 'Deep.Sea.Train.S02E01.mkv', sizeBytes: 3_700_000_000 }],
  },
  {
    id: 105,
    title: '极地摄制组：冰原一年',
    subtitle: '纪录片合集 1080p 双语',
    description: '详情页文件列表样例。',
    category: categories[3],
    tags: [tags[0], tags[3], tags[4]],
    status: 'published',
    sizeBytes: 20_600_000_000,
    infohash: '1e14010a4af5f6082705df0ea5c79d0fceba9f31',
    publishedAt: '2026-04-04T09:00:00+08:00',
    updatedAt: '2026-04-04T09:22:00+08:00',
    createdBy: summary(4),
    downloadCount: 28,
    completionCount: 8,
    activePeers: 3,
    files: [{ path: 'Polar.Crew/S01E01.mkv', sizeBytes: 5_200_000_000 }],
  },
  {
    id: 106,
    title: '片场补档：春季新番打包',
    subtitle: '归档用途 隐藏条目',
    description: '后台资源管理页隐藏状态样例。',
    category: categories[0],
    tags: [tags[4], tags[5]],
    status: 'hidden',
    sizeBytes: 52_000_000_000,
    infohash: '7f14010a4af5f6082705df0ea5c79d0fceba9f24',
    publishedAt: '2026-04-02T17:30:00+08:00',
    updatedAt: '2026-04-08T08:15:00+08:00',
    createdBy: summary(1),
    downloadCount: 11,
    completionCount: 4,
    activePeers: 0,
    files: [{ path: 'Archive/Spring/Title-01.mkv', sizeBytes: 6_000_000_000 }],
  },
];

export const downloadLogs: DownloadRecord[] = [
  { id: 9001, releaseId: 101, releaseTitle: '孤独摇滚！TV 01-12 合集', downloadedAt: '2026-04-08T11:03:00+08:00', downloaderId: 3, downloaderName: '普通成员' },
  { id: 9002, releaseId: 102, releaseTitle: 'Last Mile 电影版', downloadedAt: '2026-04-08T09:38:00+08:00', downloaderId: 3, downloaderName: '普通成员' },
  { id: 9003, releaseId: 105, releaseTitle: '极地摄制组：冰原一年', downloadedAt: '2026-04-07T20:12:00+08:00', downloaderId: 2, downloaderName: '片源搬运组' },
];

export const announcements: Announcement[] = [
  { id: 1, title: '本周下载器推荐设置', content: 'qBittorrent 请保持 DHT/PEX 关闭。', status: 'online', audience: 'all', updatedAt: '2026-04-08T09:00:00+08:00' },
  { id: 2, title: '上传前请检查 private 标记', content: '新发布 torrent 必须为 private=1。', status: 'online', audience: 'uploader', updatedAt: '2026-04-07T18:30:00+08:00' },
  { id: 3, title: '维护窗口通知', content: '周五凌晨会做一次 XBT 全量补偿同步。', status: 'draft', audience: 'admin', updatedAt: '2026-04-06T21:50:00+08:00' },
];

export const trackerSyncLogs: TrackerSyncLog[] = [
  { id: 1, scope: 'full', targetName: '全量同步', status: 'success', message: 'xbt_users 与 xbt_files 已完成比对', updatedAt: '2026-04-08T08:20:00+08:00' },
  { id: 2, scope: 'release', targetName: '孤独摇滚！TV 01-12 合集', status: 'success', message: '白名单已写入 XBT', updatedAt: '2026-04-08T10:16:00+08:00' },
  { id: 3, scope: 'user', targetName: 'watcher', status: 'failed', message: '禁用状态同步超时，等待重试', updatedAt: '2026-04-07T22:10:00+08:00' },
];

export const auditLogs: AuditLog[] = [
  { id: 1, actorName: '站务总控', action: '重置 passkey', targetType: '用户', targetName: 'watcher', createdAt: '2026-04-07T22:00:00+08:00', detail: '因疑似泄露执行重置。' },
  { id: 2, actorName: '片源搬运组', action: '发布资源', targetType: '资源', targetName: '孤独摇滚！TV 01-12 合集', createdAt: '2026-04-08T10:15:00+08:00', detail: '上传 torrent 并补充说明。' },
  { id: 3, actorName: '站务总控', action: '隐藏资源', targetType: '资源', targetName: '片场补档：春季新番打包', createdAt: '2026-04-08T08:15:00+08:00', detail: '归档完成，前台隐藏入口。' },
];

export const siteSettings: SiteSettings = {
  siteName: '字幕组分流站',
  siteDescription: '内部资源浏览、下载与 RSS 订阅入口',
  loginNotice: '仅限内部成员使用，不开放公开注册。',
  rssBasePath: 'https://tracker.subtitle.local/rss',
  downloadNotice: '种子文件包含个人身份信息，请勿外传。',
};

export function getUserById(userId: number): AdminUser | undefined {
  return users.find((item) => item.id === userId);
}

export function getUserByUsername(username: string): AdminUser | undefined {
  return users.find((item) => item.username.toLowerCase() === username.toLowerCase());
}

export function resetPasskey(userId: number): AdminUser {
  const user = getUserById(userId);
  if (!user) throw new Error('用户不存在');
  user.passkey = createPasskey();
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
  const now = new Date().toISOString();
  const release: Release = {
    id: Date.now(),
    title: payload.title,
    subtitle: payload.subtitle,
    description: payload.description,
    category,
    tags: releaseTags,
    status: payload.status ?? 'published',
    sizeBytes: 9_800_000_000,
    infohash: createPasskey().slice(0, 32),
    publishedAt: now,
    updatedAt: now,
    createdBy: {
      id: payload.createdBy.id,
      username: payload.createdBy.username,
      displayName: payload.createdBy.displayName,
      role: payload.createdBy.role,
    },
    downloadCount: 0,
    completionCount: 0,
    activePeers: 0,
    files: [{ path: payload.torrentFileName ?? 'new-upload.torrent', sizeBytes: 9_800_000_000 }],
  };
  releases.unshift(release);
  return release;
}

export function updateReleaseData(
  releaseId: number,
  patch: Partial<Pick<Release, 'title' | 'subtitle' | 'description' | 'status'>>,
): Release {
  const release = releases.find((item) => item.id === releaseId);
  if (!release) throw new Error('资源不存在');
  Object.assign(release, patch, { updatedAt: new Date().toISOString() });
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
}): AdminUser {
  const user: AdminUser = {
    id: Date.now(),
    username: payload.username,
    displayName: payload.displayName,
    email: payload.email,
    role: payload.role,
    status: 'active',
    passkey: createPasskey(),
    lastLoginAt: new Date().toISOString(),
    joinedAt: new Date().toISOString(),
    createdReleaseCount: 0,
  };
  users.unshift(user);
  return user;
}

export function toggleUserStatus(userId: number, nextStatus: 'active' | 'disabled'): AdminUser {
  const user = getUserById(userId);
  if (!user) throw new Error('用户不存在');
  user.status = nextStatus;
  return user;
}

export function saveCategory(payload: Pick<Category, 'name' | 'slug'> & Partial<Category>): Category {
  if (payload.id) {
    const current = categories.find((item) => item.id === payload.id);
    if (!current) throw new Error('分类不存在');
    Object.assign(current, payload);
    return current;
  }
  const item: Category = { id: Date.now(), name: payload.name, slug: payload.slug, sortOrder: categories.length + 1, isActive: true };
  categories.push(item);
  return item;
}

export function saveTag(payload: Pick<Tag, 'name' | 'slug'> & Partial<Tag>): Tag {
  if (payload.id) {
    const current = tags.find((item) => item.id === payload.id);
    if (!current) throw new Error('标签不存在');
    Object.assign(current, payload);
    return current;
  }
  const item: Tag = { id: Date.now(), name: payload.name, slug: payload.slug };
  tags.push(item);
  return item;
}

export function saveAnnouncement(payload: Pick<Announcement, 'title' | 'content' | 'status' | 'audience'> & Partial<Announcement>): Announcement {
  if (payload.id) {
    const current = announcements.find((item) => item.id === payload.id);
    if (!current) throw new Error('公告不存在');
    Object.assign(current, payload, { updatedAt: new Date().toISOString() });
    return current;
  }
  const item: Announcement = { id: Date.now(), title: payload.title, content: payload.content, status: payload.status, audience: payload.audience, updatedAt: new Date().toISOString() };
  announcements.unshift(item);
  return item;
}

export function saveSettings(payload: SiteSettings): SiteSettings {
  Object.assign(siteSettings, payload);
  return siteSettings;
}

export function appendAuditLog(action: Omit<AuditLog, 'id' | 'createdAt'>): AuditLog {
  const item: AuditLog = { id: Date.now(), createdAt: new Date().toISOString(), ...action };
  auditLogs.unshift(item);
  return item;
}

export function appendTrackerSyncLog(log: Omit<TrackerSyncLog, 'id' | 'updatedAt'>): TrackerSyncLog {
  const item: TrackerSyncLog = { id: Date.now(), updatedAt: new Date().toISOString(), ...log };
  trackerSyncLogs.unshift(item);
  return item;
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
