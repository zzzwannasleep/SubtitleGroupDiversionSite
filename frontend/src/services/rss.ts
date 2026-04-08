import type { CurrentUser } from '@/types/auth';
import type { RssOverview } from '@/types/admin';
import { apiRequest } from './api';
import { categories, releases, tags } from './mock-data';
import { mockResolve, useMockApi } from './runtime';

export async function getRssOverview(_user: CurrentUser): Promise<RssOverview> {
  if (useMockApi()) {
    return mockResolve(() => ({
      generalFeed: `https://tracker.subtitle.local/rss/all?passkey=${_user.passkey}`,
      categoryFeeds: categories.map((category) => ({
        label: category.name,
        url: `https://tracker.subtitle.local/rss/category/${category.slug}?passkey=${_user.passkey}`,
      })),
      tagFeeds: tags.slice(0, 5).map((tag) => ({
        label: tag.name,
        url: `https://tracker.subtitle.local/rss/tag/${tag.slug}?passkey=${_user.passkey}`,
      })),
      recentReleaseTitles: releases.slice(0, 4).map((release) => release.title),
    }));
  }

  return apiRequest<RssOverview>('/api/rss/overview/');
}
