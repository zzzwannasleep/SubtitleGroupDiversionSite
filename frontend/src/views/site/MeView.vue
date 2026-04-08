<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import { getRssOverview } from '@/services/rss';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
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
const resettingPasskey = ref(false);
const savingPassword = ref(false);

async function loadRssFeed() {
  if (!authStore.currentUser) return;

  errorMessage.value = '';
  rssLoading.value = true;

  try {
    const overview = await getRssOverview(authStore.currentUser);
    rssFeed.value = overview.generalFeed;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载 RSS 信息失败';
  } finally {
    rssLoading.value = false;
  }
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

async function handleResetPasskey() {
  errorMessage.value = '';
  feedback.value = '';
  resettingPasskey.value = true;

  try {
    await authStore.resetPasskey();
    feedback.value = 'passkey 已重置，旧 RSS 地址和旧种子都会失效。';
    await loadRssFeed();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '重置 passkey 失败';
  } finally {
    resettingPasskey.value = false;
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

onMounted(loadRssFeed);
</script>

<template>
  <AppPageHeader title="我的账户" description="展示角色、登录状态、passkey、RSS 与账户相关操作。" />

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
      <AppCard title="passkey 与 RSS" description="RSS 地址会随 passkey 一起轮换。">
        <div class="space-y-4">
          <div>
            <p class="mb-2 text-sm text-slate-500">当前 passkey</p>
            <p class="break-all rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {{ authStore.currentUser?.passkey }}
            </p>
          </div>
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
            <UiButton variant="danger" :disabled="resettingPasskey" @click="handleResetPasskey">
              {{ resettingPasskey ? '重置中...' : '重置 passkey' }}
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
</template>
