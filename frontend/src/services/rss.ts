import type { CurrentUser } from '@/types/auth';
import type { RssOverview } from '@/types/admin';
import { mockRequest } from './api';
import { categories, releases, tags } from './mock-data';

export async function getRssOverview(user: CurrentUser): Promise<RssOverview> {
  return mockRequest(() => ({
    generalFeed: `https://tracker.subtitle.local/rss/all?passkey=${user.passkey}`,
    categoryFeeds: categories.map((category) => ({
      label: category.name,
      url: `https://tracker.subtitle.local/rss/category/${category.slug}?passkey=${user.passkey}`,
    })),
    tagFeeds: tags.slice(0, 5).map((tag) => ({
      label: tag.name,
      url: `https://tracker.subtitle.local/rss/tag/${tag.slug}?passkey=${user.passkey}`,
    })),
    recentReleaseTitles: releases.slice(0, 4).map((release) => release.title),
  }));
}

