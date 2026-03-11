import { computed } from "vue";

import { useI18n } from "@/composables/useI18n";
import { useSiteStore } from "@/stores/site";


export function useSiteDisplayName() {
  const { t } = useI18n();
  const siteStore = useSiteStore();

  const siteDisplayName = computed(() => siteStore.normalizedSiteName || t("common.appName"));

  return {
    siteDisplayName,
  };
}
