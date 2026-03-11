<script setup lang="ts">
import { RouterView } from "vue-router";

import AppHeader from "@/components/AppHeader.vue";
import AppSidebar from "@/components/AppSidebar.vue";
import BackgroundLayer from "@/components/BackgroundLayer.vue";
import { useAppearance } from "@/composables/useAppearance";


const { backgroundStyle } = useAppearance();
</script>

<template>
  <div class="relative min-h-screen text-slate-900" :style="backgroundStyle">
    <BackgroundLayer />
    <div class="relative flex min-h-screen">
      <AppSidebar />
      <div class="flex min-h-screen min-w-0 flex-1 flex-col">
        <AppHeader />
        <main class="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div class="mx-auto max-w-7xl">
            <RouterView />
          </div>
        </main>
      </div>
    </div>
  </div>
</template>
