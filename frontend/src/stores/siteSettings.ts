import { ref } from 'vue';
import { defineStore } from 'pinia';
import { getPublicSiteSettings } from '@/services/admin';
import type { SiteSettings } from '@/types/admin';
import { DEFAULT_LOGIN_BACKGROUND_CSS } from '@/utils/site-branding';

const FAVICON_DEFINITIONS = [
  { id: 'subtitle-group-site-favicon', rel: 'icon' },
  { id: 'subtitle-group-site-shortcut-icon', rel: 'shortcut icon' },
  { id: 'subtitle-group-site-apple-touch-icon', rel: 'apple-touch-icon' },
] as const;
const BLANK_FAVICON_DATA_URI = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22/%3E';
const SITE_SETTINGS_STORAGE_KEY = 'sgds:site-settings';
const SITE_SETTINGS_SIGNAL_KEY = 'sgds:site-settings:signal';
const REFRESH_INTERVAL_MS = 15000;

type SetSettingsOptions = {
  persist?: boolean;
  broadcast?: boolean;
};

function createDefaultSiteSettings(): SiteSettings {
  return {
    siteName: '字幕组分流站',
    siteDescription: '内部资源浏览、下载与 RSS 订阅入口',
    loginNotice: '',
    rssBasePath: '/rss',
    downloadNotice: '',
    siteIconUrl: '',
    siteIconFileUrl: '',
    siteIconResolvedUrl: '',
    loginBackgroundType: 'css',
    loginBackgroundApiUrl: '',
    loginBackgroundFileUrl: '',
    loginBackgroundResolvedUrl: '',
    loginBackgroundCss: DEFAULT_LOGIN_BACKGROUND_CSS,
  };
}

function normalizeSiteSettings(payload?: Partial<SiteSettings>): SiteSettings {
  const defaults = createDefaultSiteSettings();

  return {
    ...defaults,
    ...payload,
    siteName: payload?.siteName?.trim() || defaults.siteName,
    siteDescription: payload?.siteDescription ?? defaults.siteDescription,
    loginNotice: payload?.loginNotice ?? '',
    rssBasePath: payload?.rssBasePath ?? '/rss',
    downloadNotice: payload?.downloadNotice ?? '',
    siteIconUrl: payload?.siteIconUrl ?? '',
    siteIconFileUrl: payload?.siteIconFileUrl ?? '',
    siteIconResolvedUrl: payload?.siteIconResolvedUrl ?? payload?.siteIconFileUrl ?? payload?.siteIconUrl ?? '',
    loginBackgroundType: payload?.loginBackgroundType ?? 'css',
    loginBackgroundApiUrl: payload?.loginBackgroundApiUrl ?? '',
    loginBackgroundFileUrl: payload?.loginBackgroundFileUrl ?? '',
    loginBackgroundResolvedUrl: payload?.loginBackgroundResolvedUrl ?? '',
    loginBackgroundCss: payload?.loginBackgroundCss ?? DEFAULT_LOGIN_BACKGROUND_CSS,
  };
}

function serializeSettings(settings: SiteSettings) {
  return JSON.stringify(settings);
}

function getFaviconType(href: string) {
  const normalized = href.toLowerCase();
  if (normalized.startsWith('data:image/svg+xml')) return 'image/svg+xml';
  if (normalized.includes('.svg')) return 'image/svg+xml';
  if (normalized.includes('.png')) return 'image/png';
  if (normalized.includes('.gif')) return 'image/gif';
  if (normalized.includes('.webp')) return 'image/webp';
  if (normalized.includes('.jpg') || normalized.includes('.jpeg')) return 'image/jpeg';
  return 'image/x-icon';
}

