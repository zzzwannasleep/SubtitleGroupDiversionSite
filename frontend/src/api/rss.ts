import type { UserProfile } from "@/types";


export interface RssFeedFilters {
  category?: string;
  keyword?: string;
  sort?: string;
  freeOnly?: boolean;
}


function buildAbsoluteUrl(path: string): string {
  if (typeof window === "undefined") {
    return path;
  }

  return new URL(path, `${window.location.origin}/`).toString();
}


export function buildRssRouteQuery(filters: RssFeedFilters = {}): Record<string, string | undefined> {
  const normalizedKeyword = filters.keyword?.trim() ?? "";

  return {
    keyword: normalizedKeyword || undefined,
    category: filters.category || undefined,
    sort: filters.sort && filters.sort !== "created_at_desc" ? filters.sort : undefined,
    free_only: filters.freeOnly ? "1" : undefined,
  };
}


export function buildRssFeedUrl(profile: UserProfile, filters: RssFeedFilters = {}): string {
  const search = new URLSearchParams();
  search.set("key", profile.rss_key);

  Object.entries(buildRssRouteQuery(filters)).forEach(([key, value]) => {
    if (value) {
      search.set(key, value);
    }
  });

  return buildAbsoluteUrl(`/rss/torrents?${search.toString()}`);
}
