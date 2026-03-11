<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";

import {
  AUTH_THEME_PRESETS,
  type AuthThemePresetId,
  resolveAuthThemePreset,
} from "@/config/authTheme";
import { useAppearanceStore } from "@/stores/appearance";


interface Props {
  formEyebrow: string;
  formTitle: string;
  formDescription: string;
  alternatePrompt: string;
  alternateLabel: string;
  alternateTo: string;
  note?: string;
  showStyleStudio?: boolean;
}


const props = withDefaults(defineProps<Props>(), {
  note: "",
  showStyleStudio: true,
});

const appearanceStore = useAppearanceStore();

const platformFacts = [
  { label: "Target scale", value: "20-50 users" },
  { label: "Deployment", value: "Docker Compose" },
  { label: "Tracker mode", value: "XBT first" },
];

const safeguards = [
  "Per-user tracker credential delivery",
  "Role-based upload and admin controls",
  "Tracker-backed traffic and swarm snapshots",
];

const branding = computed(() => ({
  brandName: appearanceStore.state.authBrandName.trim() || "PT Platform",
  headline: appearanceStore.state.authHeadline.trim() || "Private tracker operations, without the forum overhead.",
  supportText:
    appearanceStore.state.authSupportText.trim() ||
    "Role-aware uploads, tracker-backed traffic stats, and per-user credential delivery for focused PT teams.",
}));

const activePreset = computed(() => resolveAuthThemePreset(appearanceStore.state.authThemePreset));

