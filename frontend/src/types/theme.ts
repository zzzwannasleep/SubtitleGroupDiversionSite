export type ThemeMode = 'system' | 'light' | 'dark';

export interface SiteTheme {
  mode: ThemeMode;
  customCss: string;
}
