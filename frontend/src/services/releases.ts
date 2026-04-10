import type { CurrentUser } from '@/types/auth';
import type { Category, DownloadRecord, PagedResult, Release, ReleaseFormPayload, ReleaseQuery, Tag } from '@/types/release';
import { apiRequest, buildApiUrl, isApiError } from './api';
import {
  categories,
  createReleaseFromPayload,
  downloadLogs,
  releases,
  tags,
  updateReleaseData,
  updateReleaseVisibility,
} from './mock-data';
import { mockResolve, useMockApi } from './runtime';

interface PaginatedReleaseResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  page: number;
  pageSize: number;
  results: T[];
}

function triggerBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function fallbackTorrentFilename(sourceName: string) {
  const baseName = sourceName.replace(/\.torrent$/i, '') || 'private-torrent';
  return `${baseName}.torrent`;
}

function resolveFilenameFromDisposition(disposition: string | null, fallbackName: string) {
  if (!disposition) {
    return fallbackName;
  }

  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }

  const basicMatch = disposition.match(/filename="?([^"]+)"?/i);
  if (basicMatch?.[1]) {
    return basicMatch[1];
  }

  return fallbackName;
}

async function buildBinaryError(response: Response) {
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    const payload = (await response.json()) as { message?: string };
    return payload.message ?? `请求失败（HTTP ${response.status}）`;
  }

  const payload = (await response.text()).trim();
  return payload || `请求失败（HTTP ${response.status}）`;
}

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
  if (useMockApi()) {
    return mockResolve(() => applyQuery(releases.filter((item) => item.status !== 'hidden'), query));
  }

  return apiRequest<PaginatedReleaseResponse<Release>>('/api/releases/', { query });
}

export async function listAdminReleases(query: ReleaseQuery = {}): Promise<PagedResult<Release>> {
  if (useMockApi()) {
    return mockResolve(() => applyQuery(releases, query));
  }

  return apiRequest<PaginatedReleaseResponse<Release>>('/api/admin/releases/', { query });
}

