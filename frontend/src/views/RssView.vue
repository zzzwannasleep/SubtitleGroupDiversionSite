<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { listCategories } from "@/api/categories";
import { buildRssFeedUrl, buildRssRouteQuery } from "@/api/rss";
import { getProfile } from "@/api/users";
import EmptyState from "@/components/EmptyState.vue";
import PageSection from "@/components/PageSection.vue";
import { useI18n } from "@/composables/useI18n";
import type { Category, UserProfile } from "@/types";


const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const profile = ref<UserProfile | null>(null);
const categories = ref<Category[]>([]);
const errorMessage = ref("");
const isLoading = ref(true);
const copyFeedback = ref("");
const copyErrorMessage = ref("");

const filters = reactive({
  keyword: "",
  category: "",
  sort: "created_at_desc",
  freeOnly: false,
});

function parseFreeOnly(value: unknown): boolean {
  return value === "1" || value === "true" || value === true;
}

function syncFiltersFromQuery(query: typeof route.query): void {
  filters.keyword = typeof query.keyword === "string" ? query.keyword : "";
  filters.category = typeof query.category === "string" ? query.category : "";
  filters.sort = typeof query.sort === "string" ? query.sort : "created_at_desc";
  filters.freeOnly = parseFreeOnly(query.free_only);
}

watch(
  () => route.query,
  (query) => {
    syncFiltersFromQuery(query);
  },
  { immediate: true },
);

watch(
  () => [filters.keyword, filters.category, filters.sort, filters.freeOnly],
  () => {
    copyFeedback.value = "";
    copyErrorMessage.value = "";
  },
);

onMounted(async () => {
  isLoading.value = true;

  try {
    profile.value = await getProfile();
    categories.value = await listCategories().catch(() => []);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("rss.loadError");
  } finally {
    isLoading.value = false;
  }
});

const selectedCategoryName = computed(() => categories.value.find((category) => category.slug === filters.category)?.name ?? filters.category);

const feedUrl = computed(() =>
  profile.value
    ? buildRssFeedUrl(profile.value, {
        keyword: filters.keyword,
        category: filters.category,
        sort: filters.sort,
        freeOnly: filters.freeOnly,
      })
    : "",
);

const activeFilterChips = computed(() => {
  const chips: string[] = [];
  const normalizedKeyword = filters.keyword.trim();

  if (!filters.category && !normalizedKeyword && !filters.freeOnly) {
    chips.push(t("rss.generated.allVisible"));
  }
  if (filters.category) {
    chips.push(t("rss.generated.category", { name: selectedCategoryName.value }));
  }
  if (normalizedKeyword) {
    chips.push(t("rss.generated.keyword", { keyword: normalizedKeyword }));
  }
  if (filters.freeOnly) {
    chips.push(t("rss.generated.freeOnly"));
  }
  chips.push(filters.sort === "created_at_asc" ? t("torrentList.oldestFirst") : t("torrentList.newestFirst"));

  return chips;
});

async function applyFilters(): Promise<void> {
  await router.push({
    path: "/rss",
    query: buildRssRouteQuery({
      keyword: filters.keyword,
      category: filters.category,
      sort: filters.sort,
      freeOnly: filters.freeOnly,
    }),
  });
}

async function resetFilters(): Promise<void> {
  filters.keyword = "";
  filters.category = "";
  filters.sort = "created_at_desc";
  filters.freeOnly = false;
  copyFeedback.value = "";
  copyErrorMessage.value = "";

  await router.push({ path: "/rss" });
}

function copyWithFallback(text: string): void {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "absolute";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();

  const copied = document.execCommand("copy");
  textarea.remove();

  if (!copied) {
    throw new Error("copy failed");
  }
}

async function copy(): Promise<void> {
  if (!feedUrl.value) {
    return;
  }

  copyFeedback.value = "";
  copyErrorMessage.value = "";

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(feedUrl.value);
    } else {
      copyWithFallback(feedUrl.value);
    }
    copyFeedback.value = t("rss.copied");
  } catch {
    copyErrorMessage.value = t("rss.copyFailed");
  }
}
</script>

