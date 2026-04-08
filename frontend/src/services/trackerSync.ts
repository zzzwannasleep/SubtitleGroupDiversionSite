import type { TrackerSyncLog } from '@/types/admin';
import { apiRequest } from './api';

export async function listTrackerSyncLogs(): Promise<TrackerSyncLog[]> {
  return apiRequest<TrackerSyncLog[]>('/api/admin/tracker-sync/logs/');
}

export async function runFullTrackerSync(): Promise<TrackerSyncLog> {
  return apiRequest<TrackerSyncLog>('/api/admin/tracker-sync/full/', {
    method: 'POST',
  });
}
