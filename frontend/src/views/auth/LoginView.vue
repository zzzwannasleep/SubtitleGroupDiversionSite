<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import { useMockApi } from '@/services/runtime';
import { useAuthStore } from '@/stores/auth';
import { useSiteSettingsStore } from '@/stores/siteSettings';
import { buildSiteMonogram } from '@/utils/site-branding';

const authStore = useAuthStore();
const siteSettingsStore = useSiteSettingsStore();
const router = useRouter();
const route = useRoute();

const isMockMode = computed(() => useMockApi());
const settings = computed(() => siteSettingsStore.settings);
const brandIconUrl = computed(() => settings.value.siteIconResolvedUrl);
const brandMonogram = computed(() => buildSiteMonogram(settings.value.siteName));
const registerLabel = computed(() => (settings.value.allowPublicRegistration ? '注册' : '邀请码注册'));

const form = reactive({
  username: '',
  password: '',
});

onMounted(() => {
  authStore.errorMessage = '';
});

async function handleSubmit() {
  try {
    await authStore.login(form);
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/';
    await router.push(redirect);
  } catch {
    // Error state is handled by the auth store.
  }
}

function fillDemoUser(username: string) {
  form.username = username;
  form.password = 'demo';
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-card__section login-card__section--brand">
        <div :class="['login-card__icon', brandIconUrl ? 'login-card__icon--plain' : '']">
          <img
            v-if="brandIconUrl"
            :src="brandIconUrl"
            :alt="`${settings.siteName} 图标`"
            class="login-card__image"
          />
          <span v-else class="login-card__fallback">{{ brandMonogram }}</span>
        </div>
        <div class="min-w-0">
          <h1 class="login-card__title">{{ settings.siteName }}</h1>
        </div>
      </div>

      <form class="login-card__section login-card__section--form" @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <div>
            <label class="login-card__label">账号</label>
            <UiInput v-model="form.username" placeholder="请输入用户名" />
          </div>

          <div>
            <label class="login-card__label">密码</label>
            <UiInput v-model="form.password" type="password" placeholder="请输入密码" />
          </div>
        </div>

        <p v-if="authStore.errorMessage" class="login-card__error">{{ authStore.errorMessage }}</p>
      </form>

      <div class="login-card__section login-card__section--actions">
        <UiButton type="submit" block variant="primary" :disabled="authStore.isLoading" @click="handleSubmit">
          {{ authStore.isLoading ? '登录中...' : '登录' }}
        </UiButton>
        <UiButton
          to="/register"
          block
          variant="secondary"
          :disabled="authStore.isLoading"
        >
          {{ registerLabel }}
        </UiButton>
      </div>
    </div>

    <p v-if="settings.loginNotice" class="login-page__notice">{{ settings.loginNotice }}</p>

    <div v-if="!settings.allowPublicRegistration" class="login-page__invite-tip">
      站点未开启公开注册，新成员需要先取得邀请码再完成注册。
    </div>

    <div v-if="isMockMode" class="login-page__demo">
      <p class="login-page__demo-title">本地预览快捷账号</p>
      <div class="flex flex-wrap justify-center gap-2">
        <UiButton variant="ghost" size="sm" @click="fillDemoUser('admin')">admin</UiButton>
        <UiButton variant="ghost" size="sm" @click="fillDemoUser('uploader')">uploader</UiButton>
        <UiButton variant="ghost" size="sm" @click="fillDemoUser('user')">user</UiButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: grid;
  gap: 1rem;
}

.login-card {
  overflow: hidden;
  border: 1px solid rgb(var(--border) / 0.66);
  border-radius: 1.75rem;
  background:
    linear-gradient(180deg, rgb(var(--surface) / 0.9), rgb(var(--surface-muted) / 0.76)),
    rgb(var(--surface) / 0.58);
  box-shadow: var(--shadow-2xl);
  backdrop-filter: blur(24px);
}

.login-card__section {
  padding: 1.35rem 1.35rem 1.2rem;
}

.login-card__section + .login-card__section {
  border-top: 1px solid rgb(var(--border) / 0.5);
}

.login-card__section--brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.login-card__section--actions {
  display: grid;
  gap: 0.75rem;
}

.login-card__icon {
  display: flex;
  height: 3.5rem;
  width: 3.5rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 1.15rem;
  background:
    linear-gradient(145deg, rgb(var(--primary) / 0.88), rgb(var(--surface) / 0.98)),
    rgb(var(--surface));
  box-shadow:
    0 14px 28px rgb(var(--primary) / 0.18),
    inset 0 1px 0 rgb(255 255 255 / 0.14);
}

.login-card__icon--plain {
  background: transparent;
  box-shadow: none;
}

.login-card__image {
  height: 100%;
  width: 100%;
  object-fit: contain;
}

.login-card__fallback {
  color: white;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.login-card__title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 1.45rem;
  font-weight: 700;
  color: rgb(var(--text-primary));
}

.login-card__label {
  margin-bottom: 0.55rem;
  display: block;
  font-size: 0.88rem;
  font-weight: 500;
  color: rgb(var(--text-tertiary));
}

.login-card__section--form :deep(input) {
  height: 3rem;
  border-color: rgb(var(--border) / 0.7);
  background: rgb(var(--page-bg) / 0.84);
  color: rgb(var(--text-primary));
}

.login-card__section--form :deep(input::placeholder) {
  color: rgb(var(--text-secondary) / 0.9);
}

.login-card__section--actions :deep(.bg-white) {
  background: rgb(var(--surface) / 0.74);
  border-color: rgb(var(--border) / 0.74);
  color: rgb(var(--text-primary));
}

.login-card__section--actions :deep(.bg-white:hover) {
  background: rgb(var(--surface-muted) / 0.94);
}

.login-card__error {
  margin-top: 1rem;
  font-size: 0.88rem;
  line-height: 1.6;
  color: rgb(var(--danger));
}

.login-page__notice,
.login-page__demo,
.login-page__invite-tip {
  border: 1px solid rgb(var(--border) / 0.58);
  border-radius: 1.25rem;
  background: rgb(var(--surface) / 0.68);
  padding: 0.95rem 1rem;
  color: rgb(var(--text-primary));
  backdrop-filter: blur(18px);
}

.login-page__notice,
.login-page__invite-tip {
  font-size: 0.88rem;
  line-height: 1.8;
}

.login-page__demo {
  display: grid;
  gap: 0.8rem;
}

.login-page__demo-title {
  text-align: center;
  font-size: 0.82rem;
  color: rgb(var(--primary-text));
}
</style>
