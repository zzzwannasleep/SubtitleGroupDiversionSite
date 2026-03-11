<script setup lang="ts">
import { onMounted, ref } from "vue";

import { buildRssLinks } from "@/api/rss";
import { getProfile } from "@/api/users";
import EmptyState from "@/components/EmptyState.vue";
import PageSection from "@/components/PageSection.vue";


const links = ref<Array<{ name: string; url: string }>>([]);
const errorMessage = ref("");

onMounted(async () => {
  try {
    const profile = await getProfile();
    links.value = buildRssLinks(profile);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Failed to load RSS links";
  }
});

async function copy(text: string): Promise<void> {
  await navigator.clipboard.writeText(text);
}
</script>

<template>
  <PageSection title="RSS Access" subtitle="Use your personal RSS key with downloader clients.">
    <EmptyState v-if="errorMessage" title="RSS unavailable" :description="errorMessage" />

    <div v-else class="space-y-4">
      <div v-for="link in links" :key="link.name" class="rounded-2xl border border-slate-200 p-4">
        <p class="text-sm font-semibold text-slate-900">{{ link.name }}</p>
        <p class="mt-2 break-all font-mono text-sm text-slate-600">{{ link.url }}</p>
        <button class="mt-4 rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700" @click="copy(link.url)">
          Copy URL
        </button>
      </div>
    </div>
  </PageSection>
</template>

