import type { TrackerSyncLog } from '@/types/admin';
import { mockRequest } from './api';
import { appendTrackerSyncLog, trackerSyncLogs } from './mock-data';

export async function listTrackerSyncLogs(): Promise<TrackerSyncLog[]> {
  return mockRequest(() => trackerSyncLogs);
}

export async function runFullTrackerSync(): Promise<TrackerSyncLog> {
  return mockRequest(() =>
    appendTrackerSyncLog({
      scope: 'full',
      targetName: '全量同步',
      status: 'success',
      message: '已按用户状态和资源白名单重新写入 XBT',
    }),
  );
}

