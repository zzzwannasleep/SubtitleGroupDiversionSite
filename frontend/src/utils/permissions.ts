import type { CurrentUser, UserRole } from '@/types/auth';
import type { Release } from '@/types/release';

export function hasRole(user: CurrentUser | null, roles?: UserRole[]): boolean {
  if (!roles?.length) return true;
  if (!user) return false;
  if (user.role === 'admin') return true;
  return roles.includes(user.role);
}

export function canEditRelease(user: CurrentUser | null, release: Release | null | undefined): boolean {
  if (!user || !release) return false;
  if (user.role === 'admin') return true;
  return user.role === 'uploader' && user.id === release.createdBy.id;
}

export function canManageAdmin(user: CurrentUser | null): boolean {
  return user?.role === 'admin';
}

