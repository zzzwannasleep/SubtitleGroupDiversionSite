<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { listCategories } from "@/api/categories";
import { uploadTorrent } from "@/api/torrents";
import PageSection from "@/components/PageSection.vue";
import { useI18n } from "@/composables/useI18n";
import { useToastStore } from "@/stores/toast";
import type { Category } from "@/types";


const router = useRouter();
const categories = ref<Category[]>([]);
const errorMessage = ref("");
const successMessage = ref("");
const loading = ref(false);
const { t } = useI18n();
const toastStore = useToastStore();

const form = reactive({
  torrentFile: null as File | null,
  categoryId: "",
  name: "",
  subtitle: "",
  description: "",
  coverImageUrl: "",
  mediaInfo: "",
  nfoText: "",
});

async function loadCategories(): Promise<void> {
  categories.value = await listCategories();
}

async function submit(): Promise<void> {
  errorMessage.value = "";
  successMessage.value = "";

  if (!form.torrentFile || !form.categoryId) {
    errorMessage.value = t("upload.requiredError");
    return;
  }

  const payload = new FormData();
  payload.append("torrent_file", form.torrentFile);
  payload.append("category_id", form.categoryId);
  payload.append("name", form.name);
  payload.append("subtitle", form.subtitle);
  payload.append("description", form.description);
  payload.append("cover_image_url", form.coverImageUrl);
  payload.append("media_info", form.mediaInfo);
  payload.append("nfo_text", form.nfoText);

  loading.value = true;
  try {
    const response = await uploadTorrent(payload);
    successMessage.value = response.message;
    toastStore.success(t("toasts.uploadSuccess"));
    if (response.id) {
      form.torrentFile = null;
      form.categoryId = "";
      form.name = "";
      form.subtitle = "";
      form.description = "";
      form.coverImageUrl = "";
      form.mediaInfo = "";
      form.nfoText = "";
      await router.push(`/torrents/${response.id}`);
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("upload.errorFallback");
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadCategories();
});
</script>

<template>
  <div class="space-y-6">
    <PageSection :title="t('upload.pageTitle')" :subtitle="t('upload.pageSubtitle')">
      <div class="grid gap-4 lg:grid-cols-2">
        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("upload.torrentFile") }}</span>
          <input
            type="file"
            accept=".torrent"
            class="w-full rounded-xl border border-slate-300 px-4 py-3"
            @change="form.torrentFile = ($event.target as HTMLInputElement).files?.[0] ?? null"
          />
          <p v-if="form.torrentFile" class="mt-2 text-sm text-slate-500">{{ form.torrentFile.name }}</p>
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("upload.category") }}</span>
          <select v-model="form.categoryId" class="w-full rounded-xl border border-slate-300 px-4 py-3">
            <option value="">{{ t("upload.selectCategory") }}</option>
            <option v-for="category in categories" :key="category.id" :value="String(category.id)">
              {{ category.name }}
            </option>
          </select>
        </label>
      </div>
    </PageSection>

    <PageSection :title="t('upload.metadataTitle')" :subtitle="t('upload.metadataSubtitle')">
      <div class="grid gap-4 lg:grid-cols-2">
        <input v-model="form.name" :placeholder="t('upload.placeholders.name')" class="rounded-xl border border-slate-300 px-4 py-3" />
        <input
          v-model="form.subtitle"
          :placeholder="t('upload.placeholders.subtitle')"
          class="rounded-xl border border-slate-300 px-4 py-3"
        />
      </div>
      <textarea
        v-model="form.description"
        rows="6"
        :placeholder="t('upload.placeholders.description')"
        class="mt-4 w-full rounded-xl border border-slate-300 px-4 py-3"
      />
      <input
        v-model="form.coverImageUrl"
        :placeholder="t('upload.placeholders.coverImageUrl')"
        class="mt-4 w-full rounded-xl border border-slate-300 px-4 py-3"
      />
    </PageSection>

    <PageSection :title="t('upload.advancedTitle')" :subtitle="t('upload.advancedSubtitle')">
      <div class="grid gap-4 lg:grid-cols-2">
        <textarea
          v-model="form.mediaInfo"
          rows="8"
          :placeholder="t('upload.placeholders.mediaInfo')"
          class="w-full rounded-xl border border-slate-300 px-4 py-3"
        />
        <textarea
          v-model="form.nfoText"
          rows="8"
          :placeholder="t('upload.placeholders.nfoText')"
          class="w-full rounded-xl border border-slate-300 px-4 py-3"
        />
      </div>
    </PageSection>

    <p v-if="errorMessage" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ errorMessage }}</p>
    <p v-if="successMessage" class="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{{ successMessage }}</p>

    <div class="flex justify-end">
      <button
        class="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
        :disabled="loading"
        @click="submit"
      >
        {{ loading ? t("upload.submitting") : t("upload.submit") }}
      </button>
    </div>
  </div>
</template>
