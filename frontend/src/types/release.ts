import type { UserSummary } from './auth';

export type ReleaseStatus = 'draft' | 'published' | 'hidden';
export type ReleaseSort = 'latest' | 'downloads' | 'completions';

export interface Category {
  id: number;
  name: string;
  slug: string;
  sortOrder: number;
  isActive: boolean;
}

export interface Tag {
  id: number;
  name: string;
  slug: string;
}

export interface ReleaseFile {
  path: string;
  sizeBytes: number;
}

export interface WebseedLibraryEntry {
  name: string;
  path: string;
  kind: 'directory' | 'file';
  sizeBytes: number | null;
}

export interface WebseedLibraryListing {
  currentPath: string;
  parentPath: string | null;
  entries: WebseedLibraryEntry[];
}

export interface Release {
  id: number;
  title: string;
  subtitle: string;
  description: string;
  category: Category;
  tags: Tag[];
  status: ReleaseStatus;
  sizeBytes: number;
  infohash: string;
  coverImageUrl?: string;
  publishedAt: string;
  updatedAt: string;
  createdBy: UserSummary;
  files: ReleaseFile[];
  downloadCount: number;
  completionCount: number;
  activePeers: number;
  seederCount: number;
  leecherCount: number;
}

export interface DownloadRecord {
  id: number;
  releaseId: number;
  releaseTitle: string;
  downloadedAt: string;
  downloaderId: number;
  downloaderName: string;
}

export interface ReleaseQuery {
  q?: string;
  category?: string;
  tag?: string;
  sort?: ReleaseSort;
  page?: number;
  pageSize?: number;
  ownerId?: number;
  status?: ReleaseStatus | 'all';
}

export interface PagedResult<T> {
  count: number;
  page: number;
  pageSize: number;
  results: T[];
}

export interface ReleaseFormPayload {
  title?: string;
  subtitle?: string;
  description?: string;
  categorySlug?: string;
  tagSlugs?: string[];
  torrentFile?: File | null;
  torrentFileName?: string;
  webseedFiles?: File[];
  webseedPaths?: string[];
  webseedRootPath?: string;
  clearWebseedFiles?: boolean;
  status?: ReleaseStatus;
}
