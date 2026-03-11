<script setup lang="ts">
import { RouterView } from "vue-router";

import { usePageTransition } from "@/composables/usePageTransition";


const { transitionName } = usePageTransition();
</script>

<template>
  <RouterView v-slot="{ Component }">
    <Transition :name="transitionName" mode="out-in">
      <component :is="Component" />
    </Transition>
  </RouterView>
</template>

