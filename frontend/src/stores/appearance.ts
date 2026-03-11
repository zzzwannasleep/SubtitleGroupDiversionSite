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
  authBrandName: string;
  authHeadline: string;
  authSupportText: string;
  authBackgroundImageUrl: string;
}

const LEGACY_AUTH_DEFAULTS = {
  authBrandName: "PT Platform",
  authHeadline: "Private tracker operations, without the forum overhead.",
  authSupportText: "Role-aware uploads, tracker-backed traffic stats, and per-user credential delivery for focused PT teams.",
};


function defaultState(): AppearanceState {
  const defaultAuthTheme = resolveAuthThemePreset(DEFAULT_AUTH_THEME_PRESET_ID);

  return {
    reducedMotion: false,
    listDensity: "comfortable",
    backgroundMode: "solid",
    backgroundImageUrl: "",
    authThemePreset: DEFAULT_AUTH_THEME_PRESET_ID,
    authAccentColor: defaultAuthTheme.variables["--auth-accent"],
    authBrandName: "",
    authHeadline: "",
    authSupportText: "",
    authBackgroundImageUrl: "",
  };
}


function readInitialState(): AppearanceState {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return defaultState();
  }

  try {
    const merged = {
      ...defaultState(),
      ...(JSON.parse(raw) as Partial<AppearanceState>),
    };

    if (!merged.authAccentColor) {
      merged.authAccentColor = resolveAuthThemePreset(merged.authThemePreset).variables["--auth-accent"];
    }

    if (merged.authBrandName === LEGACY_AUTH_DEFAULTS.authBrandName) {
      merged.authBrandName = "";
    }
    if (merged.authHeadline === LEGACY_AUTH_DEFAULTS.authHeadline) {
      merged.authHeadline = "";
    }
    if (merged.authSupportText === LEGACY_AUTH_DEFAULTS.authSupportText) {
      merged.authSupportText = "";
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
      authBrandName: defaults.authBrandName,
      authHeadline: defaults.authHeadline,
      authSupportText: defaults.authSupportText,
      authBackgroundImageUrl: defaults.authBackgroundImageUrl,
    };
  }

  return {
    state,
    backgroundStyle,
    resetAuthPageStyle,
  };
});
