<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";

import { getProfile, rotateProfileRssKey, updateProfile } from "@/api/users";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import PageSection from "@/components/PageSection.vue";
import { useI18n } from "@/composables/useI18n";
import { AUTH_THEME_PRESETS } from "@/config/authTheme";
import { useAppearanceStore } from "@/stores/appearance";
import { useAuthStore } from "@/stores/auth";
import { useLocaleStore } from "@/stores/locale";
import { useToastStore } from "@/stores/toast";
import type { UserProfile } from "@/types";
import { formatBytes, formatDate } from "@/utils/format";

const STEADY_UPLOAD_BYTES = 100 * 1024 ** 3;
const CORE_UPLOAD_BYTES = 1024 ** 4;
const STEADY_RATIO = 1;
const CORE_RATIO = 3;
const PREVIEW_STORAGE_KEY = "pt-platform.profile-preview";
const DEFAULT_PREVIEW_AVATAR_URL = `data:image/svg+xml,${encodeURIComponent(
  "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 160 160'><rect width='160' height='160' rx='36' fill='#0f172a'/><circle cx='80' cy='62' r='28' fill='#e2e8f0'/><path d='M32 142c10-28 32-42 48-42s38 14 48 42' fill='#94a3b8'/></svg>",
)}`;

interface LevelInfo {
  cardClass: string;
  pillClass: string;
  labelKey: string;
  descriptionKey: string;
  goalKey: string;
  goalParams?: Record<string, string | number>;
}

const profile = ref<UserProfile | null>(null);
const isLoading = ref(false);
const isSaving = ref(false);
const isRotatingRssKey = ref(false);
const rssRotateConfirmOpen = ref(false);
const loadErrorMessage = ref("");
const formErrorMessage = ref("");
const successMessage = ref("");
const email = ref("");
const avatarUrl = ref("");
const bio = ref("");

const appearanceStore = useAppearanceStore();
const authStore = useAuthStore();
const localeStore = useLocaleStore();
const toastStore = useToastStore();
const route = useRoute();
const { t } = useI18n();

function buildDefaultPreviewProfile(): UserProfile {
  return {
    id: 10086,
    username: "PreviewMember",
    email: "preview.member@example.com",
    avatar_url: DEFAULT_PREVIEW_AVATAR_URL,
    bio: "偏爱冷色调海报和字幕整理，最近主要在做电影和纪录片方向的发布测试。",
    role: "user",
    status: "active",
    rss_key: "rss_preview_f6c1e9ab31",
    created_at: "2025-11-03T08:30:00Z",
    tracker_credential: "trk_preview_7fa1••••c92d",
    uploaded_bytes: 274 * 1024 ** 3,
    downloaded_bytes: 96 * 1024 ** 3,
    ratio: "2.85",
  };
}

function readPreviewProfile(): UserProfile {
  const defaults = buildDefaultPreviewProfile();
  const storedValue = localStorage.getItem(PREVIEW_STORAGE_KEY);
  if (!storedValue) {
    return defaults;
  }

  try {
    const parsed = JSON.parse(storedValue) as Partial<UserProfile>;
    return {
      ...defaults,
      ...parsed,
      avatar_url:
        typeof parsed.avatar_url === "string" || parsed.avatar_url === null
          ? parsed.avatar_url ?? null
          : defaults.avatar_url,
      bio:
        typeof parsed.bio === "string" || parsed.bio === null
          ? parsed.bio ?? null
          : defaults.bio,
      ratio:
        typeof parsed.ratio === "string" || parsed.ratio === null
          ? parsed.ratio ?? null
          : defaults.ratio,
    };
  } catch {
    return defaults;
  }
}

function writePreviewProfile(nextProfile: UserProfile): void {
  localStorage.setItem(PREVIEW_STORAGE_KEY, JSON.stringify(nextProfile));
}

function normalizeNullableString(value: string): string | null {
  const trimmedValue = value.trim();
  return trimmedValue ? trimmedValue : null;
}

function syncEditableFields(nextProfile: UserProfile): void {
  email.value = nextProfile.email;
  avatarUrl.value = nextProfile.avatar_url ?? "";
  bio.value = nextProfile.bio ?? "";
}

