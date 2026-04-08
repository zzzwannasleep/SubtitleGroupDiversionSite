import type { CurrentUser } from '@/types/auth';
import type { Category, DownloadRecord, PagedResult, Release, ReleaseFormPayload, ReleaseQuery, Tag } from '@/types/release';
import { apiRequest, buildApiUrl, isApiError } from './api';

interface PaginatedReleaseResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  page: number;
  pageSize: number;
  results: T[];
}

export async function listReleases(query: ReleaseQuery = {}): Promise<PagedResult<Release>> {
  return apiRequest<PaginatedReleaseResponse<Release>>('/api/releases/', { query });
}

export async function listAdminReleases(query: ReleaseQuery = {}): Promise<PagedResult<Release>> {
  return apiRequest<PaginatedReleaseResponse<Release>>('/api/admin/releases/', { query });
}

export async function getReleaseById(releaseId: number): Promise<Release | null> {
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
  return apiRequest('/api/home/');
}

export async function listCategories(): Promise<Category[]> {
  return apiRequest<Category[]>('/api/categories/');
}

export async function listTags(): Promise<Tag[]> {
  return apiRequest<Tag[]>('/api/tags/');
}

export async function listMyReleases(_userId: number): Promise<Release[]> {
  return apiRequest<Release[]>('/api/me/releases/');
}

export async function listMyDownloads(_userId: number): Promise<DownloadRecord[]> {
  return apiRequest<DownloadRecord[]>('/api/me/downloads/');
}

export async function createRelease(payload: ReleaseFormPayload, _user: CurrentUser): Promise<Release> {
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

export async function toggleReleaseStatus(releaseId: number, nextStatus: 'published' | 'hidden'): Promise<Release> {
  return apiRequest<Release>(`/api/releases/${releaseId}/visibility/`, {
    method: 'POST',
    body: { status: nextStatus },
  });
}

export function getReleaseDownloadUrl(releaseId: number) {
  return buildApiUrl(`/api/releases/${releaseId}/download/`);
}

export function downloadRelease(releaseId: number) {
  window.location.assign(getReleaseDownloadUrl(releaseId));
}
