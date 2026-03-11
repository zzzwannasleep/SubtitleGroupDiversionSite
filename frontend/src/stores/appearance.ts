import { computed, ref, watch } from "vue";
import { defineStore } from "pinia";


const STORAGE_KEY = "pt-platform.appearance";

interface AppearanceState {
  reducedMotion: boolean;
  listDensity: "comfortable" | "compact";
  backgroundMode: "solid" | "image";
  backgroundImageUrl: string;
}


function defaultState(): AppearanceState {
  return {
    reducedMotion: false,
    listDensity: "comfortable",
    backgroundMode: "solid",
    backgroundImageUrl: "",
  };
}


function readInitialState(): AppearanceState {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return defaultState();
  }

  try {
    return JSON.parse(raw) as AppearanceState;
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

  return {
    state,
    backgroundStyle,
  };
});

