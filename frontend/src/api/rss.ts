import type { Category, UserProfile } from "@/types";


interface RssLinkOptions {
  allTorrentsLabel?: string;
  categoryFeedName?: (categoryName: string) => string;
}

export function buildRssLinks(
  profile: UserProfile,
  categories: Category[] = [],
  options: RssLinkOptions = {},
): { name: string; url: string }[] {
  return [
    {
      name: options.allTorrentsLabel ?? "All Torrents",
      url: `/rss/torrents?key=${profile.rss_key}`,
    },
    ...categories.map((category) => ({
      name: options.categoryFeedName?.(category.name) ?? `${category.name} Feed`,
      url: `/rss/category/${category.slug}?key=${profile.rss_key}`,
    })),
  ];
}
