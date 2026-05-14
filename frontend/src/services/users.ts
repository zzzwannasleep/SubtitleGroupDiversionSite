import type { UserStatsRecord } from '@/types/user-stats';
import { apiRequest, isApiError } from './api';
import { lookupUserStatsRecord } from './mock-data';
import { mockResolve, useMockApi } from './runtime';

export async function lookupUserStats(username: string): Promise<UserStatsRecord | null> {
  const normalizedUsername = username.trim();
  if (!normalizedUsername) {
    throw new Error('请输入要查询的用户名。');
  }

  if (useMockApi()) {
    return mockResolve(() => lookupUserStatsRecord(normalizedUsername));
  }

  try {
    return await apiRequest<UserStatsRecord>('/api/users/stats-lookup/', {
      query: { username: normalizedUsername },
    });
  } catch (error) {
    if (isApiError(error) && error.status === 404) {
      return null;
    }
    throw error;
  }
}
