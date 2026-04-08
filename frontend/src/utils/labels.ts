import type { AnnouncementStatus, SyncStatus, XbtUserState } from '@/types/admin';
import type { UserRole, UserStatus } from '@/types/auth';
import type { ReleaseStatus, XbtFileState } from '@/types/release';

export const roleLabels: Record<UserRole, string> = {
  admin: '管理员',
  uploader: '上传者',
  user: '普通用户',
};

export const userStatusLabels: Record<UserStatus, string> = {
  active: '正常',
  disabled: '已禁用',
};

export const releaseStatusLabels: Record<ReleaseStatus, string> = {
  published: '已发布',
  draft: '草稿',
  hidden: '已隐藏',
};

export const syncStatusLabels: Record<SyncStatus, string> = {
  success: '成功',
  warning: '警告',
  failed: '失败',
};

export const announcementStatusLabels: Record<AnnouncementStatus, string> = {
  online: '上线',
  draft: '草稿',
  offline: '下线',
};

export const audienceLabels: Record<'all' | 'uploader' | 'admin', string> = {
  all: '全部用户',
  uploader: '上传者',
  admin: '管理员',
};

export const trackerScopeLabels: Record<'user' | 'release' | 'full', string> = {
  user: '用户',
  release: '资源',
  full: '全量',
};

export const xbtUserStateLabels: Record<XbtUserState, string> = {
  enabled: '已启用',
  disabled: '已禁用',
  missing: '未写入',
  unavailable: '不可用',
};

export const xbtFileStateLabels: Record<XbtFileState, string> = {
  whitelisted: '已白名单',
  deleted: '已移除',
  missing: '未写入',
  unavailable: '不可用',
};
