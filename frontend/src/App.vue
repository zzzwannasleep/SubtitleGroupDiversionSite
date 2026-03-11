<script setup lang="ts">
import { watchEffect } from "vue";
import { RouterView, useRoute } from "vue-router";

import { usePageTransition } from "@/composables/usePageTransition";
import { translate } from "@/locales";
import { useLocaleStore } from "@/stores/locale";


const { transitionName } = usePageTransition();
const route = useRoute();
const localeStore = useLocaleStore();

watchEffect(() => {
  const appName = translate(localeStore.locale, "common.appName");
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
</template>
