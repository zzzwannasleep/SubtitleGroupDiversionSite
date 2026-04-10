<script setup lang="ts">
import { computed } from 'vue';
import { useSiteSettingsStore } from '@/stores/siteSettings';
import { buildLoginBackgroundStyle, buildSiteMonogram } from '@/utils/site-branding';

const siteSettingsStore = useSiteSettingsStore();

const settings = computed(() => siteSettingsStore.settings);
const siteIconUrl = computed(() => settings.value.siteIconResolvedUrl);
const brandMonogram = computed(() => buildSiteMonogram(settings.value.siteName));
const backgroundStyle = computed(() => buildLoginBackgroundStyle(settings.value));
const backgroundLabel = computed(() => {
  const map = {
    api: 'API 远程图',
    file: '本地上传图',
    css: 'CSS 背景',
  } as const;

  return map[settings.value.loginBackgroundType];
});
</script>

<template>
  <div class="auth-shell">
    <div class="auth-shell__background" :style="backgroundStyle" />
    <div class="auth-shell__noise" />
    <div class="auth-shell__glow auth-shell__glow--left" />
    <div class="auth-shell__glow auth-shell__glow--right" />

    <div class="auth-shell__content">
      <div class="auth-shell__grid">
        <section class="auth-brand-panel">
          <div class="auth-brand-panel__surface">
            <div class="auth-brand-panel__eyebrow">
              <span class="auth-brand-panel__eyebrow-line" />
              <span>站点入口</span>
            </div>

            <div class="auth-brand-mark">
              <span class="auth-brand-mark__ring auth-brand-mark__ring--outer" />
              <span class="auth-brand-mark__ring auth-brand-mark__ring--inner" />
              <div class="auth-brand-mark__core">
                <img
                  v-if="siteIconUrl"
                  :src="siteIconUrl"
                  :alt="`${settings.siteName} 图标`"
                  class="auth-brand-mark__image"
                />
                <span v-else class="auth-brand-mark__fallback">{{ brandMonogram }}</span>
              </div>
            </div>

            <div class="space-y-4">
              <h1 class="auth-brand-panel__title">{{ settings.siteName }}</h1>
              <p class="auth-brand-panel__description">{{ settings.siteDescription }}</p>
            </div>

            <div class="auth-brand-panel__stats">
              <div class="auth-brand-panel__stat">
                <span>品牌图标</span>
                <strong>{{ siteIconUrl ? '已自定义' : '默认字标' }}</strong>
              </div>
              <div class="auth-brand-panel__stat">
                <span>背景方案</span>
                <strong>{{ backgroundLabel }}</strong>
              </div>
            </div>

            <p v-if="settings.loginNotice" class="auth-brand-panel__notice">
              {{ settings.loginNotice }}
            </p>
          </div>
        </section>

        <section class="auth-form-panel">
          <div class="auth-form-panel__surface">
            <RouterView />
          </div>
        </section>
      </div>
    </div>
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
.auth-shell__noise,
.auth-shell__glow {
  pointer-events: none;
  position: absolute;
  inset: 0;
}

.auth-shell__background {
  transform: scale(1.03);
  filter: saturate(1.04);
}

.auth-shell__noise {
  opacity: 0.08;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-position: center;
  background-size: 72px 72px;
  mask-image: linear-gradient(to bottom, transparent, black 14%, black 86%, transparent);
}

.auth-shell__glow {
  filter: blur(90px);
  opacity: 0.34;
}

.auth-shell__glow--left {
  inset: auto auto -16% -12%;
  height: 22rem;
  width: 22rem;
  border-radius: 9999px;
  background: rgba(59, 130, 246, 0.58);
  animation: drift 14s ease-in-out infinite;
}

.auth-shell__glow--right {
  inset: 8% -6% auto auto;
  height: 18rem;
  width: 18rem;
  border-radius: 9999px;
  background: rgba(244, 114, 182, 0.4);
  animation: drift 17s ease-in-out infinite reverse;
}

.auth-shell__content {
  position: relative;
  z-index: 1;
  margin: 0 auto;
  display: flex;
  min-height: 100vh;
  width: 100%;
  max-width: 1320px;
  align-items: center;
  padding: 2rem 1rem;
}

.auth-shell__grid {
  display: grid;
  width: 100%;
  gap: 2rem;
  align-items: center;
}

