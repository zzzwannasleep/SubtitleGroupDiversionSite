import type { CurrentUser } from './auth';

export interface UserStatsRecord extends CurrentUser {
  uploadedBytes: number;
  downloadedBytes: number;
  shareRatio: number | null;
  seedingCount: number;
  seedingSizeBytes: number;
  downloadCount: number;
  createdReleaseCount: number;
  createdReleaseSizeBytes: number;
}
