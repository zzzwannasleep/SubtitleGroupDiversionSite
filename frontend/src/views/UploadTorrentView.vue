<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { listCategories } from "@/api/categories";
import { uploadTorrent } from "@/api/torrents";
import PageSection from "@/components/PageSection.vue";
import type { Category } from "@/types";


const categories = ref<Category[]>([]);
const errorMessage = ref("");
const successMessage = ref("");
const loading = ref(false);

const form = reactive({
  torrentFile: null as File | null,
  categoryId: "",
  name: "",
  subtitle: "",
  description: "",
  coverImageUrl: "",
  mediaInfo: "",
});

async function loadCategories(): Promise<void> {
  categories.value = await listCategories();
}

async function submit(): Promise<void> {
  errorMessage.value = "";
  successMessage.value = "";

  if (!form.torrentFile || !form.categoryId) {
    errorMessage.value = "Torrent file and category are required.";
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

  loading.value = true;
  try {
    const response = await uploadTorrent(payload);
    successMessage.value = response.message;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Upload failed";
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
    <PageSection title="Upload Torrent" subtitle="Only admins and uploaders can access this page.">
      <div class="grid gap-4 lg:grid-cols-2">
        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">Torrent file</span>
          <input
            type="file"
            accept=".torrent"
            class="w-full rounded-xl border border-slate-300 px-4 py-3"
            @change="form.torrentFile = ($event.target as HTMLInputElement).files?.[0] ?? null"
          />
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">Category</span>
          <select v-model="form.categoryId" class="w-full rounded-xl border border-slate-300 px-4 py-3">
            <option value="">Select category</option>
            <option v-for="category in categories" :key="category.id" :value="String(category.id)">
              {{ category.name }}
            </option>
          </select>
        </label>
      </div>
    </PageSection>

    <PageSection title="Display Metadata" subtitle="These fields shape how the torrent appears on the site.">
      <div class="grid gap-4 lg:grid-cols-2">
        <input v-model="form.name" placeholder="Display name" class="rounded-xl border border-slate-300 px-4 py-3" />
        <input v-model="form.subtitle" placeholder="Subtitle / original title" class="rounded-xl border border-slate-300 px-4 py-3" />
      </div>
      <textarea
        v-model="form.description"
        rows="6"
        placeholder="Description"
        class="mt-4 w-full rounded-xl border border-slate-300 px-4 py-3"
      />
      <input
        v-model="form.coverImageUrl"
        placeholder="Cover image URL"
        class="mt-4 w-full rounded-xl border border-slate-300 px-4 py-3"
      />
    </PageSection>

    <PageSection title="Advanced Info" subtitle="MediaInfo and NFO-like text blocks stay plain in MVP.">
      <textarea
        v-model="form.mediaInfo"
        rows="8"
        placeholder="Media info"
        class="w-full rounded-xl border border-slate-300 px-4 py-3"
      />
    </PageSection>

    <p v-if="errorMessage" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ errorMessage }}</p>
    <p v-if="successMessage" class="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{{ successMessage }}</p>

    <div class="flex justify-end">
      <button
        class="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
        :disabled="loading"
        @click="submit"
      >
        {{ loading ? "Uploading..." : "Submit torrent" }}
      </button>
    </div>
  </div>
</template>