.auth-brand-panel__surface,
.auth-form-panel__surface {
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.74), rgba(15, 23, 42, 0.56));
  box-shadow: 0 30px 80px rgba(2, 6, 23, 0.34);
  backdrop-filter: blur(28px);
}

.auth-brand-panel__surface {
  position: relative;
  overflow: hidden;
  border-radius: 32px;
  padding: 2rem;
  color: white;
}

.auth-brand-panel__surface::before {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: 31px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.06), transparent 38%),
    linear-gradient(180deg, rgba(148, 163, 184, 0.08), transparent 60%);
}

.auth-brand-panel__eyebrow,
.auth-brand-mark,
.auth-brand-panel__title,
.auth-brand-panel__description,
.auth-brand-panel__stats,
.auth-brand-panel__notice {
  position: relative;
  z-index: 1;
}

.auth-brand-panel__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  color: rgba(191, 219, 254, 0.88);
  font-size: 0.85rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}

.auth-brand-panel__eyebrow-line {
  height: 1px;
  width: 2.25rem;
  background: linear-gradient(90deg, rgba(96, 165, 250, 0.24), rgba(96, 165, 250, 0.96));
}

.auth-brand-mark {
  position: relative;
  margin: 2rem 0 2.25rem;
  display: flex;
  height: 8rem;
  width: 8rem;
  align-items: center;
  justify-content: center;
}

.auth-brand-mark__ring {
  position: absolute;
  inset: 0;
  border-radius: 9999px;
  border: 1px solid rgba(191, 219, 254, 0.24);
}

.auth-brand-mark__ring--outer {
  animation: pulse-ring 3.8s ease-in-out infinite;
}

.auth-brand-mark__ring--inner {
  inset: 12px;
  border-color: rgba(147, 197, 253, 0.34);
  animation: pulse-ring 3.2s ease-in-out infinite reverse;
}

.auth-brand-mark__core {
  position: relative;
  z-index: 1;
  display: flex;
  height: 5.25rem;
  width: 5.25rem;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 1.75rem;
  background:
    linear-gradient(145deg, rgba(96, 165, 250, 0.35), rgba(15, 23, 42, 0.88)),
    rgba(15, 23, 42, 0.88);
  box-shadow:
    0 18px 40px rgba(37, 99, 235, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.14);
  animation: float-brand 4.8s ease-in-out infinite;
}

.auth-brand-mark__image {
  height: 100%;
  width: 100%;
  object-fit: cover;
}

.auth-brand-mark__fallback {
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.auth-brand-panel__title {
  font-size: clamp(2rem, 3vw, 3.25rem);
  line-height: 1.05;
  font-weight: 700;
}

.auth-brand-panel__description {
  max-width: 34rem;
  color: rgba(226, 232, 240, 0.86);
  font-size: 1rem;
  line-height: 1.8;
}

.auth-brand-panel__stats {
  margin-top: 2rem;
  display: grid;
  gap: 1rem;
}

.auth-brand-panel__stat {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 1rem 1.1rem;
  border-radius: 20px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(15, 23, 42, 0.34);
}

.auth-brand-panel__stat span {
  color: rgba(191, 219, 254, 0.72);
  font-size: 0.82rem;
}

.auth-brand-panel__stat strong {
  font-size: 1rem;
  font-weight: 600;
}

.auth-brand-panel__notice {
  margin-top: 1.5rem;
  border-radius: 20px;
  border: 1px solid rgba(125, 211, 252, 0.18);
  background: rgba(8, 47, 73, 0.34);
  padding: 1rem 1.1rem;
  color: rgba(224, 242, 254, 0.9);
  line-height: 1.7;
}

.auth-form-panel__surface {
  border-radius: 28px;
  padding: 1rem;
}

@media (min-width: 1024px) {
  .auth-shell__grid {
    grid-template-columns: minmax(0, 1.08fr) minmax(380px, 0.78fr);
  }

  .auth-form-panel__surface {
    padding: 1.25rem;
  }
}

@media (max-width: 1023px) {
  .auth-brand-panel {
    display: none;
  }

  .auth-shell__content {
    max-width: 680px;
  }
}

@keyframes float-brand {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg) scale(1);
  }
  50% {
    transform: translateY(-8px) rotate(-3deg) scale(1.02);
  }
}

@keyframes pulse-ring {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.42;
  }
  50% {
    transform: scale(1.08);
    opacity: 0.18;
  }
}

@keyframes drift {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(18px, -14px, 0);
  }
}
</style>
