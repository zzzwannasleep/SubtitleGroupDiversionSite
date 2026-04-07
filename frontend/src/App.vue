<script setup lang="ts">
import { watchEffect } from "vue";
import { RouterView, useRoute } from "vue-router";

import ToastHost from "@/components/ToastHost.vue";
import { usePageTransition } from "@/composables/usePageTransition";
import { useSiteDisplayName } from "@/composables/useSiteDisplayName";
import { translate } from "@/locales";
import { useLocaleStore } from "@/stores/locale";


const { transitionName } = usePageTransition();
const route = useRoute();
const localeStore = useLocaleStore();
const { siteDisplayName } = useSiteDisplayName();

watchEffect(() => {
  const appName = siteDisplayName.value || translate(localeStore.locale, "common.appName");
  const pageTitle = route.meta.titleKey
    ? translate(localeStore.locale, route.meta.titleKey as string)
    : (route.meta.title as string | undefined) ?? appName;

  document.title = `${pageTitle} | ${appName}`;
});
</script>

<template>
  <RouterView v-slot="{ Component }">
    <Transition :name="transitionName" mode="out-in">
      <component :is="Component" />
    </Transition>
  </RouterView>
  <ToastHost />
</template>