const memberSince = computed(() =>
  profile.value ? formatDate(profile.value.created_at, localeStore.locale) : "",
);

const isPreviewMode = computed(() => route.meta.previewProfile === true);

const ratioValue = computed<number | null>(() => {
  if (!profile.value?.ratio) {
    return null;
  }

  const parsedRatio = Number(profile.value.ratio);
  return Number.isFinite(parsedRatio) ? parsedRatio : null;
});

const ratioDisplay = computed(() => {
  if (ratioValue.value === null) {
    return t("common.na");
  }

  return ratioValue.value.toFixed(2);
});

const avatarPreviewUrl = computed(() => normalizeNullableString(avatarUrl.value));

const avatarInitial = computed(() => {
  const source = profile.value?.username.trim();
  return source ? source.charAt(0).toUpperCase() : "?";
});

const bioPreview = computed(() => normalizeNullableString(bio.value) ?? t("profile.overview.bioFallback"));

const canSaveProfile = computed(() => {
  if (!profile.value || isSaving.value) {
    return false;
  }

  const trimmedEmail = email.value.trim();
  const nextAvatarUrl = normalizeNullableString(avatarUrl.value);
  const nextBio = normalizeNullableString(bio.value);
  const currentAvatarUrl = normalizeNullableString(profile.value.avatar_url ?? "");
  const currentBio = normalizeNullableString(profile.value.bio ?? "");

  return (
    trimmedEmail.length > 0
    && (
      trimmedEmail !== profile.value.email
      || nextAvatarUrl !== currentAvatarUrl
      || nextBio !== currentBio
    )
  );
});

const statusBadgeClass = computed(() => {
  switch (profile.value?.status) {
    case "active":
      return "border-emerald-200 bg-emerald-50 text-emerald-700";
    case "banned":
      return "border-rose-200 bg-rose-50 text-rose-700";
    case "pending":
      return "border-amber-200 bg-amber-50 text-amber-700";
    default:
      return "border-slate-200 bg-slate-50 text-slate-700";
  }
});

const levelInfo = computed<LevelInfo>(() => {
  if (!profile.value) {
    return {
      cardClass: "border-slate-200 bg-white text-slate-900",
      pillClass: "border-slate-200 bg-slate-100 text-slate-700",
      labelKey: "profile.level.tiers.newcomer.label",
      descriptionKey: "profile.level.tiers.newcomer.description",
      goalKey: "profile.level.goals.steady",
      goalParams: { upload: formatBytes(STEADY_UPLOAD_BYTES), ratio: STEADY_RATIO.toFixed(2) },
    };
  }

  if (profile.value.status === "banned") {
    return {
      cardClass: "border-rose-200 bg-rose-50 text-rose-950",
      pillClass: "border-rose-200 bg-white text-rose-700",
      labelKey: "profile.level.tiers.restricted.label",
      descriptionKey: "profile.level.tiers.restricted.description",
      goalKey: "profile.level.goals.restricted",
    };
  }

  if (profile.value.status === "pending") {
    return {
      cardClass: "border-amber-200 bg-amber-50 text-amber-950",
      pillClass: "border-amber-200 bg-white text-amber-700",
      labelKey: "profile.level.tiers.pending.label",
      descriptionKey: "profile.level.tiers.pending.description",
      goalKey: "profile.level.goals.pending",
    };
  }

  if (profile.value.role === "admin") {
    return {
      cardClass: "border-blue-200 bg-blue-50 text-blue-950",
      pillClass: "border-blue-200 bg-white text-blue-700",
      labelKey: "profile.level.tiers.admin.label",
      descriptionKey: "profile.level.tiers.admin.description",
      goalKey: "profile.level.goals.max",
    };
  }

  if (profile.value.role === "uploader") {
    return {
      cardClass: "border-sky-200 bg-sky-50 text-sky-950",
      pillClass: "border-sky-200 bg-white text-sky-700",
      labelKey: "profile.level.tiers.uploader.label",
      descriptionKey: "profile.level.tiers.uploader.description",
      goalKey: "profile.level.goals.max",
    };
  }

  if (
    profile.value.uploaded_bytes >= CORE_UPLOAD_BYTES
    || (ratioValue.value !== null && ratioValue.value >= CORE_RATIO)
  ) {
    return {
      cardClass: "border-emerald-200 bg-emerald-50 text-emerald-950",
      pillClass: "border-emerald-200 bg-white text-emerald-700",
      labelKey: "profile.level.tiers.core.label",
      descriptionKey: "profile.level.tiers.core.description",
      goalKey: "profile.level.goals.max",
    };
  }

  if (
    profile.value.uploaded_bytes >= STEADY_UPLOAD_BYTES
    || (ratioValue.value !== null && ratioValue.value >= STEADY_RATIO)
  ) {
    return {
      cardClass: "border-teal-200 bg-teal-50 text-teal-950",
      pillClass: "border-teal-200 bg-white text-teal-700",
      labelKey: "profile.level.tiers.steady.label",
      descriptionKey: "profile.level.tiers.steady.description",
      goalKey: "profile.level.goals.core",
      goalParams: { upload: formatBytes(CORE_UPLOAD_BYTES), ratio: CORE_RATIO.toFixed(2) },
    };
  }

  return {
    cardClass: "border-amber-200 bg-amber-50 text-amber-950",
    pillClass: "border-amber-200 bg-white text-amber-700",
    labelKey: "profile.level.tiers.newcomer.label",
    descriptionKey: "profile.level.tiers.newcomer.description",
    goalKey: "profile.level.goals.steady",
    goalParams: { upload: formatBytes(STEADY_UPLOAD_BYTES), ratio: STEADY_RATIO.toFixed(2) },
  };
});

