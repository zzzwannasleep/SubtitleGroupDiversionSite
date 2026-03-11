import { computed } from "vue";

import { useAppearanceStore } from "@/stores/appearance";


export function useAppearance() {
  const appearanceStore = useAppearanceStore();

  return {
    appearance: computed(() => appearanceStore.state),
    backgroundStyle: computed(() => appearanceStore.backgroundStyle),
  };
}
