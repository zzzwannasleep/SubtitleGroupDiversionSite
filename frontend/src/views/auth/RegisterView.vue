<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import { useAuthStore } from '@/stores/auth';
import { useSiteSettingsStore } from '@/stores/siteSettings';
import { buildSiteMonogram } from '@/utils/site-branding';

const authStore = useAuthStore();
const siteSettingsStore = useSiteSettingsStore();
const router = useRouter();
const route = useRoute();

const settings = computed(() => siteSettingsStore.settings);
const brandIconUrl = computed(() => settings.value.siteIconResolvedUrl);
const brandMonogram = computed(() => buildSiteMonogram(settings.value.siteName));
const requiresInvite = computed(() => !settings.value.allowPublicRegistration);

const form = reactive({
  username: '',
  displayName: '',
  email: '',
  password: '',
  confirmPassword: '',
  inviteCode: '',
});

onMounted(() => {
  authStore.errorMessage = '';
  if (typeof route.query.code === 'string' && route.query.code.trim()) {
    form.inviteCode = route.query.code.trim();
  }
});

async function handleSubmit() {
  try {
    await authStore.register(form);
    await router.push('/');
  } catch {
    // Error state is handled by the auth store.
  }
}
</script>

<template>
  <div class="register-page">
    <div class="register-card">
      <div class="register-card__section register-card__section--brand">
        <div :class="['register-card__icon', brandIconUrl ? 'register-card__icon--plain' : '']">
          <img
            v-if="brandIconUrl"
            :src="brandIconUrl"
            :alt="`${settings.siteName} 图标`"
            class="register-card__image"
          />
          <span v-else class="register-card__fallback">{{ brandMonogram }}</span>
        </div>
        <div class="min-w-0">
          <h1 class="register-card__title">{{ settings.siteName }}</h1>
          <p class="register-card__subtitle">{{ requiresInvite ? '使用邀请码创建新账号' : '创建新账号' }}</p>
        </div>
      </div>

      <form class="register-card__section register-card__section--form" @submit.prevent="handleSubmit">
        <p v-if="requiresInvite" class="register-card__notice">
          当前站点采用邀请码注册，请先向管理员索取邀请码后再完成注册。
        </p>

        <div class="space-y-4">
          <div v-if="requiresInvite">
            <label class="register-card__label">邀请码</label>
            <UiInput v-model="form.inviteCode" placeholder="例如：ABCD-EFGH-2345" />
          </div>

          <div>
            <label class="register-card__label">用户名</label>
            <UiInput v-model="form.username" placeholder="请输入登录用户名" />
          </div>

          <div>
            <label class="register-card__label">站内名称</label>
            <UiInput v-model="form.displayName" placeholder="请输入显示名称" />
          </div>

          <div>
            <label class="register-card__label">邮箱</label>
            <UiInput v-model="form.email" type="email" placeholder="请输入邮箱地址" />
          </div>

          <div>
            <label class="register-card__label">密码</label>
            <UiInput v-model="form.password" type="password" placeholder="请输入密码" />
          </div>

          <div>
            <label class="register-card__label">确认密码</label>
            <UiInput v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" />
          </div>
        </div>

        <p v-if="authStore.errorMessage" class="register-card__error">{{ authStore.errorMessage }}</p>
      </form>

      <div class="register-card__section register-card__section--actions">
        <UiButton block variant="primary" :disabled="authStore.isLoading" @click="handleSubmit">
          {{ authStore.isLoading ? '提交中...' : requiresInvite ? '使用邀请码注册' : '注册' }}
        </UiButton>
        <UiButton to="/login" block variant="secondary" :disabled="authStore.isLoading">返回登录</UiButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-page {
  display: grid;
}

.register-card {
  overflow: hidden;
  border: 1px solid rgb(var(--border) / 0.66);
  border-radius: 1.75rem;
  background:
    linear-gradient(180deg, rgb(var(--surface) / 0.9), rgb(var(--surface-muted) / 0.76)),
    rgb(var(--surface) / 0.58);
  box-shadow: var(--shadow-2xl);
  backdrop-filter: blur(24px);
}

.register-card__section {
  padding: 1.35rem 1.35rem 1.2rem;
}

.register-card__section + .register-card__section {
  border-top: 1px solid rgb(var(--border) / 0.5);
}

.register-card__section--brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.register-card__section--actions {
  display: grid;
  gap: 0.75rem;
}

.register-card__icon {
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

.register-card__icon--plain {
  background: transparent;
  box-shadow: none;
}

.register-card__image {
  height: 100%;
  width: 100%;
  object-fit: contain;
}

.register-card__fallback {
  color: white;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.register-card__title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 1.35rem;
  font-weight: 700;
  color: rgb(var(--text-primary));
}

.register-card__subtitle {
  margin-top: 0.2rem;
  font-size: 0.88rem;
  color: rgb(var(--primary-text));
}

.register-card__notice {
  margin-bottom: 1rem;
  border: 1px solid rgb(var(--primary-border) / 0.56);
  border-radius: 1rem;
  background: rgb(var(--primary-soft) / 0.72);
  padding: 0.85rem 0.95rem;
  font-size: 0.88rem;
  line-height: 1.7;
  color: rgb(var(--primary-text));
}

.register-card__label {
  margin-bottom: 0.55rem;
  display: block;
  font-size: 0.88rem;
  font-weight: 500;
  color: rgb(var(--text-tertiary));
}

.register-card__section--form :deep(input) {
  height: 3rem;
  border-color: rgb(var(--border) / 0.7);
  background: rgb(var(--page-bg) / 0.84);
  color: rgb(var(--text-primary));
}

.register-card__section--form :deep(input::placeholder) {
  color: rgb(var(--text-secondary) / 0.9);
}

.register-card__section--actions :deep(.bg-white) {
  background: rgb(var(--surface) / 0.74);
  border-color: rgb(var(--border) / 0.74);
  color: rgb(var(--text-primary));
}

.register-card__section--actions :deep(.bg-white:hover) {
  background: rgb(var(--surface-muted) / 0.94);
}

.register-card__error {
  margin-top: 1rem;
  font-size: 0.9rem;
  line-height: 1.7;
  color: rgb(var(--danger));
}
</style>
