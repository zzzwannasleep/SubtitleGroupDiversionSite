import type { TrackerSyncLog } from '@/types/admin';
import { apiRequest } from './api';
import { appendTrackerSyncLog, trackerSyncLogs } from './mock-data';
import { mockResolve, useMockApi } from './runtime';

export async function listTrackerSyncLogs(): Promise<TrackerSyncLog[]> {
  if (useMockApi()) {
    return mockResolve(() => trackerSyncLogs);
  }

  return apiRequest<TrackerSyncLog[]>('/api/admin/tracker-sync/logs/');
}

export async function runFullTrackerSync(): Promise<TrackerSyncLog> {
  if (useMockApi()) {
    return mockResolve(() =>
      appendTrackerSyncLog({
        scope: 'full',
        targetName: '全量同步',
        status: 'success',
        message: '已按用户状态和资源白名单重新写入 XBT',
      }),
    );
  }

  return apiRequest<TrackerSyncLog>('/api/admin/tracker-sync/full/', {
    method: 'POST',
  });
}