const pageStyle = computed<Record<string, string>>(() => {
  const backgroundImageUrl = appearanceStore.state.authBackgroundImageUrl.trim().replace(/'/g, "%27");

  return {
    ...activePreset.value.variables,
    "--auth-accent": appearanceStore.state.authAccentColor || activePreset.value.variables["--auth-accent"],
    "--auth-remote-image": backgroundImageUrl ? `url('${backgroundImageUrl}')` : "none",
  };
});

function applyPreset(presetId: AuthThemePresetId): void {
  const preset = resolveAuthThemePreset(presetId);
  appearanceStore.state.authThemePreset = presetId;
  appearanceStore.state.authAccentColor = preset.variables["--auth-accent"];
}

function usePresetAccent(): void {
  appearanceStore.state.authAccentColor = activePreset.value.variables["--auth-accent"];
}

function clearBackgroundImage(): void {
  appearanceStore.state.authBackgroundImageUrl = "";
}

function resetStyleStudio(): void {
  appearanceStore.resetAuthPageStyle();
}
</script>

<template>
  <div class="auth-shell" :style="pageStyle">
    <div class="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
      <header class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <RouterLink to="/login" class="auth-brand-link">
          <span class="h-2.5 w-2.5 rounded-full bg-[color:var(--auth-accent)]"></span>
          {{ branding.brandName }}
        </RouterLink>

        <div class="flex flex-wrap items-center gap-3">
          <RouterLink to="/torrents" class="auth-secondary-btn">Browse public torrents</RouterLink>
          <RouterLink v-if="props.alternateTo === '/register'" to="/register" class="auth-secondary-btn">
            Create account
          </RouterLink>
          <RouterLink v-else to="/login" class="auth-secondary-btn">Back to sign in</RouterLink>
        </div>
      </header>

      <div class="grid flex-1 gap-6 lg:grid-cols-[1.1fr,0.9fr] xl:gap-8">
        <section class="auth-panel auth-grid-panel overflow-hidden rounded-[2rem] p-6 sm:p-8 xl:p-10">
          <div class="relative z-10 max-w-2xl">
            <p class="auth-kicker-badge">Architecture-aligned access</p>
            <h2 class="mt-6 text-4xl font-semibold tracking-tight text-[color:var(--auth-text)] sm:text-5xl">
              {{ branding.headline }}
            </h2>
            <p class="mt-4 max-w-xl text-base leading-7 text-[color:var(--auth-text-muted)] sm:text-lg">
              {{ branding.supportText }}
            </p>

            <div class="mt-8 grid gap-4 sm:grid-cols-3">
              <div v-for="fact in platformFacts" :key="fact.label" class="auth-subpanel rounded-3xl p-4">
                <p class="text-xs font-semibold uppercase tracking-[0.2em] text-[color:var(--auth-text-muted)]">
                  {{ fact.label }}
                </p>
                <p class="mt-3 text-xl font-semibold text-[color:var(--auth-text)]">{{ fact.value }}</p>
              </div>
            </div>

            <div class="auth-subpanel mt-8 rounded-[2rem] p-6">
              <p class="text-sm font-semibold uppercase tracking-[0.2em] text-[color:var(--auth-text-muted)]">
                Operational focus
              </p>

              <div class="mt-4 grid gap-3">
                <div v-for="item in safeguards" :key="item" class="auth-subpanel flex items-start gap-3 rounded-2xl px-4 py-3">
                  <span class="mt-1 h-2.5 w-2.5 rounded-full bg-[color:var(--auth-accent)]"></span>
                  <span class="text-sm leading-6 text-[color:var(--auth-text)]">{{ item }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="space-y-6">
          <div class="auth-panel rounded-[2rem] p-6 sm:p-8">
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-[color:var(--auth-text-muted)]">
              {{ props.formEyebrow }}
            </p>
            <h1 class="mt-4 text-3xl font-semibold tracking-tight text-[color:var(--auth-text)] sm:text-4xl">
              {{ props.formTitle }}
            </h1>
            <p class="mt-3 max-w-xl text-sm leading-6 text-[color:var(--auth-text-muted)] sm:text-base">
              {{ props.formDescription }}
            </p>

            <div class="mt-8">
              <slot />
            </div>

            <p class="mt-6 text-sm text-[color:var(--auth-text-muted)]">
              {{ props.alternatePrompt }}
              <RouterLink :to="props.alternateTo" class="auth-link font-semibold">{{ props.alternateLabel }}</RouterLink>
            </p>
            <p v-if="props.note" class="mt-3 text-xs uppercase tracking-[0.16em] text-[color:var(--auth-text-muted)]">
              {{ props.note }}
            </p>
          </div>

          <div v-if="props.showStyleStudio" class="auth-panel rounded-[2rem] p-6 sm:p-8">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-[color:var(--auth-text-muted)]">
                  Style studio
                </p>
                <h2 class="mt-3 text-2xl font-semibold text-[color:var(--auth-text)]">
                  Customize the login presentation
                </h2>
                <p class="mt-2 text-sm leading-6 text-[color:var(--auth-text-muted)]">
                  Preferences are stored locally in this browser and can be reset at any time.
                </p>
              </div>

              <button type="button" class="auth-secondary-btn shrink-0" @click="resetStyleStudio">Reset</button>
            </div>

            <div class="mt-6 grid gap-5">
              <div>
                <label class="auth-field-label">Theme preset</label>

                <div class="mt-3 grid gap-3 sm:grid-cols-3">
                  <button
                    v-for="themePreset in AUTH_THEME_PRESETS"
                    :key="themePreset.id"
                    type="button"
                    class="auth-preset-btn"
                    :class="{ 'auth-preset-btn--active': themePreset.id === activePreset.id }"
                    @click="applyPreset(themePreset.id)"
                  >
                    <div class="flex items-center gap-3">
                      <span
                        class="h-4 w-4 rounded-full border border-white/20"
                        :style="{ backgroundColor: themePreset.variables['--auth-accent'] }"
                      />
                      <span class="text-sm font-semibold text-[color:var(--auth-text)]">{{ themePreset.label }}</span>
                    </div>
                    <p class="mt-3 text-xs leading-5 text-[color:var(--auth-text-muted)]">{{ themePreset.description }}</p>
                  </button>
                </div>
              </div>

              <div class="grid gap-4 sm:grid-cols-[auto,1fr] sm:items-end">
                <label class="block">
                  <span class="auth-field-label">Accent color</span>
                  <input v-model="appearanceStore.state.authAccentColor" type="color" class="auth-color-input mt-3" />
                </label>
                <button type="button" class="auth-secondary-btn w-full sm:w-auto" @click="usePresetAccent">
                  Use preset accent
                </button>
              </div>

              <label class="block">
                <span class="auth-field-label">Brand label</span>
                <input v-model="appearanceStore.state.authBrandName" class="auth-input mt-3" placeholder="PT Platform" />
              </label>

              <label class="block">
                <span class="auth-field-label">Hero title</span>
                <input
                  v-model="appearanceStore.state.authHeadline"
                  class="auth-input mt-3"
                  placeholder="Private tracker operations, without the forum overhead."
                />
              </label>

              <label class="block">
                <span class="auth-field-label">Hero subtitle</span>
                <textarea
                  v-model="appearanceStore.state.authSupportText"
                  class="auth-textarea mt-3"
                  rows="3"
                  placeholder="Role-aware uploads, tracker-backed traffic stats, and per-user credential delivery."
                />
              </label>

              <div class="grid gap-4 sm:grid-cols-[1fr,auto] sm:items-end">
                <label class="block">
                  <span class="auth-field-label">Background image URL</span>
                  <input
                    v-model="appearanceStore.state.authBackgroundImageUrl"
                    class="auth-input mt-3"
                    placeholder="https://example.com/tracker-room.jpg"
                  />
                </label>
                <button type="button" class="auth-secondary-btn w-full sm:w-auto" @click="clearBackgroundImage">
                  Clear image
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style>
.auth-shell {
  min-height: 100vh;
  color: var(--auth-text);
  background-color: var(--auth-bg);
  background-image:
    linear-gradient(var(--auth-image-overlay-top), var(--auth-image-overlay-bottom)),
    var(--auth-remote-image),
    radial-gradient(circle at top left, var(--auth-spotlight-a), transparent 34%),
    radial-gradient(circle at bottom right, var(--auth-spotlight-b), transparent 30%),
    linear-gradient(135deg, var(--auth-bg), var(--auth-bg-soft));
  background-position: center;
  background-size: cover, cover, auto, auto, auto;
}

.auth-panel {
  border: 1px solid var(--auth-border);
  background: var(--auth-surface);
  backdrop-filter: blur(22px);
  box-shadow: var(--auth-shadow);
}

.auth-subpanel {
  border: 1px solid var(--auth-border);
  background: var(--auth-surface-elevated);
}

.auth-grid-panel {
  position: relative;
}

.auth-grid-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(var(--auth-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--auth-grid) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.85), transparent 92%);
  pointer-events: none;
}

