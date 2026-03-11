export type AuthThemePresetId = "control" | "ledger" | "signal";

export interface AuthThemePreset {
  id: AuthThemePresetId;
  labelKey: string;
  descriptionKey: string;
  variables: Record<string, string>;
}

export const AUTH_THEME_PRESETS: AuthThemePreset[] = [
  {
    id: "control",
    labelKey: "auth.themePresets.control.label",
    descriptionKey: "auth.themePresets.control.description",
    variables: {
      "--auth-bg": "#07111f",
      "--auth-bg-soft": "#10233f",
      "--auth-surface": "rgba(8, 16, 30, 0.74)",
      "--auth-surface-elevated": "rgba(12, 23, 42, 0.92)",
      "--auth-border": "rgba(148, 163, 184, 0.18)",
      "--auth-text": "#e2e8f0",
      "--auth-text-muted": "#94a3b8",
      "--auth-accent": "#38bdf8",
      "--auth-accent-soft": "rgba(56, 189, 248, 0.16)",
      "--auth-grid": "rgba(148, 163, 184, 0.12)",
      "--auth-shadow": "0 30px 80px rgba(2, 6, 23, 0.42)",
      "--auth-input-bg": "rgba(15, 23, 42, 0.68)",
      "--auth-spotlight-a": "rgba(56, 189, 248, 0.22)",
      "--auth-spotlight-b": "rgba(14, 165, 233, 0.12)",
      "--auth-image-overlay-top": "rgba(4, 10, 22, 0.52)",
      "--auth-image-overlay-bottom": "rgba(4, 10, 22, 0.2)",
    },
  },
  {
    id: "ledger",
    labelKey: "auth.themePresets.ledger.label",
    descriptionKey: "auth.themePresets.ledger.description",
    variables: {
      "--auth-bg": "#f5efe3",
      "--auth-bg-soft": "#eadcc3",
      "--auth-surface": "rgba(255, 252, 247, 0.78)",
      "--auth-surface-elevated": "rgba(255, 255, 255, 0.94)",
      "--auth-border": "rgba(120, 53, 15, 0.16)",
      "--auth-text": "#3b2417",
      "--auth-text-muted": "#7c5d46",
      "--auth-accent": "#a16207",
      "--auth-accent-soft": "rgba(161, 98, 7, 0.12)",
      "--auth-grid": "rgba(120, 53, 15, 0.08)",
      "--auth-shadow": "0 26px 60px rgba(120, 53, 15, 0.12)",
      "--auth-input-bg": "rgba(255, 255, 255, 0.9)",
      "--auth-spotlight-a": "rgba(202, 138, 4, 0.16)",
      "--auth-spotlight-b": "rgba(120, 53, 15, 0.1)",
      "--auth-image-overlay-top": "rgba(255, 255, 255, 0.3)",
      "--auth-image-overlay-bottom": "rgba(255, 255, 255, 0.1)",
    },
  },
  {
    id: "signal",
    labelKey: "auth.themePresets.signal.label",
    descriptionKey: "auth.themePresets.signal.description",
    variables: {
      "--auth-bg": "#07130e",
      "--auth-bg-soft": "#11261d",
      "--auth-surface": "rgba(7, 19, 14, 0.78)",
      "--auth-surface-elevated": "rgba(11, 28, 21, 0.92)",
      "--auth-border": "rgba(134, 239, 172, 0.16)",
      "--auth-text": "#dcfce7",
      "--auth-text-muted": "#86efac",
      "--auth-accent": "#22c55e",
      "--auth-accent-soft": "rgba(34, 197, 94, 0.16)",
      "--auth-grid": "rgba(134, 239, 172, 0.08)",
      "--auth-shadow": "0 30px 80px rgba(2, 6, 23, 0.34)",
      "--auth-input-bg": "rgba(12, 28, 21, 0.7)",
      "--auth-spotlight-a": "rgba(34, 197, 94, 0.16)",
      "--auth-spotlight-b": "rgba(16, 185, 129, 0.12)",
      "--auth-image-overlay-top": "rgba(4, 10, 22, 0.42)",
      "--auth-image-overlay-bottom": "rgba(4, 10, 22, 0.14)",
    },
  },
];

export const DEFAULT_AUTH_THEME_PRESET_ID: AuthThemePresetId = "control";

const presetMap = new Map(AUTH_THEME_PRESETS.map((preset) => [preset.id, preset]));

export function resolveAuthThemePreset(id: string | undefined): AuthThemePreset {
  return presetMap.get(id as AuthThemePresetId) ?? presetMap.get(DEFAULT_AUTH_THEME_PRESET_ID)!;
}
