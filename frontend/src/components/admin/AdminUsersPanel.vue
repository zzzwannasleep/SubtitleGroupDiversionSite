<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { listAdminUsers, updateAdminUser, type AdminUserItem } from "@/api/admin";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import { useI18n } from "@/composables/useI18n";
import { useToastStore } from "@/stores/toast";
import type { UserRole, UserStatus } from "@/types";
import { formatDate } from "@/utils/format";


interface UserDraft {
  role: UserRole;
  status: UserStatus;
}


const roleOptions: UserRole[] = ["admin", "uploader", "user"];
const statusOptions: UserStatus[] = ["active", "pending", "banned"];

const users = ref<AdminUserItem[]>([]);
const drafts = reactive<Record<number, UserDraft>>({});
const loading = ref(false);
const savingUserId = ref<number | null>(null);
const errorMessage = ref("");
const confirmOpen = ref(false);
const pendingUser = ref<AdminUserItem | null>(null);
const { locale, t } = useI18n();
const toastStore = useToastStore();

const pendingDraft = computed(() => (pendingUser.value ? drafts[pendingUser.value.id] : null));
const confirmTone = computed(() => {
  if (!pendingUser.value || !pendingDraft.value) {
    return "default";
  }
  if (pendingDraft.value.status === "banned") {
    return "danger";
  }
  if (pendingUser.value.role === "admin" && pendingDraft.value.role !== "admin") {
    return "danger";
  }
  return "default";
});

function syncDraft(user: AdminUserItem): void {
  drafts[user.id] = {
    role: user.role,
    status: user.status,
  };
}

function hasChanges(user: AdminUserItem): boolean {
  const draft = drafts[user.id];
  return Boolean(draft && (draft.role !== user.role || draft.status !== user.status));
}

async function loadUsers(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";

  try {
    const response = await listAdminUsers();
    users.value = response.items;
    for (const user of response.items) {
      syncDraft(user);
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("admin.users.loadError");
  } finally {
    loading.value = false;
  }
}

function requestSave(user: AdminUserItem): void {
  if (!hasChanges(user) || savingUserId.value !== null) {
    return;
  }
  pendingUser.value = user;
  confirmOpen.value = true;
}

async function confirmSave(): Promise<void> {
  const user = pendingUser.value;
  const draft = pendingDraft.value;
  if (!user || !draft) {
    confirmOpen.value = false;
    return;
  }

  savingUserId.value = user.id;
  errorMessage.value = "";

  try {
    const updatedUser = await updateAdminUser(user.id, {
      role: draft.role,
      status: draft.status,
    });
    users.value = users.value.map((item) => (item.id === updatedUser.id ? updatedUser : item));
    syncDraft(updatedUser);
    toastStore.success(t("toasts.adminUserUpdated"));
    confirmOpen.value = false;
    pendingUser.value = null;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("admin.users.updateError");
  } finally {
    savingUserId.value = null;
  }
}

onMounted(() => {
  void loadUsers();
});
</script>

<template>
  <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 class="text-lg font-semibold text-slate-950">{{ t("admin.users.title") }}</h2>
        <p class="mt-1 text-sm leading-6 text-slate-600">{{ t("admin.users.subtitle") }}</p>
      </div>
      <button
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-blue-600 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        type="button"
        :disabled="loading"
        @click="loadUsers"
      >
        {{ loading ? t("admin.common.refreshing") : t("admin.common.refresh") }}
      </button>
    </div>

    <p v-if="errorMessage" class="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ errorMessage }}</p>
    <p v-else-if="loading && users.length === 0" class="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
      {{ t("admin.users.loading") }}
    </p>
    <p v-else-if="users.length === 0" class="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
      {{ t("admin.users.empty") }}
    </p>

    <div v-else class="mt-4 overflow-x-auto">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50 text-left text-slate-500">
          <tr>
            <th class="px-3 py-3 font-medium">{{ t("admin.users.user") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.users.email") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.users.role") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.users.status") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.users.created") }}</th>
            <th class="px-3 py-3 font-medium">{{ t("admin.users.actions") }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="user in users" :key="user.id" class="align-top" :class="{ 'bg-blue-50/40': hasChanges(user) }">
            <template v-if="drafts[user.id]">
              <td class="px-3 py-3 font-semibold text-slate-900">{{ user.username }}</td>
              <td class="px-3 py-3 text-slate-600">{{ user.email }}</td>
              <td class="px-3 py-3">
                <select v-model="drafts[user.id].role" class="rounded-xl border border-slate-300 px-3 py-2">
                  <option v-for="role in roleOptions" :key="role" :value="role">
                    {{ t(`common.roles.${role}`) }}
                  </option>
                </select>
              </td>
              <td class="px-3 py-3">
                <select v-model="drafts[user.id].status" class="rounded-xl border border-slate-300 px-3 py-2">
                  <option v-for="status in statusOptions" :key="status" :value="status">
                    {{ t(`common.statuses.${status}`) }}
                  </option>
                </select>
              </td>
              <td class="px-3 py-3 text-slate-600">{{ formatDate(user.created_at, locale) }}</td>
              <td class="px-3 py-3">
                <button
                  class="rounded-xl bg-blue-600 px-3 py-2 text-xs font-semibold text-white transition enabled:hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                  type="button"
                  :disabled="!hasChanges(user) || savingUserId !== null"
                  @click="requestSave(user)"
                >
                  {{ savingUserId === user.id ? t("admin.common.saving") : t("admin.common.save") }}
                </button>
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmDialog
      v-model:open="confirmOpen"
      :title="t('admin.users.confirmTitle')"
      :description="t('admin.users.confirmDescription')"
      :confirm-label="t('admin.users.confirm')"
      :tone="confirmTone"
      :busy="savingUserId !== null"
      @confirm="confirmSave"
    />
  </section>
</template>