.auth-brand-link {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  border: 1px solid var(--auth-border);
  border-radius: 999px;
  background: var(--auth-surface-elevated);
  color: var(--auth-text);
  padding: 0.7rem 1rem;
  font-size: 0.875rem;
  font-weight: 700;
  backdrop-filter: blur(20px);
}

.auth-kicker-badge {
  display: inline-flex;
  border: 1px solid var(--auth-border);
  border-radius: 999px;
  background: var(--auth-accent-soft);
  padding: 0.65rem 1rem;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: var(--auth-text);
}

.auth-field-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--auth-text-muted);
}

.auth-input,
.auth-textarea {
  width: 100%;
  border-radius: 1rem;
  border: 1px solid var(--auth-border);
  background: var(--auth-input-bg);
  color: var(--auth-text);
  padding: 0.95rem 1rem;
  transition: border-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
}

.auth-input::placeholder,
.auth-textarea::placeholder {
  color: var(--auth-text-muted);
}

.auth-input:focus,
.auth-textarea:focus {
  outline: none;
  border-color: var(--auth-accent);
  box-shadow: 0 0 0 4px var(--auth-accent-soft);
  transform: translateY(-1px);
}

.auth-textarea {
  resize: vertical;
  min-height: 7rem;
}

.auth-color-input {
  width: 4.5rem;
  height: 3.25rem;
  padding: 0.35rem;
  border-radius: 1rem;
  border: 1px solid var(--auth-border);
  background: var(--auth-input-bg);
}

.auth-primary-btn,
.auth-secondary-btn,
.auth-link,
.auth-preset-btn {
  transition:
    transform 140ms ease,
    filter 140ms ease,
    border-color 140ms ease,
    background-color 140ms ease,
    color 140ms ease;
}

.auth-primary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  border: 0;
  border-radius: 1rem;
  padding: 0.95rem 1.25rem;
  background: var(--auth-accent);
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}

.auth-primary-btn:hover,
.auth-secondary-btn:hover,
.auth-preset-btn:hover {
  transform: translateY(-1px);
  filter: brightness(0.98);
}

.auth-primary-btn:disabled {
  cursor: wait;
  opacity: 0.7;
  transform: none;
}

.auth-secondary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid var(--auth-border);
  background: var(--auth-surface-elevated);
  color: var(--auth-text);
  padding: 0.7rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.auth-link {
  color: var(--auth-accent);
}

.auth-link:hover {
  filter: brightness(1.08);
}

.auth-preset-btn {
  border: 1px solid var(--auth-border);
  border-radius: 1.25rem;
  background: var(--auth-surface-elevated);
  padding: 1rem;
  text-align: left;
}

.auth-preset-btn--active {
  border-color: var(--auth-accent);
  background: var(--auth-accent-soft);
}

.auth-error-banner {
  border-radius: 1rem;
  border: 1px solid rgba(248, 113, 113, 0.28);
  background: rgba(127, 29, 29, 0.2);
  padding: 0.95rem 1rem;
  font-size: 0.875rem;
  color: #fecaca;
}
</style>
