import { ref, watch } from "vue";
import { defineStore } from "pinia";

import {
  DEFAULT_LOCALE,
  SUPPORTED_LOCALES,
  detectDefaultLocale,
  isLocaleCode,
  translate,
  type LocaleCode,
} from "@/locales";


const STORAGE_KEY = "pt-platform.locale";

function readInitialLocale(): LocaleCode {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (isLocaleCode(raw)) {
    return raw;
  }
  return detectDefaultLocale() ?? DEFAULT_LOCALE;
}

export const useLocaleStore = defineStore("locale", () => {
  const locale = ref<LocaleCode>(readInitialLocale());

  watch(locale, (nextLocale) => {
    localStorage.setItem(STORAGE_KEY, nextLocale);
  });

  function setLocale(nextLocale: LocaleCode): void {
    locale.value = nextLocale;
  }

  function t(key: string, params?: Record<string, string | number>): string {
    return translate(locale.value, key, params);
  }

  return {
    locale,
    options: SUPPORTED_LOCALES,
    setLocale,
    t,
  };
});