export const useSiteSettingsStore = defineStore('site-settings', () => {
  const settings = ref<SiteSettings>(createDefaultSiteSettings());
  const isLoading = ref(false);
  const lastRouteTitle = ref('');
  const lastLoadedAt = ref(0);

  let loadPromise: Promise<void> | null = null;
  let initialized = false;
  let refreshTimer: number | null = null;
  let broadcastChannel: BroadcastChannel | null = null;

  function buildDocumentTitle(routeTitle?: string) {
    const siteName = settings.value.siteName.trim() || createDefaultSiteSettings().siteName;
    return routeTitle ? `${routeTitle} | ${siteName}` : siteName;
  }

  function applyFavicon() {
    if (typeof document === 'undefined') {
      return;
    }

    const faviconHref = settings.value.siteIconResolvedUrl
      ? (() => {
          const iconUrl = new URL(settings.value.siteIconResolvedUrl, window.location.origin);
          iconUrl.searchParams.set('v', String(lastLoadedAt.value || Date.now()));
          return iconUrl.toString();
        })()
      : BLANK_FAVICON_DATA_URI;

    const faviconType = getFaviconType(faviconHref);
    const existingFavicons = Array.from(
      document.head.querySelectorAll('link[rel~="icon"], link[rel="apple-touch-icon"]'),
    ) as HTMLLinkElement[];

    for (const definition of FAVICON_DEFINITIONS) {
      let favicon =
        (document.getElementById(definition.id) as HTMLLinkElement | null) ??
        existingFavicons.find((item) => item.rel === definition.rel) ??
        null;
      if (!favicon) {
        favicon = document.createElement('link');
        favicon.id = definition.id;
        document.head.appendChild(favicon);
      } else if (!favicon.id) {
        favicon.id = definition.id;
      }

      favicon.rel = definition.rel;
      favicon.href = faviconHref;
      favicon.type = faviconType;
      favicon.sizes = faviconType === 'image/svg+xml' ? 'any' : '';
    }
  }

  function syncDocumentTitle(routeTitle?: string) {
    lastRouteTitle.value = routeTitle ?? '';

    if (typeof document !== 'undefined') {
      document.title = buildDocumentTitle(routeTitle);
    }
  }

  function applyBranding() {
    applyFavicon();
    syncDocumentTitle(lastRouteTitle.value || undefined);
  }

  function persistSettingsSnapshot(nextSettings: SiteSettings) {
    if (typeof window === 'undefined') {
      return;
    }

    const serialized = serializeSettings(nextSettings);
    const previous = window.localStorage.getItem(SITE_SETTINGS_STORAGE_KEY);
    if (previous !== serialized) {
      window.localStorage.setItem(SITE_SETTINGS_STORAGE_KEY, serialized);
      window.localStorage.setItem(SITE_SETTINGS_SIGNAL_KEY, String(Date.now()));
    }
  }

  function broadcastSettingsSnapshot(nextSettings: SiteSettings) {
    if (!broadcastChannel) {
      return;
    }

    broadcastChannel.postMessage(nextSettings);
  }

  function setSettings(nextSettings: Partial<SiteSettings>, options: SetSettingsOptions = {}) {
    const persist = options.persist ?? false;
    const broadcast = options.broadcast ?? false;
    const normalizedSettings = normalizeSiteSettings(nextSettings);

    settings.value = normalizedSettings;
    lastLoadedAt.value = Date.now();
    applyBranding();

    if (persist) {
      persistSettingsSnapshot(normalizedSettings);
    }

    if (broadcast) {
      broadcastSettingsSnapshot(normalizedSettings);
    }
  }

  function publishSettings(nextSettings: Partial<SiteSettings>) {
    setSettings(nextSettings, { persist: true, broadcast: true });
  }

  function resetSettings() {
    settings.value = createDefaultSiteSettings();
    lastLoadedAt.value = 0;
    applyBranding();
  }

  function hydrateFromStorage() {
    if (typeof window === 'undefined') {
      return;
    }

    const raw = window.localStorage.getItem(SITE_SETTINGS_STORAGE_KEY);
    if (!raw) {
      applyBranding();
      return;
    }

    try {
      const payload = JSON.parse(raw) as Partial<SiteSettings>;
      setSettings(payload);
    } catch (error) {
      console.error('Failed to parse cached site settings:', error);
      applyBranding();
    }
  }

  async function loadPublicSettings(force = false) {
    if (loadPromise) {
      return loadPromise;
    }

    isLoading.value = true;
    loadPromise = (async () => {
      try {
        const payload = await getPublicSiteSettings();
        setSettings(payload, { persist: true });
      } catch (error) {
        console.error('Failed to load public site settings:', error);
        if (force && !lastLoadedAt.value) {
          resetSettings();
        } else {
          applyBranding();
        }
      } finally {
        isLoading.value = false;
        loadPromise = null;
      }
    })();

    return loadPromise;
  }

  async function refreshIfVisible(force = false) {
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
      return;
    }

    await loadPublicSettings(force);
  }

  function handleStorageSync(event: StorageEvent) {
    if (event.key !== SITE_SETTINGS_STORAGE_KEY && event.key !== SITE_SETTINGS_SIGNAL_KEY) {
      return;
    }

    if (typeof window === 'undefined') {
      return;
    }

    const raw = window.localStorage.getItem(SITE_SETTINGS_STORAGE_KEY);
    if (!raw) {
      return;
    }

    try {
      const payload = JSON.parse(raw) as Partial<SiteSettings>;
      setSettings(payload);
    } catch (error) {
      console.error('Failed to sync site settings from storage:', error);
    }
  }

  function initialize() {
    if (initialized || typeof window === 'undefined') {
      return;
    }

    initialized = true;
    hydrateFromStorage();

    if (typeof BroadcastChannel !== 'undefined') {
      broadcastChannel = new BroadcastChannel('sgds-site-settings');
      broadcastChannel.addEventListener('message', (event: MessageEvent<Partial<SiteSettings>>) => {
        setSettings(event.data);
      });
    }

    window.addEventListener('storage', handleStorageSync);
    window.addEventListener('focus', () => {
      void refreshIfVisible(true);
    });
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        void refreshIfVisible(true);
      }
    });

    refreshTimer = window.setInterval(() => {
      void refreshIfVisible(true);
    }, REFRESH_INTERVAL_MS);
  }

  return {
    settings,
    isLoading,
    buildDocumentTitle,
    initialize,
    loadPublicSettings,
    publishSettings,
    resetSettings,
    setSettings,
    syncDocumentTitle,
  };
});
