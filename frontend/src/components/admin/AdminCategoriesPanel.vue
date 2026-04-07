<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import {
  createAdminCategory,
  listAdminCategories,
  updateAdminCategory,
  type AdminCategoryItem,
} from "@/api/admin";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import { useI18n } from "@/composables/useI18n";
import { useToastStore } from "@/stores/toast";


interface CategoryDraft {
  name: string;
  slug: string;
  sort_order: number;
  is_enabled: boolean;
}


const categories = ref<AdminCategoryItem[]>([]);
const drafts = reactive<Record<number, CategoryDraft>>({});
const newCategory = reactive<CategoryDraft>({
  name: "",
  slug: "",
  sort_order: 0,
  is_enabled: true,
});
const loading = ref(false);
const creating = ref(false);
const savingCategoryId = ref<number | null>(null);
const errorMessage = ref("");
const confirmOpen = ref(false);
const pendingCategory = ref<AdminCategoryItem | null>(null);
const { t } = useI18n();
const toastStore = useToastStore();

const pendingDraft = computed(() => (pendingCategory.value ? drafts[pendingCategory.value.id] : null));
const confirmTone = computed(() => {
  if (!pendingCategory.value || !pendingDraft.value) {
    return "default";
  }
  return pendingCategory.value.is_enabled && !pendingDraft.value.is_enabled ? "danger" : "default";
});

function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
}

function syncDraft(category: AdminCategoryItem): void {
  drafts[category.id] = {
    name: category.name,
    slug: category.slug,
    sort_order: category.sort_order,
    is_enabled: category.is_enabled,
  };
}

function hasChanges(category: AdminCategoryItem): boolean {
  const draft = drafts[category.id];
  return Boolean(
    draft
      && (
        draft.name !== category.name
        || draft.slug !== category.slug
        || draft.sort_order !== category.sort_order
        || draft.is_enabled !== category.is_enabled
      ),
  );
}

