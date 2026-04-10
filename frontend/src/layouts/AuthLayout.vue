<script setup lang="ts">
import { computed } from 'vue';
import { useSiteSettingsStore } from '@/stores/siteSettings';
import { buildLoginBackgroundStyle } from '@/utils/site-branding';

const siteSettingsStore = useSiteSettingsStore();
const settings = computed(() => siteSettingsStore.settings);
const backgroundStyle = computed(() => buildLoginBackgroundStyle(settings.value));
</script>

<template>
  <div class="auth-shell">
    <div class="auth-shell__background" :style="backgroundStyle" />
    <div class="auth-shell__veil" />
    <div class="auth-shell__noise" />
    <div class="auth-shell__glow auth-shell__glow--left" />
    <div class="auth-shell__glow auth-shell__glow--right" />

    <main class="auth-shell__content">
      <div class="auth-shell__viewport">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<style scoped>
.auth-shell {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #020617;
}

.auth-shell__background,
.auth-shell__veil,
.auth-shell__noise,
.auth-shell__glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.auth-shell__background {
  transform: scale(1.05);
  filter: saturate(1.06);
}

.auth-shell__veil {
  background:
    radial-gradient(circle at top left, rgb(15 23 42 / 0.18), transparent 38%),
    linear-gradient(135deg, rgb(2 6 23 / 0.56), rgb(15 23 42 / 0.76));
}

.auth-shell__noise {
  opacity: 0.08;
  background-image:
    linear-gradient(rgb(255 255 255 / 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgb(255 255 255 / 0.05) 1px, transparent 1px);
  background-position: center;
  background-size: 72px 72px;
  mask-image: linear-gradient(to bottom, transparent, black 14%, black 86%, transparent);
}

.auth-shell__glow {
  filter: blur(110px);
  opacity: 0.34;
}

.auth-shell__glow--left {
  inset: auto auto -18% -8%;
  height: 22rem;
  width: 22rem;
  border-radius: 9999px;
  background: rgb(56 189 248 / 0.36);
  animation: auth-glow-drift 15s ease-in-out infinite;
}

.auth-shell__glow--right {
  inset: 6% -10% auto auto;
  height: 18rem;
  width: 18rem;
  border-radius: 9999px;
  background: rgb(148 163 184 / 0.26);
  animation: auth-glow-drift 18s ease-in-out infinite reverse;
}

.auth-shell__content {
  position: relative;
  z-index: 1;
  display: flex;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.auth-shell__viewport {
  width: min(100%, 30rem);
}

@keyframes auth-glow-drift {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(24px, -16px, 0);
  }
}
</style>
