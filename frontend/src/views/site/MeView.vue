<script setup lang="ts">
import { reactive, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
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

async function handleResetPasskey() {
  await authStore.resetPasskey();
  feedback.value = 'passkey 已重置，旧 RSS 与旧种子链接需要重新生成。';
}

function handleChangePassword() {
  feedback.value = '这是前端骨架，修改密码入口已预留，等待后端接口接入。';
  passwordForm.currentPassword = '';
  passwordForm.nextPassword = '';
}
</script>

<template>
  <AppPageHeader title="我的账户" description="展示角色、登录状态、passkey 与账户相关操作。" />

  <div v-if="feedback" class="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
    {{ feedback }}
  </div>

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
      <AppCard title="passkey 与 RSS">
        <p class="break-all rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          {{ authStore.currentUser?.passkey }}
        </p>
        <template #footer>
          <UiButton variant="danger" @click="handleResetPasskey">重置 passkey</UiButton>
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
          <UiButton variant="primary" @click="handleChangePassword">保存修改</UiButton>
        </template>
      </AppCard>
    </div>
  </div>
</template>