<template>
  <div class="space-y-6">
    <PageSection :title="t('rss.title')" :subtitle="t('rss.subtitle')">
      <EmptyState v-if="errorMessage" :title="t('rss.unavailable')" :description="errorMessage" />

      <div v-else-if="isLoading" class="grid gap-4">
        <div class="h-36 animate-pulse rounded-2xl border border-slate-200 bg-white/70" />
        <div class="h-72 animate-pulse rounded-2xl border border-slate-200 bg-white/70" />
      </div>

      <div v-else class="space-y-6">
        <div class="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("rss.instructions.title") }}</p>
          <p class="mt-3 text-sm leading-6 text-slate-600">{{ t("rss.instructions.summary") }}</p>
          <ul class="mt-4 space-y-2 text-sm leading-6 text-slate-600">
            <li>{{ t("rss.instructions.scope") }}</li>
            <li>{{ t("rss.instructions.client") }}</li>
            <li>{{ t("rss.instructions.bookmark") }}</li>
            <li>{{ t("rss.instructions.privacy") }}</li>
          </ul>
        </div>

        <div class="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
          <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("rss.filters.title") }}</p>
              <p class="mt-2 text-sm leading-6 text-slate-600">{{ t("rss.filters.description") }}</p>
            </div>

            <div class="mt-5 grid gap-4 lg:grid-cols-[2fr,1fr,1fr]">
              <label class="block">
                <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("rss.filters.keywordLabel") }}</span>
                <input
                  v-model="filters.keyword"
                  type="search"
                  :placeholder="t('rss.filters.keywordPlaceholder')"
                  class="w-full rounded-xl border border-slate-300 px-4 py-3"
                  @keyup.enter="applyFilters"
                />
              </label>

              <label class="block">
                <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("rss.filters.categoryLabel") }}</span>
                <select v-model="filters.category" class="w-full rounded-xl border border-slate-300 px-4 py-3">
                  <option value="">{{ t("torrentList.allCategories") }}</option>
                  <option v-for="category in categories" :key="category.id" :value="category.slug">
                    {{ category.name }}
                  </option>
                </select>
              </label>

              <label class="block">
                <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("rss.filters.sortLabel") }}</span>
                <select v-model="filters.sort" class="w-full rounded-xl border border-slate-300 px-4 py-3">
                  <option value="created_at_desc">{{ t("torrentList.newestFirst") }}</option>
                  <option value="created_at_asc">{{ t("torrentList.oldestFirst") }}</option>
                </select>
              </label>
            </div>

            <div class="mt-5 flex flex-col gap-4 border-t border-slate-200 pt-5 sm:flex-row sm:items-center sm:justify-between">
              <label class="inline-flex items-center gap-3 text-sm font-medium text-slate-700">
                <input v-model="filters.freeOnly" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-blue-600" />
                {{ t("rss.filters.freeOnly") }}
              </label>

              <div class="flex flex-wrap gap-3">
                <button class="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700" @click="applyFilters">
                  {{ t("rss.filters.apply") }}
                </button>
                <button class="rounded-xl border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700" @click="resetFilters">
                  {{ t("rss.filters.reset") }}
                </button>
              </div>
            </div>
          </section>

          <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("rss.generated.title") }}</p>
              <p class="mt-2 text-sm leading-6 text-slate-600">{{ t("rss.generated.description") }}</p>
            </div>

            <div class="mt-4 flex flex-wrap gap-2">
              <span
                v-for="chip in activeFilterChips"
                :key="chip"
                class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700"
              >
                {{ chip }}
              </span>
            </div>

            <p class="mt-4 break-all rounded-2xl border border-slate-200 bg-slate-50 p-4 font-mono text-sm text-slate-700">
              {{ feedUrl }}
            </p>

            <div class="mt-4 flex flex-wrap gap-3">
              <button class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700" @click="copy">
                {{ t("rss.copyUrl") }}
              </button>
              <a
                :href="feedUrl"
                target="_blank"
                rel="noreferrer"
                class="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
              >
                {{ t("rss.openUrl") }}
              </a>
            </div>

            <p v-if="copyFeedback" class="mt-4 text-sm text-emerald-600">{{ copyFeedback }}</p>
            <p v-if="copyErrorMessage" class="mt-2 text-sm text-red-600">{{ copyErrorMessage }}</p>
          </section>
        </div>
      </div>
    </PageSection>
  </div>
</template>
