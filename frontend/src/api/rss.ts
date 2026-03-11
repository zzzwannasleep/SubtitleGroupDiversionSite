import type { Category, UserProfile } from "@/types";


export function buildRssLinks(profile: UserProfile, categories: Category[] = []): { name: string; url: string }[] {
  return [
    {
      name: "All Torrents",
      url: `/rss/torrents?key=${profile.rss_key}`,
    },
    ...categories.map((category) => ({
      name: `${category.name} Feed`,
      url: `/rss/category/${category.slug}?key=${profile.rss_key}`,
    })),
  ];
}