export async function getReleaseById(releaseId: number): Promise<Release | null> {
  if (useMockApi()) {
    return mockResolve(() => releases.find((item) => item.id === releaseId) ?? null);
  }

  try {
    return await apiRequest<Release>(`/api/releases/${releaseId}/`);
  } catch (error) {
    if (isApiError(error) && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function getHomeData(): Promise<{
  latestReleases: Release[];
  categories: Category[];
  tags: Tag[];
}> {
  if (useMockApi()) {
    return mockResolve(() => ({
      latestReleases: releases.filter((item) => item.status === 'published').slice(0, 5),
      categories,
      tags,
    }));
  }

  return apiRequest('/api/home/');
}

export async function listCategories(): Promise<Category[]> {
  if (useMockApi()) {
    return mockResolve(() => categories);
  }

  return apiRequest<Category[]>('/api/categories/');
}

export async function listTags(): Promise<Tag[]> {
  if (useMockApi()) {
    return mockResolve(() => tags);
  }

  return apiRequest<Tag[]>('/api/tags/');
}

export async function listMyReleases(_userId: number): Promise<Release[]> {
  if (useMockApi()) {
    return mockResolve(() => releases.filter((item) => item.createdBy.id === _userId));
  }

  return apiRequest<Release[]>('/api/me/releases/');
}

export async function listMyDownloads(_userId: number): Promise<DownloadRecord[]> {
  if (useMockApi()) {
    return mockResolve(() => downloadLogs.filter((item) => item.downloaderId === _userId));
  }

  return apiRequest<DownloadRecord[]>('/api/me/downloads/');
}

export async function createRelease(payload: ReleaseFormPayload, _user: CurrentUser): Promise<Release> {
  if (useMockApi()) {
    return mockResolve(() => {
      if (!payload.torrentFile && !payload.torrentFileName) {
        throw new Error('请选择要上传的 .torrent 文件');
      }

      return createReleaseFromPayload({
        title: payload.title,
        subtitle: payload.subtitle,
        description: payload.description,
        categorySlug: payload.categorySlug,
        tagSlugs: payload.tagSlugs,
        torrentFileName: payload.torrentFile?.name ?? payload.torrentFileName,
        createdBy: _user,
        status: payload.status ?? 'published',
      });
    });
  }

  if (!payload.torrentFile) {
    throw new Error('请选择要上传的 .torrent 文件');
  }

  const formData = new FormData();
  formData.set('title', payload.title);
  formData.set('subtitle', payload.subtitle);
  formData.set('description', payload.description);
  formData.set('categorySlug', payload.categorySlug);
  formData.set('status', payload.status ?? 'published');
  formData.set('torrentFile', payload.torrentFile, payload.torrentFile.name);

  for (const tagSlug of payload.tagSlugs) {
    formData.append('tagSlugs', tagSlug);
  }

  return apiRequest<Release>('/api/releases/', {
    method: 'POST',
    body: formData,
  });
}

export async function editRelease(releaseId: number, payload: ReleaseFormPayload): Promise<Release> {
  if (useMockApi()) {
    return mockResolve(() =>
      updateReleaseData(releaseId, {
        title: payload.title,
        subtitle: payload.subtitle,
        description: payload.description,
        status: payload.status ?? 'published',
      }),
    );
  }

  if (payload.torrentFile) {
    const formData = new FormData();
    formData.set('title', payload.title);
    formData.set('subtitle', payload.subtitle);
    formData.set('description', payload.description);
    formData.set('categorySlug', payload.categorySlug);
    formData.set('status', payload.status ?? 'published');
    formData.set('torrentFile', payload.torrentFile, payload.torrentFile.name);

    for (const tagSlug of payload.tagSlugs) {
      formData.append('tagSlugs', tagSlug);
    }

    return apiRequest<Release>(`/api/releases/${releaseId}/`, {
      method: 'PATCH',
      body: formData,
    });
  }

  return apiRequest<Release>(`/api/releases/${releaseId}/`, {
    method: 'PATCH',
    body: {
      title: payload.title,
      subtitle: payload.subtitle,
      description: payload.description,
      categorySlug: payload.categorySlug,
      tagSlugs: payload.tagSlugs,
      status: payload.status ?? 'published',
    },
  });
}

export async function privatizeTorrent(file: File): Promise<string> {
  const fallbackName = fallbackTorrentFilename(file.name);

  if (useMockApi()) {
    triggerBlobDownload(
      new Blob([`Mock private torrent for ${file.name}`], { type: 'application/x-bittorrent' }),
      fallbackName,
    );
    return mockResolve(() => fallbackName);
  }

  const formData = new FormData();
  formData.set('torrentFile', file, file.name);

  const response = await fetch(buildApiUrl('/api/torrents/privatize/'), {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(await buildBinaryError(response));
  }

  const filename = resolveFilenameFromDisposition(response.headers.get('content-disposition'), fallbackName);
  const blob = await response.blob();
  triggerBlobDownload(blob, filename);
  return filename;
}

export async function toggleReleaseStatus(releaseId: number, nextStatus: 'published' | 'hidden'): Promise<Release> {
  if (useMockApi()) {
    return mockResolve(() => updateReleaseVisibility(releaseId, nextStatus));
  }

  return apiRequest<Release>(`/api/releases/${releaseId}/visibility/`, {
    method: 'POST',
    body: { status: nextStatus },
  });
}

export function getReleaseDownloadUrl(releaseId: number) {
  if (useMockApi()) {
    return '#';
  }

  return buildApiUrl(`/api/releases/${releaseId}/download/`);
}

export function downloadRelease(releaseId: number) {
  if (useMockApi()) {
    const release = releases.find((item) => item.id === releaseId);
    const title = release?.title ?? `release-${releaseId}`;
    const blob = new Blob([`Mock torrent for ${title}`], { type: 'application/x-bittorrent' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${title}.torrent`;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    return;
  }

  window.location.assign(getReleaseDownloadUrl(releaseId));
}
