<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppConfirmDialog from '@/components/app/AppConfirmDialog.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import { getMyApiToken, resetMyApiToken } from '@/services/auth';
import { getRssOverview } from '@/services/rss';
import { useAuthStore } from '@/stores/auth';
import { formatDateTime } from '@/utils/format';

const authStore = useAuthStore();
const passwordForm = reactive({
  currentPassword: '',
  nextPassword: '',
});
const feedback = ref('');
const errorMessage = ref('');
const rssFeed = ref('');
const rssLoading = ref(false);
const apiToken = ref('');
const apiTokenLoading = ref(false);
const apiTokenDialogOpen = ref(false);
const resettingApiToken = ref(false);
const savingPassword = ref(false);

async function loadRssFeed() {
  errorMessage.value = '';
  rssLoading.value = true;

  try {
    const overview = await getRssOverview();
    rssFeed.value = overview.generalFeed;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载 RSS 信息失败';
  } finally {
    rssLoading.value = false;
  }
}

async function loadApiToken() {
  if (!authStore.currentUser) return;

  errorMessage.value = '';
  apiTokenLoading.value = true;

  try {
    apiToken.value = (await getMyApiToken()).apiToken;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载 API Token 失败';
  } finally {
    apiTokenLoading.value = false;
  }
}

async function loadAccountData() {
  await Promise.all([loadRssFeed(), loadApiToken()]);
}

async function copyRssFeed() {
  if (!rssFeed.value) return;

  errorMessage.value = '';

  try {
    await navigator.clipboard.writeText(rssFeed.value);
    feedback.value = 'RSS 地址已复制。';
  } catch {
    errorMessage.value = '复制 RSS 地址失败，请手动复制。';
  }
}

async function copyApiToken() {
  if (!apiToken.value) return;

  errorMessage.value = '';

  try {
    await navigator.clipboard.writeText(apiToken.value);
    feedback.value = 'API Token 已复制。';
  } catch {
    errorMessage.value = '复制 API Token 失败，请手动复制。';
  }
}

async function handleResetApiToken() {
  errorMessage.value = '';
  feedback.value = '';
  resettingApiToken.value = true;

  try {
    apiToken.value = (await resetMyApiToken()).apiToken;
    feedback.value = 'API Token 已重置，旧 token 已立即失效。';
    apiTokenDialogOpen.value = false;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '重置 API Token 失败';
  } finally {
    resettingApiToken.value = false;
  }
}

async function handleChangePassword() {
  if (!passwordForm.currentPassword || !passwordForm.nextPassword) {
    errorMessage.value = '请填写当前密码和新密码。';
    feedback.value = '';
    return;
  }

  errorMessage.value = '';
  feedback.value = '';
  savingPassword.value = true;

  try {
    await authStore.changePassword(passwordForm.currentPassword, passwordForm.nextPassword);
    feedback.value = '密码已修改成功。';
    passwordForm.currentPassword = '';
    passwordForm.nextPassword = '';
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '修改密码失败';
  } finally {
    savingPassword.value = false;
  }
}

onMounted(loadAccountData);
</script>