async function loadProfile(): Promise<void> {
  isLoading.value = true;
  loadErrorMessage.value = "";

  try {
    profile.value = isPreviewMode.value ? readPreviewProfile() : await getProfile();
    syncEditableFields(profile.value);
  } catch (error) {
    profile.value = null;
    loadErrorMessage.value = error instanceof Error ? error.message : t("profile.account.loadError");
  } finally {
    isLoading.value = false;
  }
}

async function saveProfile(): Promise<void> {
  if (!profile.value || !canSaveProfile.value) {
    return;
  }

  formErrorMessage.value = "";
  successMessage.value = "";
  isSaving.value = true;

  try {
    if (isPreviewMode.value) {
      profile.value = {
        ...profile.value,
        email: email.value.trim(),
        avatar_url: normalizeNullableString(avatarUrl.value),
        bio: normalizeNullableString(bio.value),
      };
      writePreviewProfile(profile.value);
      successMessage.value = t("profile.preview.saveSuccess");
      toastStore.success(t("toasts.profileSaved"));
      syncEditableFields(profile.value);
      return;
    }

    profile.value = await updateProfile({
      email: email.value.trim(),
      avatar_url: normalizeNullableString(avatarUrl.value),
      bio: normalizeNullableString(bio.value),
    });
    syncEditableFields(profile.value);

    if (authStore.user) {
      authStore.user = {
        ...authStore.user,
        email: profile.value.email,
        avatar_url: profile.value.avatar_url,
      };
    }

    successMessage.value = t("profile.account.updateSuccess");
    toastStore.success(t("toasts.profileSaved"));
  } catch (error) {
    formErrorMessage.value = error instanceof Error ? error.message : t("profile.account.updateError");
  } finally {
    isSaving.value = false;
  }
}

function requestRotateRssKey(): void {
  if (isPreviewMode.value || isRotatingRssKey.value) {
    return;
  }

  rssRotateConfirmOpen.value = true;
}

async function rotateRssKey(): Promise<void> {
  if (isPreviewMode.value || isRotatingRssKey.value) {
    return;
  }

  rssRotateConfirmOpen.value = false;
  formErrorMessage.value = "";
  successMessage.value = "";
  isRotatingRssKey.value = true;

  try {
    profile.value = await rotateProfileRssKey();
    syncEditableFields(profile.value);
    successMessage.value = t("profile.access.rotateSuccess");
    toastStore.success(t("toasts.rssKeyRotated"));
  } catch (error) {
    formErrorMessage.value = error instanceof Error ? error.message : t("profile.access.rotateError");
  } finally {
    isRotatingRssKey.value = false;
  }
}

