import type {
  TrackerSyncLog,
  TrackerSyncLogFilters,
  TrackerSyncOverview,
  TrackerSyncReleaseDetail,
  TrackerSyncUserDetail,
} from '@/types/admin';
import { apiRequest, isApiError } from './api';
import {
  getTrackerSyncOverview as getMockTrackerSyncOverview,
  getTrackerSyncReleaseDetail as getMockTrackerSyncReleaseDetail,
  getTrackerSyncUserDetail as getMockTrackerSyncUserDetail,
  listTrackerSyncLogRecords,
  retryTrackerSyncLogById,
  runFullTrackerSyncLog,
  runReleaseTrackerSync,
  runUserTrackerSync,
} from './mock-data';
import { mockResolve, useMockApi } from './runtime';

export async function listTrackerSyncLogs(filters: TrackerSyncLogFilters = {}): Promise<TrackerSyncLog[]> {
  if (useMockApi()) {
    return mockResolve(() => listTrackerSyncLogRecords(filters));
  }

  return apiRequest<TrackerSyncLog[]>('/api/admin/tracker-sync/logs/', {
    query: filters,
  });
}

export async function getTrackerSyncOverview(): Promise<TrackerSyncOverview> {
  if (useMockApi()) {
    return mockResolve(() => getMockTrackerSyncOverview());
  }

  return apiRequest<TrackerSyncOverview>('/api/admin/tracker-sync/overview/');
}

export async function getTrackerSyncUserDetail(userId: number): Promise<TrackerSyncUserDetail | null> {
  if (useMockApi()) {
    return mockResolve(() => getMockTrackerSyncUserDetail(userId));
  }

  try {
    return await apiRequest<TrackerSyncUserDetail>(`/api/admin/tracker-sync/users/${userId}/`);
  } catch (error) {
    if (isApiError(error) && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function runTrackerSyncForUser(userId: number): Promise<TrackerSyncLog> {
  if (useMockApi()) {
    return mockResolve(() => runUserTrackerSync(userId));
  }

  return apiRequest<TrackerSyncLog>(`/api/admin/tracker-sync/users/${userId}/`, {
    method: 'POST',
  });
}

export async function getTrackerSyncReleaseDetail(releaseId: number): Promise<TrackerSyncReleaseDetail | null> {
  if (useMockApi()) {
    return mockResolve(() => getMockTrackerSyncReleaseDetail(releaseId));
  }

  try {
    return await apiRequest<TrackerSyncReleaseDetail>(`/api/admin/tracker-sync/releases/${releaseId}/`);
  } catch (error) {
    if (isApiError(error) && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function runTrackerSyncForRelease(releaseId: number): Promise<TrackerSyncLog> {
  if (useMockApi()) {
    return mockResolve(() => runReleaseTrackerSync(releaseId));
  }

  return apiRequest<TrackerSyncLog>(`/api/admin/tracker-sync/releases/${releaseId}/`, {
    method: 'POST',
  });
}

export async function retryTrackerSyncLog(logId: number): Promise<TrackerSyncLog> {
  if (useMockApi()) {
    return mockResolve(() => retryTrackerSyncLogById(logId));
  }

  return apiRequest<TrackerSyncLog>(`/api/admin/tracker-sync/logs/${logId}/retry/`, {
    method: 'POST',
  });
}

export async function runFullTrackerSync(): Promise<TrackerSyncLog> {
  if (useMockApi()) {
    return mockResolve(() => runFullTrackerSyncLog());
  }

  return apiRequest<TrackerSyncLog>('/api/admin/tracker-sync/full/', {
    method: 'POST',
  });
}
