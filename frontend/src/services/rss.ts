import type { RssOverview } from '@/types/admin';
import { apiRequest } from './api';
import { getUserTrackerProfile, releases, siteSettings } from './mock-data';
import { mockResolve, useMockApi } from './runtime';

const SESSION_KEY = 'sgds:session-user-id';

function getStoredSessionId(): number | null {
  const value = window.localStorage.getItem(SESSION_KEY);
  if (!value) return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export async function getRssOverview(): Promise<RssOverview> {
  if (useMockApi()) {
    return mockResolve(() => {
      const basePath = siteSettings.rssBasePath.replace(/\/$/, '');
      const sessionId = getStoredSessionId();
      const personalFeed = sessionId ? `${basePath}/passkey/${getUserTrackerProfile(sessionId).passkey}/all` : '';

      return {
        personalFeed,
        recentReleaseTitles: releases.slice(0, 4).map((release) => release.title),
      };
    });
  }

  return apiRequest<RssOverview>('/api/rss/overview/');
}