onMounted(() => {
  void loadProfile();
});
</script>

<template>
  <div class="space-y-6">
    <div
      v-if="isPreviewMode"
      class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-900"
    >
      <p class="font-semibold">{{ t("profile.preview.title") }}</p>
      <p class="mt-1 leading-6 text-amber-800">{{ t("profile.preview.description") }}</p>
    </div>

    <PageSection :title="t('profile.overview.title')" :subtitle="t('profile.overview.subtitle')">
      <div v-if="profile" class="grid gap-6 xl:grid-cols-[1.25fr,0.75fr]">
        <div class="overflow-hidden rounded-[1.75rem] border border-blue-100 bg-gradient-to-br from-blue-50 via-white to-slate-100 p-6 shadow-sm">
          <div class="flex flex-col gap-6 lg:flex-row lg:items-start">
            <div class="flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-[1.5rem] bg-slate-900 text-3xl font-semibold text-white shadow-sm ring-4 ring-white/70">
              <img
                v-if="avatarPreviewUrl"
                :src="avatarPreviewUrl"
                :alt="profile.username"
                class="h-full w-full object-cover"
              />
              <span v-else>{{ avatarInitial }}</span>
            </div>

            <div class="min-w-0 flex-1">
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-blue-700">{{ t("profile.overview.eyebrow") }}</p>
              <div class="mt-4 flex flex-wrap items-center gap-3">
                <h3 class="text-3xl font-semibold text-slate-950">{{ profile.username }}</h3>
                <span
                  class="inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em]"
                  :class="statusBadgeClass"
                >
                  {{ t(`common.statuses.${profile.status}`) }}
                </span>
              </div>
              <p class="mt-3 text-sm text-slate-600">{{ profile.email }}</p>
              <p class="mt-5 max-w-2xl text-sm leading-7 text-slate-600">{{ bioPreview }}</p>
            </div>
          </div>

          <div class="mt-6 grid gap-3 sm:grid-cols-3">
            <div class="rounded-2xl bg-white/90 p-4 ring-1 ring-slate-200/80">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("profile.account.role") }}</p>
              <p class="mt-2 text-base font-semibold text-slate-900">{{ t(`common.roles.${profile.role}`) }}</p>
            </div>
            <div class="rounded-2xl bg-white/90 p-4 ring-1 ring-slate-200/80">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("profile.overview.memberSince") }}</p>
              <p class="mt-2 text-base font-semibold text-slate-900">{{ memberSince }}</p>
            </div>
            <div class="rounded-2xl bg-white/90 p-4 ring-1 ring-slate-200/80">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("profile.overview.accountId") }}</p>
              <p class="mt-2 text-base font-semibold text-slate-900">#{{ profile.id }}</p>
            </div>
          </div>
        </div>

        <div class="grid gap-3">
          <div class="rounded-2xl bg-slate-950 p-5 text-white shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{{ t("profile.overview.ratio") }}</p>
            <p class="mt-3 text-3xl font-semibold">{{ ratioDisplay }}</p>
            <p class="mt-2 text-sm text-slate-400">{{ t("profile.overview.ratioHint") }}</p>
          </div>

          <div class="rounded-2xl border p-5 shadow-sm" :class="levelInfo.cardClass">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-current/60">{{ t("profile.level.title") }}</p>
            <div class="mt-3">
              <span
                class="inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em]"
                :class="levelInfo.pillClass"
              >
                {{ t(levelInfo.labelKey) }}
              </span>
            </div>
            <p class="mt-3 text-sm leading-6 text-current/80">{{ t(levelInfo.descriptionKey) }}</p>

            <div class="mt-4 rounded-2xl bg-white/75 p-4 ring-1 ring-black/5">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("profile.level.nextTitle") }}</p>
              <p class="mt-2 text-sm leading-6 text-slate-700">{{ t(levelInfo.goalKey, levelInfo.goalParams) }}</p>
            </div>
          </div>

          <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("profile.account.uploaded") }}</p>
              <p class="mt-3 text-2xl font-semibold text-slate-900">{{ formatBytes(profile.uploaded_bytes) }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("profile.account.downloaded") }}</p>
              <p class="mt-3 text-2xl font-semibold text-slate-900">{{ formatBytes(profile.downloaded_bytes) }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="isLoading" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
        {{ t("profile.loading") }}
      </div>

      <p v-else class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
        {{ loadErrorMessage || t("profile.account.loadError") }}
      </p>
    </PageSection>

    <div v-if="profile" class="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
      <PageSection :title="t('profile.access.title')" :subtitle="t('profile.access.subtitle')">
        <div class="grid gap-4">
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("profile.account.trackerCredential") }}</p>
            <p class="mt-3 break-all font-mono text-sm text-slate-800">{{ profile.tracker_credential }}</p>
            <p class="mt-3 text-sm leading-6 text-slate-500">{{ t("profile.access.trackerDescription") }}</p>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("profile.account.rssKey") }}</p>
            <p class="mt-3 break-all font-mono text-sm text-slate-800">{{ profile.rss_key }}</p>
            <p class="mt-3 text-sm leading-6 text-slate-500">{{ t("profile.access.rssDescription") }}</p>
            <p
              v-if="isPreviewMode"
              class="mt-4 inline-flex rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-500"
            >
              {{ t("profile.preview.rssUnavailable") }}
            </p>
            <RouterLink
              v-else
              to="/rss"
              class="mt-4 inline-flex rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
            >
              {{ t("profile.access.openRss") }}
            </RouterLink>
            <button
              v-if="!isPreviewMode"
              class="ml-0 mt-3 inline-flex rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-800 transition hover:border-amber-300 hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-60 sm:ml-3"
              type="button"
              :disabled="isRotatingRssKey"
              @click="requestRotateRssKey"
            >
              {{ isRotatingRssKey ? t("profile.access.rotateLoading") : t("profile.access.rotateRssKey") }}
            </button>
          </div>
        </div>
      </PageSection>

      <PageSection :title="t('profile.account.title')" :subtitle="t('profile.account.subtitle')">
        <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr),280px]">
          <div class="space-y-4">
            <label class="block">
              <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.account.avatarUrl") }}</span>
              <input
                v-model="avatarUrl"
                class="w-full rounded-xl border border-slate-300 px-4 py-3"
                :placeholder="t('profile.account.avatarUrlPlaceholder')"
              />
            </label>

            <label class="block">
              <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.account.email") }}</span>
              <input v-model="email" type="email" class="w-full rounded-xl border border-slate-300 px-4 py-3" />
            </label>

            <label class="block">
              <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.account.bio") }}</span>
              <textarea
                v-model="bio"
                rows="5"
                class="w-full rounded-xl border border-slate-300 px-4 py-3"
                :placeholder="t('profile.account.bioPlaceholder')"
              />
            </label>

            <p class="text-sm leading-6 text-slate-500">{{ t("profile.account.helper") }}</p>

            <p v-if="formErrorMessage" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
              {{ formErrorMessage }}
            </p>
            <p v-if="successMessage" class="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              {{ successMessage }}
            </p>

            <button
              class="rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition enabled:hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              :disabled="!canSaveProfile"
              @click="saveProfile"
            >
              {{ isSaving ? t("profile.account.saveLoading") : t("profile.account.save") }}
            </button>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
            <div class="flex items-center gap-4">
              <div class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-slate-900 text-xl font-semibold text-white">
                <img
                  v-if="avatarPreviewUrl"
                  :src="avatarPreviewUrl"
                  :alt="profile.username"
                  class="h-full w-full object-cover"
                />
                <span v-else>{{ avatarInitial }}</span>
              </div>
              <div class="min-w-0">
                <p class="text-base font-semibold text-slate-900">{{ profile.username }}</p>
                <p class="mt-1 text-sm text-slate-500">{{ t(`common.roles.${profile.role}`) }}</p>
              </div>
            </div>

            <div class="mt-5 space-y-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("profile.overview.status") }}</p>
                <span
                  class="mt-2 inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em]"
                  :class="statusBadgeClass"
                >
                  {{ t(`common.statuses.${profile.status}`) }}
                </span>
              </div>

              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{{ t("profile.account.bioPreview") }}</p>
                <p class="mt-2 text-sm leading-6 text-slate-600">{{ bioPreview }}</p>
              </div>
            </div>
          </div>
        </div>
      </PageSection>
    </div>

    <PageSection :title="t('profile.appearance.title')" :subtitle="t('profile.appearance.subtitle')">
      <div class="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
        <div class="space-y-4">
          <label class="block">
            <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.locale") }}</span>
            <select v-model="localeStore.locale" class="w-full rounded-xl border border-slate-300 px-4 py-3">
              <option v-for="option in localeStore.options" :key="option.code" :value="option.code">
                {{ option.nativeLabel }}
              </option>
            </select>
            <p class="mt-2 text-sm text-slate-500">{{ t("profile.appearance.localeDescription") }}</p>
          </label>

          <label class="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-3">
            <span class="text-sm font-medium text-slate-700">{{ t("profile.appearance.reducedMotion") }}</span>
            <input v-model="appearanceStore.state.reducedMotion" type="checkbox" class="h-4 w-4" />
          </label>

          <label class="block">
            <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.backgroundMode") }}</span>
            <select v-model="appearanceStore.state.backgroundMode" class="w-full rounded-xl border border-slate-300 px-4 py-3">
              <option value="solid">{{ t("profile.appearance.backgroundModes.solid") }}</option>
              <option value="image">{{ t("profile.appearance.backgroundModes.image") }}</option>
            </select>
          </label>

          <label class="block">
            <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.backgroundImageUrl") }}</span>
            <input
              v-model="appearanceStore.state.backgroundImageUrl"
              class="w-full rounded-xl border border-slate-300 px-4 py-3"
              :placeholder="t('profile.appearance.backgroundImagePlaceholder')"
            />
          </label>

          <label class="block">
            <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.listDensity") }}</span>
            <select v-model="appearanceStore.state.listDensity" class="w-full rounded-xl border border-slate-300 px-4 py-3">
              <option value="comfortable">{{ t("profile.appearance.listDensityOptions.comfortable") }}</option>
              <option value="compact">{{ t("profile.appearance.listDensityOptions.compact") }}</option>
            </select>
          </label>
        </div>

        <div class="rounded-2xl border border-slate-200 p-4">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="text-sm font-semibold text-slate-900">{{ t("profile.appearance.authThemeTitle") }}</p>
              <p class="mt-1 text-sm text-slate-500">{{ t("profile.appearance.authThemeDescription") }}</p>
            </div>
            <button
              class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700"
              @click="appearanceStore.resetAuthPageStyle"
            >
              {{ t("profile.appearance.resetAuthTheme") }}
            </button>
          </div>

          <div class="mt-4 space-y-4">
            <label class="block">
              <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.themePreset") }}</span>
              <select v-model="appearanceStore.state.authThemePreset" class="w-full rounded-xl border border-slate-300 px-4 py-3">
                <option v-for="preset in AUTH_THEME_PRESETS" :key="preset.id" :value="preset.id">
                  {{ t(preset.labelKey) }}
                </option>
              </select>
            </label>

            <label class="block">
              <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.accentColor") }}</span>
              <input v-model="appearanceStore.state.authAccentColor" type="color" class="h-12 w-20 rounded-xl border border-slate-300 bg-white p-2" />
            </label>

            <label class="block">
              <span class="mb-2 block text-sm font-medium text-slate-700">{{ t("profile.appearance.authBackgroundImageUrl") }}</span>
              <input v-model="appearanceStore.state.authBackgroundImageUrl" class="w-full rounded-xl border border-slate-300 px-4 py-3" />
            </label>
          </div>
        </div>
      </div>
    </PageSection>

    <ConfirmDialog
      v-model:open="rssRotateConfirmOpen"
      :title="t('profile.access.rotateConfirmTitle')"
      :description="t('profile.access.rotateConfirmDescription')"
      :confirm-label="t('profile.access.rotateConfirm')"
      tone="danger"
      :busy="isRotatingRssKey"
      @confirm="rotateRssKey"
    />
  </div>
</template>
