import { computed, ref, watch } from "vue";
import { defineStore } from "pinia";

import {
  DEFAULT_AUTH_THEME_PRESET_ID,
  type AuthThemePresetId,
  resolveAuthThemePreset,
} from "@/config/authTheme";


const STORAGE_KEY = "pt-platform.appearance";

interface AppearanceState {
  reducedMotion: boolean;
  listDensity: "comfortable" | "compact";
  backgroundMode: "solid" | "image";
  backgroundImageUrl: string;
  authThemePreset: AuthThemePresetId;
  authAccentColor: string;
  authBackgroundImageUrl: string;
}


function defaultState(): AppearanceState {
  const defaultAuthTheme = resolveAuthThemePreset(DEFAULT_AUTH_THEME_PRESET_ID);

  return {
    reducedMotion: false,
    listDensity: "comfortable",
    backgroundMode: "solid",
    backgroundImageUrl: "",
    authThemePreset: DEFAULT_AUTH_THEME_PRESET_ID,
    authAccentColor: defaultAuthTheme.variables["--auth-accent"],
    authBackgroundImageUrl: "",
  };
}


function readInitialState(): AppearanceState {
  const storedValue = localStorage.getItem(STORAGE_KEY);
  if (!storedValue) {
    return defaultState();
  }

  try {
    const defaults = defaultState();
    const parsed = JSON.parse(storedValue) as Partial<Record<string, unknown>>;
    const merged: AppearanceState = {
      reducedMotion: typeof parsed.reducedMotion === "boolean" ? parsed.reducedMotion : defaults.reducedMotion,
      listDensity: parsed.listDensity === "compact" ? "compact" : defaults.listDensity,
      backgroundMode: parsed.backgroundMode === "image" ? "image" : defaults.backgroundMode,
      backgroundImageUrl: typeof parsed.backgroundImageUrl === "string" ? parsed.backgroundImageUrl : defaults.backgroundImageUrl,
      authThemePreset:
        typeof parsed.authThemePreset === "string"
          ? resolveAuthThemePreset(parsed.authThemePreset).id
          : defaults.authThemePreset,
      authAccentColor:
        typeof parsed.authAccentColor === "string" && parsed.authAccentColor
          ? parsed.authAccentColor
          : defaults.authAccentColor,
      authBackgroundImageUrl:
        typeof parsed.authBackgroundImageUrl === "string"
          ? parsed.authBackgroundImageUrl
          : defaults.authBackgroundImageUrl,
    };

    if (!merged.authAccentColor) {
      merged.authAccentColor = resolveAuthThemePreset(merged.authThemePreset).variables["--auth-accent"];
    }

    return merged;
  } catch {
    return defaultState();
  }
}


export const useAppearanceStore = defineStore("appearance", () => {
  const state = ref<AppearanceState>(readInitialState());

  watch(
    state,
    (nextValue) => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextValue));
    },
    { deep: true },
  );

  const backgroundStyle = computed<Record<string, string>>(() => {
    if (state.value.backgroundMode === "image" && state.value.backgroundImageUrl) {
      return {
        backgroundImage: `linear-gradient(rgba(248,250,252,0.88), rgba(248,250,252,0.94)), url(${state.value.backgroundImageUrl})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      };
    }
    return { backgroundColor: "var(--color-bg)" };
  });

  function resetAuthPageStyle(): void {
    const defaults = defaultState();
    state.value = {
      ...state.value,
      authThemePreset: defaults.authThemePreset,
      authAccentColor: defaults.authAccentColor,
      authBackgroundImageUrl: defaults.authBackgroundImageUrl,
    };
  }

  return {
    state,
    backgroundStyle,
    resetAuthPageStyle,
  };
});
