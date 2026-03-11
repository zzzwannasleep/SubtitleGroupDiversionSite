import { computed } from "vue";
import { useRoute } from "vue-router";

import { useAppearanceStore } from "@/stores/appearance";


export function usePageTransition() {
  const route = useRoute();
  const appearanceStore = useAppearanceStore();

  const transitionName = computed(() => {
    if (appearanceStore.state.reducedMotion) {
      return "page-none";
    }
    return (route.meta.transition as string | undefined) ?? "page-fade";
  });

  return {
    transitionName,
  };
}

