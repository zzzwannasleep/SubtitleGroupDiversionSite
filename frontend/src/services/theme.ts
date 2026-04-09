import type { SiteTheme } from '@/types/theme';
import { apiRequest, isApiError } from './api';
import { getThemeRecord, saveThemeRecord } from './mock-data';
import { mockResolve, useMockApi } from './runtime';

const SESSION_KEY = 'sgds:session-user-id';

function getStoredSessionId(): number | null {
  if (typeof window === 'undefined') return null;

  const value = window.localStorage.getItem(SESSION_KEY);
  if (!value) return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export async function getMyTheme(): Promise<SiteTheme | null> {
  if (useMockApi()) {
    return mockResolve(() => {
      const userId = getStoredSessionId();
      if (!userId) return null;
      return getThemeRecord(userId);
    });
  }

  try {
    return await apiRequest<SiteTheme>('/api/me/theme/');
  } catch (error) {
    if (isApiError(error) && (error.status === 401 || error.status === 403 || error.status === 404)) {
      return null;
    }
    throw error;
  }
}

export async function saveMyTheme(payload: SiteTheme): Promise<SiteTheme> {
  if (useMockApi()) {
    return mockResolve(() => {
      const userId = getStoredSessionId();
      if (!userId) {
        throw new Error('当前未登录');
      }

      return saveThemeRecord(userId, payload);
    });
  }

  return apiRequest<SiteTheme>('/api/me/theme/', {
    method: 'PUT',
    body: payload,
  });
}
