<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { listCategories } from "@/api/categories";
import { buildRssLinks } from "@/api/rss";
import { getProfile } from "@/api/users";
import EmptyState from "@/components/EmptyState.vue";
import PageSection from "@/components/PageSection.vue";
import { useI18n } from "@/composables/useI18n";
import type { Category, UserProfile } from "@/types";


const profile = ref<UserProfile | null>(null);
const categories = ref<Category[]>([]);
const errorMessage = ref("");
const { t } = useI18n();

const links = computed(() =>
  profile.value
    ? buildRssLinks(profile.value, categories.value, {
        allTorrentsLabel: t("rss.feeds.allTorrents"),
        categoryFeedName: (categoryName) => t("rss.feeds.category", { name: categoryName }),
      })
    : [],
);

onMounted(async () => {
  try {
    [profile.value, categories.value] = await Promise.all([getProfile(), listCategories()]);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("rss.loadError");
  }
});

async function copy(text: string): Promise<void> {
  await navigator.clipboard.writeText(text);
}
</script>

<template>
  <PageSection :title="t('rss.title')" :subtitle="t('rss.subtitle')">
    <EmptyState v-if="errorMessage" :title="t('rss.unavailable')" :description="errorMessage" />

    <div v-else class="space-y-4">
      <div v-for="link in links" :key="link.name" class="rounded-2xl border border-slate-200 p-4">
        <p class="text-sm font-semibold text-slate-900">{{ link.name }}</p>
        <p class="mt-2 break-all font-mono text-sm text-slate-600">{{ link.url }}</p>
        <button class="mt-4 rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700" @click="copy(link.url)">
          {{ t("rss.copyUrl") }}
        </button>
      </div>
    </div>
  </PageSection>
</template>
