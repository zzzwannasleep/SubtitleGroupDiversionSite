import type { CurrentUser } from '@/types/auth';
import type { RssOverview } from '@/types/admin';
import { apiRequest } from './api';
import { categories, releases, siteSettings, tags } from './mock-data';
import { mockResolve, useMockApi } from './runtime';

export async function getRssOverview(user: CurrentUser): Promise<RssOverview> {
  if (useMockApi()) {
    return mockResolve(() => {
      const basePath = siteSettings.rssBasePath.replace(/\/$/, '');

      return {
        generalFeed: `${basePath}/all?passkey=${user.passkey}`,
        categoryFeeds: categories.map((category) => ({
          label: category.name,
          url: `${basePath}/category/${category.slug}?passkey=${user.passkey}`,
        })),
        tagFeeds: tags.slice(0, 5).map((tag) => ({
          label: tag.name,
          url: `${basePath}/tag/${tag.slug}?passkey=${user.passkey}`,
        })),
        recentReleaseTitles: releases.slice(0, 4).map((release) => release.title),
      };
    });
  }

  return apiRequest<RssOverview>('/api/rss/overview/');
}
