import { computed } from "vue";

import { useLocaleStore } from "@/stores/locale";


export function useI18n() {
  const localeStore = useLocaleStore();

  return {
    locale: computed(() => localeStore.locale),
    localeOptions: localeStore.options,
    setLocale: localeStore.setLocale,
    t: (key: string, params?: Record<string, string | number>) => localeStore.t(key, params),
  };
}
