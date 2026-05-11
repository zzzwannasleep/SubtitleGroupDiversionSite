import { apiRequest } from './api';
import { getTrackerOverview, getUserTrackerProfile, runTrackerSyncMock } from './mock-data';
import { mockResolve, useMockApi } from './runtime';
import type {
  AdminTrackerOverview,
  AdminTrackerSyncPayload,
  AdminTrackerSyncResult,
  SelfTrackerProfile,
} from '@/types/tracker';

const SESSION_KEY = 'sgds:session-user-id';

function getStoredSessionId(): number | null {
  const value = window.localStorage.getItem(SESSION_KEY);
  if (!value) return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export async function getMyTrackerProfile(): Promise<SelfTrackerProfile> {
  if (useMockApi()) {
    return mockResolve(() => {
      const sessionId = getStoredSessionId();
      if (!sessionId) {
        throw new Error('当前未登录。');
      }
      return getUserTrackerProfile(sessionId);
    });
  }

  return apiRequest<SelfTrackerProfile>('/api/me/tracker/');
}

export async function getAdminTrackerOverview(): Promise<AdminTrackerOverview> {
  if (useMockApi()) {
    return mockResolve(() => getTrackerOverview());
  }

  return apiRequest<AdminTrackerOverview>('/api/admin/tracker/overview/');
}

export async function runAdminTrackerSync(payload: AdminTrackerSyncPayload = {}): Promise<AdminTrackerSyncResult> {
  if (useMockApi()) {
    return mockResolve(() => runTrackerSyncMock(payload));
  }

  return apiRequest<AdminTrackerSyncResult>('/api/admin/tracker/sync/', {
    method: 'POST',
    body: payload,
  });
}