<template>
  <AppPageHeader title="我的账户" description="展示角色、登录状态、API Token、RSS 与账户相关操作。" />

  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

  <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
    <AppCard title="基础信息">
      <dl class="grid gap-4 sm:grid-cols-2">
        <div>
          <dt class="text-sm text-slate-500">用户名</dt>
          <dd class="mt-1 font-medium text-slate-900">{{ authStore.currentUser?.username }}</dd>
        </div>
        <div>
          <dt class="text-sm text-slate-500">显示名</dt>
          <dd class="mt-1 font-medium text-slate-900">{{ authStore.currentUser?.displayName }}</dd>
        </div>
        <div>
          <dt class="text-sm text-slate-500">角色</dt>
          <dd class="mt-1"><AppStatusBadge type="role" :value="authStore.currentUser?.role || 'user'" /></dd>
        </div>
        <div>
          <dt class="text-sm text-slate-500">状态</dt>
          <dd class="mt-1">
            <AppStatusBadge type="user-status" :value="authStore.currentUser?.status || 'active'" />
          </dd>
        </div>
        <div>
          <dt class="text-sm text-slate-500">最近登录</dt>
          <dd class="mt-1 font-medium text-slate-900">
            {{ authStore.currentUser ? formatDateTime(authStore.currentUser.lastLoginAt) : '-' }}
          </dd>
        </div>
        <div>
          <dt class="text-sm text-slate-500">加入时间</dt>
          <dd class="mt-1 font-medium text-slate-900">
            {{ authStore.currentUser ? formatDateTime(authStore.currentUser.joinedAt) : '-' }}
          </dd>
        </div>
      </dl>
    </AppCard>

    <div class="space-y-6">
      <AppCard title="RSS 订阅" description="当前站点提供统一的公开 RSS 地址，可直接用于自动化订阅。">
        <div class="space-y-4">
          <div>
            <p class="mb-2 text-sm text-slate-500">通用 RSS 地址</p>
            <p class="break-all rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {{ rssLoading ? '正在加载 RSS 地址...' : rssFeed || '暂时无法获取 RSS 地址' }}
            </p>
          </div>
        </div>
        <template #footer>
          <div class="flex flex-wrap gap-2">
            <UiButton variant="secondary" :disabled="!rssFeed || rssLoading" @click="copyRssFeed">复制 RSS</UiButton>
            <UiButton to="/rss" variant="ghost">前往 RSS 页</UiButton>
          </div>
        </template>
      </AppCard>

      <AppCard title="API Token" description="用于内部脚本或工具直接调用站点 API。">
        <div class="space-y-4">
          <div>
            <p class="mb-2 text-sm text-slate-500">当前 API Token</p>
            <p class="break-all rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {{ apiTokenLoading ? '正在加载 API Token...' : apiToken || '暂时无法获取 API Token' }}
            </p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-600">
            <p class="font-medium text-slate-700">支持的认证请求头</p>
            <ul class="mt-3 space-y-2 font-mono leading-6 text-slate-700">
              <li>Authorization: Token &lt;api_token&gt;</li>
              <li>Authorization: Bearer &lt;api_token&gt;</li>
              <li>X-API-Key: &lt;api_token&gt;</li>
            </ul>
          </div>
        </div>
        <template #footer>
          <div class="flex flex-wrap gap-2">
            <UiButton variant="secondary" :disabled="!apiToken || apiTokenLoading" @click="copyApiToken">
              复制 Token
            </UiButton>
            <UiButton variant="danger" :disabled="resettingApiToken" @click="apiTokenDialogOpen = true">
              {{ resettingApiToken ? '重置中...' : '重置 Token' }}
            </UiButton>
          </div>
        </template>
      </AppCard>

      <AppCard title="修改密码">
        <div class="space-y-4">
          <div>
            <label class="app-field-label">当前密码</label>
            <UiInput v-model="passwordForm.currentPassword" type="password" />
          </div>
          <div>
            <label class="app-field-label">新密码</label>
            <UiInput v-model="passwordForm.nextPassword" type="password" />
          </div>
        </div>
        <template #footer>
          <UiButton variant="primary" :disabled="savingPassword" @click="handleChangePassword">
            {{ savingPassword ? '保存中...' : '保存修改' }}
          </UiButton>
        </template>
      </AppCard>
    </div>
  </div>

  <AppConfirmDialog
    :open="apiTokenDialogOpen"
    title="确认重置 API Token"
    description="旧 token 会立刻失效，所有正在使用旧 token 的脚本或工具都需要同步更新。"
    confirm-label="确认重置"
    tone="warning"
    :pending="resettingApiToken"
    @close="apiTokenDialogOpen = false"
    @confirm="handleResetApiToken"
  >
    <p>建议在确认调用方都可及时更新配置后，再执行这次凭据轮换。</p>
  </AppConfirmDialog>
</template>
