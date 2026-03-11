import type { UserProfile } from "@/types";


export function buildRssLinks(profile: UserProfile): { name: string; url: string }[] {
  return [
    {
      name: "All Torrents",
      url: `/rss/torrents?key=${profile.rss_key}`,
    },
  ];
}

