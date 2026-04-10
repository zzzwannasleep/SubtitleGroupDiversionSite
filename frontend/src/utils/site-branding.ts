import type { SiteSettings } from '@/types/admin';

export const DEFAULT_LOGIN_BACKGROUND_CSS =
  'radial-gradient(circle at top left, rgba(96, 165, 250, 0.38), transparent 34%), ' +
  'radial-gradient(circle at 85% 15%, rgba(244, 114, 182, 0.28), transparent 30%), ' +
  'linear-gradient(135deg, #020617 0%, #0f172a 46%, #111827 100%)';

export function buildSiteMonogram(siteName: string) {
  const characters = Array.from(siteName.replace(/\s+/g, '').trim());
  if (!characters.length) {
    return 'SG';
  }

  return characters.slice(0, 2).join('').toUpperCase();
}

export function buildLoginBackgroundStyle(
  settings: Pick<SiteSettings, 'loginBackgroundType' | 'loginBackgroundCss' | 'loginBackgroundResolvedUrl'>,
) {
  if (settings.loginBackgroundType === 'css' && settings.loginBackgroundCss.trim()) {
    return {
      background: settings.loginBackgroundCss,
    };
  }

  if (settings.loginBackgroundResolvedUrl) {
    return {
      backgroundImage: `linear-gradient(135deg, rgba(2, 6, 23, 0.56), rgba(15, 23, 42, 0.84)), url("${settings.loginBackgroundResolvedUrl}")`,
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
      backgroundSize: 'cover',
    };
  }

  return {
    background: DEFAULT_LOGIN_BACKGROUND_CSS,
  };
}
