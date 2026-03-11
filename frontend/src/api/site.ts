import { apiRequest } from "./http";


export interface SiteSettings {
  site_name: string;
}


export function getSiteSettings(): Promise<SiteSettings> {
  return apiRequest<SiteSettings>("/site-settings", {
    auth: false,
  });
}