async function loadCategories(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";

  try {
    const response = await listAdminCategories();
    categories.value = response;
    for (const category of response) {
      syncDraft(category);
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("admin.categories.loadError");
  } finally {
    loading.value = false;
  }
}

function resetNewCategory(): void {
  newCategory.name = "";
  newCategory.slug = "";
  newCategory.sort_order = 0;
  newCategory.is_enabled = true;
}

async function createCategory(): Promise<void> {
  const name = newCategory.name.trim();
  const slug = (newCategory.slug.trim() || slugify(newCategory.name)).toLowerCase();
  if (!name || !slug) {
    errorMessage.value = t("admin.categories.requiredError");
    return;
  }

  creating.value = true;
  errorMessage.value = "";

  try {
    const createdCategory = await createAdminCategory({
      name,
      slug,
      sort_order: Number(newCategory.sort_order) || 0,
      is_enabled: newCategory.is_enabled,
    });
    categories.value = [...categories.value, createdCategory].sort((left, right) => {
      if (left.sort_order !== right.sort_order) {
        return left.sort_order - right.sort_order;
      }
      return left.name.localeCompare(right.name);
    });
    syncDraft(createdCategory);
    resetNewCategory();
    toastStore.success(t("toasts.adminCategoryCreated"));
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("admin.categories.createError");
  } finally {
    creating.value = false;
  }
}

function requestSave(category: AdminCategoryItem): void {
  if (!hasChanges(category) || savingCategoryId.value !== null) {
    return;
  }
  pendingCategory.value = category;
  confirmOpen.value = true;
}

async function confirmSave(): Promise<void> {
  const category = pendingCategory.value;
  const draft = pendingDraft.value;
  if (!category || !draft) {
    confirmOpen.value = false;
    return;
  }

  savingCategoryId.value = category.id;
  errorMessage.value = "";

  try {
    const updatedCategory = await updateAdminCategory(category.id, {
      name: draft.name.trim(),
      slug: draft.slug.trim().toLowerCase(),
      sort_order: Number(draft.sort_order) || 0,
      is_enabled: draft.is_enabled,
    });
    categories.value = categories.value.map((item) => (item.id === updatedCategory.id ? updatedCategory : item));
    syncDraft(updatedCategory);
    toastStore.success(t("toasts.adminCategoryUpdated"));
    confirmOpen.value = false;
    pendingCategory.value = null;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("admin.categories.updateError");
  } finally {
    savingCategoryId.value = null;
  }
}

onMounted(() => {
  void loadCategories();
});
</script>

<template>
  <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 class="text-lg font-semibold text-slate-950">{{ t("admin.categories.title") }}</h2>
        <p class="mt-1 text-sm leading-6 text-slate-600">{{ t("admin.categories.subtitle") }}</p>
      </div>
      <button
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-blue-600 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        type="button"
        :disabled="loading"
        @click="loadCategories"
      >
        {{ loading ? t("admin.common.refreshing") : t("admin.common.refresh") }}
      </button>
    </div>

    <div class="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p class="text-sm font-semibold text-slate-900">{{ t("admin.categories.createTitle") }}</p>
      <div class="mt-4 grid gap-3 lg:grid-cols-[1.2fr,1fr,120px,120px,auto]">
        <input v-model="newCategory.name" class="rounded-xl border border-slate-300 px-3 py-2" :placeholder="t('admin.categories.name')" />
        <input v-model="newCategory.slug" class="rounded-xl border border-slate-300 px-3 py-2" :placeholder="t('admin.categories.slug')" />
        <input v-model.number="newCategory.sort_order" class="rounded-xl border border-slate-300 px-3 py-2" type="number" :placeholder="t('admin.categories.sortOrder')" />
        <label class="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700">
          <input v-model="newCategory.is_enabled" type="checkbox" class="h-4 w-4" />
          {{ t("admin.categories.enabled") }}
        </label>
        <button
          class="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition enabled:hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          type="button"
          :disabled="creating"
          @click="createCategory"
        >
          {{ creating ? t("admin.common.saving") : t("admin.categories.create") }}
        </button>
      </div>
    </div>

    <p v-if="errorMessage" class="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ errorMessage }}</p>
    <p v-else-if="loading && categories.length === 0" class="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
      {{ t("admin.categories.loading") }}
    </p>
    <p v-else-if="categories.length === 0" class="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
      {{ t("admin.categories.empty") }}
    </p>

    <div v-else class="mt-4 overflow-x-auto">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50 text-left text-slate-500">
          <tr>
            <th class="px-3 py-3 font-medium">{{ t("admin.categories.name") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.categories.slug") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.categories.sortOrder") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.categories.enabled") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.categories.actions") }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="category in categories" :key="category.id" :class="{ 'bg-blue-50/40': hasChanges(category) }">
            <template v-if="drafts[category.id]">
              <td class="px-3 py-3">
                <input v-model="drafts[category.id].name" class="w-52 rounded-xl border border-slate-300 px-3 py-2" />
              </td>
              <td class="px-3 py-3">
                <input v-model="drafts[category.id].slug" class="w-44 rounded-xl border border-slate-300 px-3 py-2" />
              </td>
              <td class="px-3 py-3">
                <input v-model.number="drafts[category.id].sort_order" class="w-24 rounded-xl border border-slate-300 px-3 py-2" type="number" />
              </td>
              <td class="px-3 py-3">
                <input v-model="drafts[category.id].is_enabled" type="checkbox" class="h-4 w-4" />
              </td>
              <td class="px-3 py-3">
                <button
                  class="rounded-xl bg-blue-600 px-3 py-2 text-xs font-semibold text-white transition enabled:hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                  type="button"
                  :disabled="!hasChanges(category) || savingCategoryId !== null"
                  @click="requestSave(category)"
                >
                  {{ savingCategoryId === category.id ? t("admin.common.saving") : t("admin.common.save") }}
                </button>
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmDialog
      v-model:open="confirmOpen"
      :title="t('admin.categories.confirmTitle')"
      :description="t('admin.categories.confirmDescription')"
      :confirm-label="t('admin.categories.confirm')"
      :tone="confirmTone"
      :busy="savingCategoryId !== null"
      @confirm="confirmSave"
    />
  </section>
</template>
