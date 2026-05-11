export interface SelfTrackerProfile {
  enabled: boolean;
  authMode: string;
  announceUrl: string;
  scrapeUrl: string;
  passkey: string;
  keyValidUntil: string | null;
  requireAuthDownloads: boolean;
  forcePrivateTorrents: boolean;
}

export interface TrackerApiStats {
  torrents: number;
  seeders: number;
  leechers: number;
  completed: number;
  announcesHandled: number;
  scrapesHandled: number;
}

export interface AdminTrackerOverview {
  enabled: boolean;
  trackerReachable: boolean;
  trackerMessage: string;
  authMode: string;
  announceUrl: string;
  scrapeUrl: string;
  requireAuthDownloads: boolean;
  forcePrivateTorrents: boolean;
  userCount: number;
  activeUserCount: number;
  userKeysProvisioned: number;
  releaseSyncCount: number;
  publishedReleaseCount: number;
  whitelistedReleaseCount: number;
  syncErrorCount: number;
  latestSyncAt: string | null;
  latestScrapeAt: string | null;
  trackerStats: TrackerApiStats | null;
}

export interface AdminTrackerSyncPayload {
  syncUsers?: boolean;
  syncReleases?: boolean;
  syncScrape?: boolean;
}

export interface AdminTrackerSyncResult {
  usersProcessed: number;
  usersFailed: number;
  releasesProcessed: number;
  releasesFailed: number;
  scrapesProcessed: number;
  scrapesFailed: number;
  errors: string[];
}
