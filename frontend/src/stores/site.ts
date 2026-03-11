import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { getSiteSettings } from "@/api/site";


export const useSiteStore = defineStore("site", () => {
  const siteName = ref("");
  const loaded = ref(false);
  const loading = ref(false);

  const normalizedSiteName = computed(() => siteName.value.trim());

  async function loadSiteSettings(force = false): Promise<string> {
    if (loading.value) {
      return normalizedSiteName.value;
    }
    if (loaded.value && !force) {
      return normalizedSiteName.value;
    }

    loading.value = true;
    try {
      const response = await getSiteSettings();
      siteName.value = response.site_name.trim();
      loaded.value = true;
      return normalizedSiteName.value;
    } catch {
      loaded.value = true;
      return normalizedSiteName.value;
    } finally {
      loading.value = false;
    }
  }

  function setSiteName(nextSiteName: string): void {
    siteName.value = nextSiteName.trim();
    loaded.value = true;
  }

  return {
    siteName,
    loaded,
    loading,
    normalizedSiteName,
    loadSiteSettings,
    setSiteName,
  };
});
