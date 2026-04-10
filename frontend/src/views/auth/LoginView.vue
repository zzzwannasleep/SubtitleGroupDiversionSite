<script setup lang="ts">
import { computed, reactive } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import { useRoute, useRouter } from 'vue-router';
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
const mobileBrandIcon = computed(() => settings.value.siteIconResolvedUrl);
const mobileBrandMonogram = computed(() => buildSiteMonogram(settings.value.siteName));

const form = reactive({
  username: '',
  password: '',
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
  <div class="space-y-6">
    <div class="login-brand-compact lg:hidden">
      <div :class="['login-brand-compact__icon', mobileBrandIcon ? 'login-brand-compact__icon--plain' : '']">
        <img
          v-if="mobileBrandIcon"
          :src="mobileBrandIcon"
          :alt="`${settings.siteName} 图标`"
          class="login-brand-compact__image"
        />
        <span v-else class="login-brand-compact__fallback">{{ mobileBrandMonogram }}</span>
      </div>
      <div class="min-w-0 space-y-1">
        <p class="text-xs uppercase tracking-[0.24em] text-slate-300/80">站点登录</p>
        <h1 class="text-2xl font-semibold text-white">{{ settings.siteName }}</h1>
        <p class="text-sm leading-6 text-slate-300/88">{{ settings.siteDescription }}</p>
      </div>
    </div>

    <div class="login-card-shell">
      <AppCard title="登录系统" :description="`使用管理员预先创建的账号进入 ${settings.siteName}。`">
        <div class="space-y-5">
          <AppAlert
            v-if="settings.loginNotice"
            variant="info"
            title="登录提示"
            :description="settings.loginNotice"
          />

          <form class="space-y-4" @submit.prevent="handleSubmit">
            <div>
              <label class="app-field-label">用户名</label>
              <UiInput v-model="form.username" placeholder="请输入用户名" />
            </div>
            <div>
              <label class="app-field-label">密码</label>
              <UiInput v-model="form.password" type="password" placeholder="请输入密码" />
              <p class="app-field-help">登录成功后会自动跳回你刚才尝试访问的页面。</p>
            </div>
            <AppAlert v-if="authStore.errorMessage" variant="error" :title="authStore.errorMessage" />
            <UiButton type="submit" block variant="primary" :disabled="authStore.isLoading">
              {{ authStore.isLoading ? '登录中...' : '登录' }}
            </UiButton>
          </form>
        </div>

        <template v-if="isMockMode" #footer>
          <div class="space-y-3">
            <p class="text-sm text-slate-500">本地预览可直接填入演示账号</p>
            <div class="flex flex-wrap gap-2">
              <UiButton variant="ghost" size="sm" @click="fillDemoUser('admin')">admin</UiButton>
              <UiButton variant="ghost" size="sm" @click="fillDemoUser('uploader')">uploader</UiButton>
              <UiButton variant="ghost" size="sm" @click="fillDemoUser('user')">user</UiButton>
            </div>
          </div>
        </template>
      </AppCard>
    </div>
  </div>
</template>

<style scoped>
.login-brand-compact {
  display: flex;
  align-items: center;
  gap: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 24px;
  background: linear-gradient(145deg, rgba(15, 23, 42, 0.74), rgba(15, 23, 42, 0.5));
  box-shadow: 0 20px 60px rgba(2, 6, 23, 0.24);
  backdrop-filter: blur(18px);
  padding: 1.1rem 1rem;
}

.login-brand-compact__icon {
  display: flex;
  height: 4rem;
  width: 4rem;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  border-radius: 1.25rem;
  background:
    linear-gradient(145deg, rgba(96, 165, 250, 0.34), rgba(15, 23, 42, 0.92)),
    rgba(15, 23, 42, 0.92);
  box-shadow:
    0 16px 30px rgba(37, 99, 235, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  animation: compact-brand-float 4s ease-in-out infinite;
}

.login-brand-compact__icon--plain {
  background: transparent;
  box-shadow: none;
}

.login-brand-compact__image {
  height: 100%;
  width: 100%;
  object-fit: contain;
}

.login-brand-compact__fallback {
  color: white;
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.login-card-shell :deep(.app-surface) {
  overflow: hidden;
  border-color: rgba(148, 163, 184, 0.18);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 0.84));
  box-shadow: 0 28px 72px rgba(2, 6, 23, 0.26);
  backdrop-filter: blur(22px);
}

.login-card-shell :deep(.app-card-header) {
  border-bottom-color: rgba(148, 163, 184, 0.16);
}

.login-card-shell :deep(.app-card-header h2) {
  color: white;
}

.login-card-shell :deep(.app-card-header p),
.login-card-shell :deep(.app-field-label) {
  color: rgb(226 232 240 / 0.9);
}

.login-card-shell :deep(.app-field-help) {
  color: rgb(148 163 184 / 0.95);
}

.login-card-shell :deep(input) {
  border-color: rgba(148, 163, 184, 0.18);
  background: rgba(30, 41, 59, 0.78);
  color: white;
}

.login-card-shell :deep(input::placeholder) {
  color: rgb(148 163 184 / 0.9);
}

.login-card-shell :deep(.app-card-footer) {
  border-top-color: rgba(148, 163, 184, 0.16);
}

@keyframes compact-brand-float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-5px) rotate(-2deg);
  }
}
</style>
