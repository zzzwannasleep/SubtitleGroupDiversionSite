<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";

import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import { useI18n } from "@/composables/useI18n";
import { resolveAuthThemePreset } from "@/config/authTheme";
import { useAppearanceStore } from "@/stores/appearance";


interface Props {
  formEyebrow?: string;
  formTitle: string;
  formDescription?: string;
  alternatePrompt: string;
  alternateLabel: string;
  alternateTo: string;
  note?: string;
}


const props = withDefaults(defineProps<Props>(), {
  note: "",
});

const appearanceStore = useAppearanceStore();
const { t } = useI18n();

const brandName = computed(() => appearanceStore.state.authBrandName.trim() || t("common.appName"));

const activePreset = computed(() => resolveAuthThemePreset(appearanceStore.state.authThemePreset));

const pageStyle = computed<Record<string, string>>(() => {
  const backgroundImageUrl = appearanceStore.state.authBackgroundImageUrl.trim().replace(/'/g, "%27");

  return {
    ...activePreset.value.variables,
    "--auth-accent": appearanceStore.state.authAccentColor || activePreset.value.variables["--auth-accent"],
    "--auth-remote-image": backgroundImageUrl ? `url('${backgroundImageUrl}')` : "none",
  };
});
</script>

<template>
  <div class="auth-shell" :style="pageStyle">
    <div class="mx-auto min-h-screen max-w-5xl px-4 py-5 sm:px-6 lg:px-8">
      <div class="flex justify-end">
        <LocaleSwitcher variant="auth" />
      </div>

      <div class="flex min-h-[calc(100vh-3.5rem)] items-center justify-center py-10">
        <section class="auth-window w-full max-w-md">
          <div class="auth-window-bar">
            <div class="auth-window-dots" aria-hidden="true">
              <span class="auth-window-dot auth-window-dot--warm"></span>
              <span class="auth-window-dot auth-window-dot--soft"></span>
              <span class="auth-window-dot auth-window-dot--cool"></span>
            </div>
            <p class="auth-window-meta">{{ brandName }}</p>
          </div>

          <div class="auth-window-body">
            <div>
              <p
                v-if="props.formEyebrow"
                class="text-[11px] font-semibold uppercase tracking-[0.24em] text-[color:var(--auth-text-muted)]"
              >
                {{ props.formEyebrow }}
              </p>
              <h1 class="text-3xl font-semibold tracking-tight text-[color:var(--auth-text)]" :class="props.formEyebrow ? 'mt-3' : ''">
                {{ props.formTitle }}
              </h1>
              <p v-if="props.formDescription" class="mt-2 text-sm leading-6 text-[color:var(--auth-text-muted)]">
                {{ props.formDescription }}
              </p>

              <div class="mt-7">
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
    radial-gradient(circle at top, var(--auth-spotlight-a), transparent 42%),
    linear-gradient(180deg, var(--auth-bg), var(--auth-bg-soft));
  background-position: center;
  background-size: cover, cover, auto, auto;
}

.auth-window {
  overflow: hidden;
  border: 1px solid var(--auth-border);
  border-radius: 1.5rem;
  background: color-mix(in srgb, var(--auth-surface-elevated) 90%, transparent);
  backdrop-filter: blur(24px);
  box-shadow: var(--auth-shadow);
}

.auth-window-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--auth-border);
  background: color-mix(in srgb, var(--auth-surface) 84%, transparent);
}

.auth-window-dots {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}

.auth-window-dot {
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.auth-window-dot--warm {
  background: #fb7185;
}

.auth-window-dot--soft {
  background: #fbbf24;
}

.auth-window-dot--cool {
  background: var(--auth-accent);
}

.auth-window-meta {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--auth-text-muted);
}

  .auth-window-body {
    padding: 1.4rem;
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

.auth-primary-btn,
.auth-link {
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

.auth-primary-btn:hover {
  transform: translateY(-1px);
  filter: brightness(0.98);
}

.auth-primary-btn:disabled {
  cursor: wait;
  opacity: 0.7;
  transform: none;
}

.auth-link {
  color: var(--auth-accent);
}

.auth-link:hover {
  filter: brightness(1.08);
}

.auth-error-banner {
  border-radius: 1rem;
  border: 1px solid rgba(248, 113, 113, 0.28);
  background: rgba(127, 29, 29, 0.2);
  padding: 0.95rem 1rem;
  font-size: 0.875rem;
  color: #fecaca;
}

@media (min-width: 640px) {
  .auth-window-body {
    padding: 1.75rem;
  }
}
</style>
