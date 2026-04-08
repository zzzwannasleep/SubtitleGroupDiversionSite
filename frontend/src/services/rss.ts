import type { CurrentUser } from '@/types/auth';
import type { RssOverview } from '@/types/admin';
import { apiRequest } from './api';

export async function getRssOverview(_user: CurrentUser): Promise<RssOverview> {
  return apiRequest<RssOverview>('/api/rss/overview/');
}
