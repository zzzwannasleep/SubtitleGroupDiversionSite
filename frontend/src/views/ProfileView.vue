<script setup lang="ts">
import { onMounted, ref } from "vue";

import { getProfile, updateProfile } from "@/api/users";
import PageSection from "@/components/PageSection.vue";
import { useAppearanceStore } from "@/stores/appearance";
import type { UserProfile } from "@/types";
import { formatBytes } from "@/utils/format";


const profile = ref<UserProfile | null>(null);
const errorMessage = ref("");
const successMessage = ref("");
const email = ref("");
const appearanceStore = useAppearanceStore();

async function loadProfile(): Promise<void> {
  try {
    profile.value = await getProfile();
    email.value = profile.value.email;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Failed to load profile";
  }
}

async function saveProfile(): Promise<void> {
  errorMessage.value = "";
  successMessage.value = "";

  try {
    profile.value = await updateProfile(email.value);
    successMessage.value = "Profile updated";
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Failed to update profile";
  }
}

onMounted(() => {
  void loadProfile();
});
</script>

<template>
  <div class="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
    <PageSection title="Account" subtitle="Identity, tracker-backed stats, and RSS access.">
      <div v-if="profile" class="space-y-6">
        <div class="grid gap-4 sm:grid-cols-2">
          <div class="rounded-2xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Username</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ profile.username }}</p>
          </div>
          <div class="rounded-2xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Role</p>
            <p class="mt-2 text-lg font-semibold capitalize text-slate-900">{{ profile.role }}</p>
          </div>
          <div class="rounded-2xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Uploaded</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ formatBytes(profile.uploaded_bytes) }}</p>
          </div>
          <div class="rounded-2xl bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Downloaded</p>
            <p class="mt-2 text-lg font-semibold text-slate-900">{{ formatBytes(profile.downloaded_bytes) }}</p>
          </div>
        </div>

        <div class="grid gap-4">
          <label class="block">
            <span class="mb-2 block text-sm font-medium text-slate-700">Email</span>
            <input v-model="email" type="email" class="w-full rounded-xl border border-slate-300 px-4 py-3" />
          </label>
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="rounded-2xl border border-slate-200 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Tracker credential</p>
              <p class="mt-3 break-all font-mono text-sm text-slate-700">{{ profile.tracker_credential }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 p-4">
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">RSS key</p>
              <p class="mt-3 break-all font-mono text-sm text-slate-700">{{ profile.rss_key }}</p>
            </div>
          </div>
        </div>

        <p v-if="errorMessage" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ errorMessage }}</p>
        <p v-if="successMessage" class="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{{ successMessage }}</p>

        <button class="rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white" @click="saveProfile">
          Save profile
        </button>
      </div>
    </PageSection>

    <PageSection title="Appearance" subtitle="Lightweight frontend preferences stored locally in MVP.">
      <div class="space-y-4">
        <label class="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-3">
          <span class="text-sm font-medium text-slate-700">Reduced motion</span>
          <input v-model="appearanceStore.state.reducedMotion" type="checkbox" class="h-4 w-4" />
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">Background mode</span>
          <select v-model="appearanceStore.state.backgroundMode" class="w-full rounded-xl border border-slate-300 px-4 py-3">
            <option value="solid">Solid</option>
            <option value="image">Image URL</option>
          </select>
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">Background image URL</span>
          <input
            v-model="appearanceStore.state.backgroundImageUrl"
            class="w-full rounded-xl border border-slate-300 px-4 py-3"
            placeholder="https://example.com/background.jpg"
          />
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">List density</span>
          <select v-model="appearanceStore.state.listDensity" class="w-full rounded-xl border border-slate-300 px-4 py-3">
            <option value="comfortable">Comfortable</option>
            <option value="compact">Compact</option>
          </select>
        </label>
      </div>
    </PageSection>
  </div>
</template>

