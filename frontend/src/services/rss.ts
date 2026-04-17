import type { RssOverview } from '@/types/admin';
import { apiRequest } from './api';
import { releases, siteSettings } from './mock-data';
import { mockResolve, useMockApi } from './runtime';

export async function getRssOverview(): Promise<RssOverview> {
  if (useMockApi()) {
    return mockResolve(() => {
      const basePath = siteSettings.rssBasePath.replace(/\/$/, '');

      return {
        generalFeed: `${basePath}/all`,
        recentReleaseTitles: releases.slice(0, 4).map((release) => release.title),
      };
    });
  }

  return apiRequest<RssOverview>('/api/rss/overview/');
}
