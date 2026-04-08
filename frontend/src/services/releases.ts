import type { CurrentUser } from '@/types/auth';
import type { DownloadRecord, PagedResult, Release, ReleaseFormPayload, ReleaseQuery } from '@/types/release';
import { mockRequest } from './api';
import {
  categories,
  createReleaseFromPayload,
  downloadLogs,
  releases,
  tags,
  updateReleaseData,
  updateReleaseVisibility,
} from './mock-data';

function applyQuery(items: Release[], query: ReleaseQuery = {}): PagedResult<Release> {
  const keyword = query.q?.trim().toLowerCase();
  const page = query.page ?? 1;
  const pageSize = query.pageSize ?? 5;
  let results = [...items];

  if (keyword) {
    results = results.filter((item) =>
      [item.title, item.subtitle, item.description].some((field) => field.toLowerCase().includes(keyword)),
    );
  }

  if (query.category) {
    results = results.filter((item) => item.category.slug === query.category);
  }

  if (query.tag) {
    results = results.filter((item) => item.tags.some((tag) => tag.slug === query.tag));
  }

  if (query.ownerId) {
    results = results.filter((item) => item.createdBy.id === query.ownerId);
  }

  if (query.status && query.status !== 'all') {
    results = results.filter((item) => item.status === query.status);
  }

  if (query.sort === 'downloads') {
    results.sort((left, right) => right.downloadCount - left.downloadCount);
  } else if (query.sort === 'completions') {
    results.sort((left, right) => right.completionCount - left.completionCount);
  } else {
    results.sort((left, right) => +new Date(right.publishedAt) - +new Date(left.publishedAt));
  }

  const start = (page - 1) * pageSize;

  return {
    count: results.length,
    page,
    pageSize,
    results: results.slice(start, start + pageSize),
  };
}

export async function listReleases(query: ReleaseQuery = {}): Promise<PagedResult<Release>> {
  return mockRequest(() => applyQuery(releases.filter((item) => item.status !== 'hidden'), query));
}

export async function listAdminReleases(query: ReleaseQuery = {}): Promise<PagedResult<Release>> {
  return mockRequest(() => applyQuery(releases, query));
}

export async function getReleaseById(releaseId: number): Promise<Release | null> {
  return mockRequest(() => releases.find((item) => item.id === releaseId) ?? null);
}

export async function getHomeData(): Promise<{
  latestReleases: Release[];
  categories: typeof categories;
  tags: typeof tags;
}> {
  return mockRequest(() => ({
    latestReleases: releases.filter((item) => item.status === 'published').slice(0, 5),
    categories,
    tags,
  }));
}

export async function listCategories() {
  return mockRequest(() => categories);
}

export async function listTags() {
  return mockRequest(() => tags);
}

export async function listMyReleases(userId: number): Promise<Release[]> {
  return mockRequest(() => releases.filter((item) => item.createdBy.id === userId));
}

export async function listMyDownloads(userId: number): Promise<DownloadRecord[]> {
  return mockRequest(() => downloadLogs.filter((item) => item.downloaderId === userId));
}

export async function createRelease(payload: ReleaseFormPayload, user: CurrentUser): Promise<Release> {
  return mockRequest(() =>
    createReleaseFromPayload({
      ...payload,
      createdBy: user,
      status: payload.status ?? 'published',
    }),
  );
}

export async function editRelease(releaseId: number, payload: ReleaseFormPayload): Promise<Release> {
  return mockRequest(() =>
    updateReleaseData(releaseId, {
      title: payload.title,
      subtitle: payload.subtitle,
      description: payload.description,
      status: payload.status ?? 'published',
    }),
  );
}

export async function toggleReleaseStatus(releaseId: number, nextStatus: 'published' | 'hidden'): Promise<Release> {
  return mockRequest(() => updateReleaseVisibility(releaseId, nextStatus));
}

